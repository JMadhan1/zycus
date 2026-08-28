from app.config import GROQ_MODEL
from app.data_loader import get_account, get_account_tickets
from app.llm import call_json
from app.prompts import account_brief_v1
from app.schemas import AccountBrief, RiskFlag


class AccountNotFoundError(Exception):
    pass


def _source_text(account: dict, tickets: list[dict]) -> str:
    """Everything an evidence_quote is allowed to be copied from."""
    parts = list(account.get("escalation_notes", []))
    for t in tickets:
        parts.append(t.get("subject", ""))
        parts.append(t.get("body", ""))
    return "\n".join(parts)


def _is_grounded(quote: str, source_text: str) -> bool:
    """The LLM will happily fabricate a plausible-sounding quote. Reject any
    evidence_quote that isn't a verbatim substring of the ticket/escalation-note
    text it claims to come from."""
    return quote.strip() and quote.strip() in source_text


def account_health_brief(account_id: str, window_days: int = 90) -> AccountBrief:
    account = get_account(account_id)
    if account is None:
        raise AccountNotFoundError(f"No account found for account_id={account_id}")

    tickets = get_account_tickets(account_id, days=window_days)
    source_text = _source_text(account, tickets)

    system_prompt = account_brief_v1.SYSTEM_PROMPT
    user_prompt = account_brief_v1.build_user_prompt(account, tickets, window_days)

    result = call_json(system_prompt, user_prompt)

    valid_ticket_ids = {t["ticket_id"] for t in tickets}
    risks = []
    for r in result.get("open_risks", []):
        quote = r.get("evidence_quote", "")
        if not _is_grounded(quote, source_text):
            continue
        source_id = r.get("source_ticket_id")
        if source_id not in valid_ticket_ids:
            source_id = None
        risks.append(
            RiskFlag(
                risk=r["risk"],
                evidence_quote=quote,
                source_ticket_id=source_id,
                severity=r["severity"],
            )
        )

    return AccountBrief(
        account_id=account_id,
        company=account["company"],
        executive_summary=result["executive_summary"],
        open_risks=risks,
        talking_points=result.get("talking_points", []),
        tickets_analyzed=len(tickets),
        window_days=window_days,
        model=GROQ_MODEL,
        prompt_version=account_brief_v1.VERSION,
    )
