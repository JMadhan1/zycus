from typing import Literal, Optional

from pydantic import BaseModel, Field

Urgency = Literal["P1", "P2", "P3", "P4"]
Category = Literal[
    "Bug",
    "Feature Request",
    "How-To",
    "Performance",
    "Billing",
    "Integration",
    "Onboarding",
    "Data Loss",
]


class TicketInput(BaseModel):
    subject: str
    body: str
    account_id: Optional[str] = None
    company: Optional[str] = None
    product: Optional[str] = None
    plan_tier: Optional[str] = None


class KBMatch(BaseModel):
    doc_path: str
    section: str
    relevance_score: float
    excerpt: str


class TriageOutput(BaseModel):
    product_area: str
    issue_category: Category
    urgency: Urgency
    urgency_reasoning: str
    kb_match: Optional[KBMatch] = None
    recommended_responder_team: str
    draft_first_response: str
    confidence: float = Field(ge=0.0, le=1.0)
    model: str
    prompt_version: str


class RiskFlag(BaseModel):
    risk: str
    evidence_quote: str
    source_ticket_id: Optional[str] = None
    severity: Literal["low", "medium", "high"]


class AccountBrief(BaseModel):
    account_id: str
    company: str
    executive_summary: str
    open_risks: list[RiskFlag]
    talking_points: list[str]
    tickets_analyzed: int
    window_days: int
    model: str
    prompt_version: str
