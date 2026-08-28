"""Single entry-point demo: run `python run_demo.py` after setting GROQ_API_KEY
in .env. Demonstrates Task 1 (triage) and Task 2 (account brief) end-to-end
against the mock dataset.
"""
import json

from app.account_brief import account_health_brief
from app.schemas import TicketInput
from app.triage import triage_ticket


def main():
    print("=" * 70)
    print("TASK 1 — Ticket Triage")
    print("=" * 70)
    ticket = TicketInput(
        subject="SAML SSO login failing for all users after IdP metadata update",
        body=(
            "We updated our IdP's SAML metadata yesterday and now no one in our "
            "org can log in via SSO. Getting 'invalid_signature' errors. This is "
            "blocking our entire team."
        ),
        product="SecureVault",
        plan_tier="Enterprise",
    )
    result = triage_ticket(ticket)
    print(json.dumps(result.model_dump(), indent=2))

    print()
    print("=" * 70)
    print("TASK 2 — TAM Account Health Brief")
    print("=" * 70)
    brief = account_health_brief("ACC-1785")
    print(json.dumps(brief.model_dump(), indent=2))

    print()
    print("Run `python -m eval.harness` for the full eval suite.")
    print("Run `uvicorn app.api:app --reload` to start the REST API.")


if __name__ == "__main__":
    main()
