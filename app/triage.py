from app import kb_retrieval
from app.config import GROQ_MODEL
from app.llm import call_json
from app.prompts import triage_v1
from app.schemas import KBMatch, TicketInput, TriageOutput


def triage_ticket(ticket: TicketInput) -> TriageOutput:
    query = f"{ticket.subject}\n{ticket.body}"
    kb_chunks = kb_retrieval.retrieve(query, top_k=3)

    system_prompt = triage_v1.SYSTEM_PROMPT
    user_prompt = triage_v1.build_user_prompt(ticket.model_dump(), kb_chunks)

    result = call_json(system_prompt, user_prompt)

    kb_match = None
    if kb_chunks:
        best = kb_chunks[0]
        kb_match = KBMatch(**best)

    return TriageOutput(
        product_area=result["product_area"],
        issue_category=result["issue_category"],
        urgency=result["urgency"],
        urgency_reasoning=result["urgency_reasoning"],
        kb_match=kb_match,
        recommended_responder_team=result["recommended_responder_team"],
        draft_first_response=result["draft_first_response"],
        confidence=result["confidence"],
        model=GROQ_MODEL,
        prompt_version=triage_v1.VERSION,
    )
