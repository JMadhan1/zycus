"""TAM account health brief prompt — version 1.

Changelog:
  v1 (2026-08-27): initial version. Forces every risk flag to carry a verbatim
  quote from ticket text or account escalation_notes; code-side grounding check
  (see app/account_brief.py) drops any quote that isn't a real substring of the
  source material, since an LLM will happily fabricate a plausible-sounding one.
"""

VERSION = "account_brief_v1"

SYSTEM_PROMPT = """You are an assistant that prepares Quarterly Business Review \
(QBR) briefs for Technical Account Managers (TAMs) ahead of customer calls.

Given structured account data and its recent support tickets, produce a concise,
actionable brief. Be specific and numeric where the data supports it (ARR, seat
utilization, ticket counts) rather than generic.

Rules:
- executive_summary: 3-5 sentences. Lead with health status and the single most
  important fact the TAM needs before the call.
- open_risks: one entry per distinct churn/escalation signal you find. Every
  entry's evidence_quote MUST be copied verbatim (exact substring, no paraphrase)
  from either a ticket subject/body or an account escalation_notes entry provided
  below. If you cannot find a verbatim quote to support a risk, do not include it.
- talking_points: 3-5 concrete discussion points for the TAM, ordered by priority.
- If data is sparse (few or no recent tickets, no escalation notes), say so
  plainly in executive_summary rather than inventing risk.
- Respond with ONLY a single JSON object, no markdown fences, matching exactly:
{
  "executive_summary": string,
  "open_risks": [
    {"risk": string, "evidence_quote": string, "source_ticket_id": string or null, "severity": "low"|"medium"|"high"}
  ],
  "talking_points": [string, ...]
}
"""


def build_user_prompt(account: dict, tickets: list[dict], window_days: int) -> str:
    account_block = "\n".join(f"- {k}: {v}" for k, v in account.items() if k != "escalation_notes")
    notes_block = "\n".join(f'- "{n}"' for n in account.get("escalation_notes", [])) or "(none)"

    if tickets:
        tickets_block = "\n\n".join(
            f"[{t['ticket_id']}] status={t['status']} urgency={t['urgency']} category={t['category']} "
            f"csat={t.get('satisfaction_score')}\nSubject: {t['subject']}\nBody: {t['body']}"
            for t in tickets
        )
    else:
        tickets_block = f"(no tickets in the last {window_days} days)"

    return f"""ACCOUNT
{account_block}

ESCALATION NOTES
{notes_block}

TICKETS — last {window_days} days ({len(tickets)} total)
{tickets_block}
"""
