"""LLM-as-judge scoring for the qualitative parts of Task 1 / Task 2 output
(draft response tone/actionability, brief usefulness) that rule-based checks
can't capture."""

from app.llm import call_json

JUDGE_VERSION = "judge_v1"

TRIAGE_JUDGE_SYSTEM = """You score a support-ticket triage output for quality.
Score 0.0-1.0 on: does the draft_first_response actually address the customer's
issue, is it professional, does urgency_reasoning logically justify the urgency
tier. Respond with ONLY JSON: {"score": number, "pass": boolean, "notes": string}.
pass = true if score >= 0.6."""

ACCOUNT_JUDGE_SYSTEM = """You score a TAM account-brief output for quality.
Score 0.0-1.0 on: is the executive_summary specific and useful (not generic
boilerplate), are talking_points concrete and actionable, are risks (if any)
plausible given the summary. Respond with ONLY JSON:
{"score": number, "pass": boolean, "notes": string}. pass = true if score >= 0.6."""


def judge_triage(ticket_input: dict, triage_output: dict) -> dict:
    user = f"TICKET:\n{ticket_input}\n\nTRIAGE OUTPUT:\n{triage_output}"
    return call_json(TRIAGE_JUDGE_SYSTEM, user)


def judge_account_brief(account_id: str, brief_output: dict) -> dict:
    user = f"ACCOUNT_ID: {account_id}\n\nBRIEF OUTPUT:\n{brief_output}"
    return call_json(ACCOUNT_JUDGE_SYSTEM, user)
