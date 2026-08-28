import hashlib
import json
import re
import time

import groq

from app.config import GROQ_MODEL, LLM_SEED, LLM_TEMPERATURE, ROOT_DIR, get_client

_MAX_RETRIES = 4


def _create_with_retry(client, **kwargs):
    """The free/on-demand Groq tier has a low tokens-per-minute limit and will
    429 under any real burst of calls (e.g. the eval harness running 10 cases
    back to back) — retry with backoff rather than let a transient rate limit
    fail a whole case."""
    for attempt in range(_MAX_RETRIES):
        try:
            return client.chat.completions.create(**kwargs)
        except groq.RateLimitError as e:
            if attempt == _MAX_RETRIES - 1:
                raise
            wait_s = getattr(e, "retry_after", None) or (2 ** attempt)
            time.sleep(min(float(wait_s), 30) + 0.5)


_CACHE_PATH = ROOT_DIR / ".cache" / "llm_cache.json"


def _cache_key(system_prompt: str, user_prompt: str) -> str:
    payload = f"{GROQ_MODEL}|{LLM_TEMPERATURE}|{LLM_SEED}|{system_prompt}|{user_prompt}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_cache() -> dict:
    if not _CACHE_PATH.exists():
        return {}
    try:
        return json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_cache(cache: dict) -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def call_json(system_prompt: str, user_prompt: str) -> dict:
    """Call the LLM and parse a single JSON object from the response.

    temperature=0 + a fixed seed is Groq's documented *best-effort* determinism
    — verified empirically here that it is NOT exact for openai/gpt-oss-20b:
    identical calls return semantically-equivalent but differently-worded JSON
    (see README design note / eval_report determinism check). Task 2 requires
    literal determinism for the same input, so this adds a content-hash cache
    as the "post-process to ensure this" the task brief explicitly allows:
    same (model, temperature, seed, prompts) -> same cached response, always.
    """
    cache = _load_cache()
    key = _cache_key(system_prompt, user_prompt)
    if key in cache:
        return cache[key]

    client = get_client()
    response = _create_with_retry(
        client,
        model=GROQ_MODEL,
        temperature=LLM_TEMPERATURE,
        seed=LLM_SEED,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    raw = response.choices[0].message.content
    parsed = _parse_json(raw)

    cache[key] = parsed
    _save_cache(cache)
    return parsed


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
    if fence_match:
        raw = fence_match.group(1)
    return json.loads(raw)
