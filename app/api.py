import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app import kb_retrieval
from app.account_brief import AccountNotFoundError, account_health_brief
from app.data_loader import load_accounts, load_tickets
from app.schemas import AccountBrief, TicketInput, TriageOutput
from app.triage import triage_ticket

app = FastAPI(title="Zycus Support AI", version="1.0")

# Local Vite dev origins are always allowed; add the deployed frontend's
# origin (e.g. https://your-app.vercel.app, no trailing slash) via the
# ALLOWED_ORIGINS env var (comma-separated for more than one) once deployed —
# see the README's Deployment section.
_default_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
_extra_origins = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins + _extra_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/accounts")
def list_accounts():
    return [{"account_id": a["account_id"], "company": a["company"]} for a in load_accounts()]


@app.get("/stats")
def stats():
    kb_docs = len({c.doc_path for c in kb_retrieval.load_chunks()})
    return {"tickets": len(load_tickets()), "accounts": len(load_accounts()), "kb_docs": kb_docs}


@app.post("/triage", response_model=TriageOutput)
def triage(ticket: TicketInput):
    return triage_ticket(ticket)


@app.get("/accounts/{account_id}/brief", response_model=AccountBrief)
def account_brief(account_id: str, window_days: int = 90):
    try:
        return account_health_brief(account_id, window_days=window_days)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
