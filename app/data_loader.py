import json
from datetime import datetime, timedelta, timezone
from functools import lru_cache

from app.config import DATA_DIR


@lru_cache(maxsize=1)
def load_tickets() -> list[dict]:
    with open(DATA_DIR / "tickets.json", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_accounts() -> list[dict]:
    with open(DATA_DIR / "accounts.json", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def account_map() -> dict[str, dict]:
    return {a["account_id"]: a for a in load_accounts()}


def get_account(account_id: str) -> dict | None:
    return account_map().get(account_id)


@lru_cache(maxsize=1)
def dataset_as_of() -> datetime:
    """Anchor for 'recent' windows. The mock dataset's timestamps are fixed at
    generation time and drift out of any real 90-day window almost immediately,
    so we anchor to the latest `created_at` in the dataset rather than wall-clock
    now — otherwise every account would show zero recent tickets."""
    latest = max(
        datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
        for t in load_tickets()
    )
    return latest


def get_account_tickets(account_id: str, days: int = 90) -> list[dict]:
    cutoff = dataset_as_of() - timedelta(days=days)
    out = []
    for t in load_tickets():
        if t["account_id"] != account_id:
            continue
        created = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
        if created > cutoff:
            out.append(t)
    return out
