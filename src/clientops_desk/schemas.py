from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field

ResolutionLane = Literal['RESOLVE_NOW', 'NEED_CLIENT_CLARIFICATION', 'CREATE_INTERNAL_TASK']
Priority = Literal['low', 'medium', 'high']

class ClientRequest(BaseModel):
    request_id: str | None = None
    client_id: str = Field(..., description='Stable client identifier used to retrieve a mock client context card.')
    client_company: str
    requester_name: str | None = None
    requester_role: str
    channel: Literal['email', 'form', 'chat'] = 'email'
    subject: str
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)

class ClientProfile(BaseModel):
    client_id: str
    company: str
    segment: str
    plan: str
    enrolled_employees: int
    monthly_budget_chf: int
    account_health: str
    last_roster_update: str
    renewal_window: str
    open_requests: int
    relationship_owner: str
    account_notes: list[str]

class RetrievedCase(BaseModel):
    case_id: str
    title: str
    category: str
    score: float
    previous_resolution: str
    why_relevant: str

class InternalTaskDraft(BaseModel):
    title: str
    priority: Priority
    suggested_team: str
    task_summary: str
    evidence_to_attach: list[str]
    intake_payload: dict[str, Any]

class WorkflowTraceStep(BaseModel):
    label: str
    status: Literal['done', 'pending', 'skipped']
    detail: str

class ResolutionPacket(BaseModel):
    lane: ResolutionLane
    confidence: float = Field(..., ge=0, le=1)
    service_theme: str
    request_fingerprint: str
    operator_brief: str
    likely_cause: str
    business_risk: Priority
    next_best_actions: list[str]
    clarifying_questions: list[str]
    draft_client_reply: str
    similar_cases: list[RetrievedCase]
    internal_task: InternalTaskDraft | None = None
    client_context: ClientProfile
    value_signals: dict[str, str]
    workflow_trace: list[WorkflowTraceStep]
