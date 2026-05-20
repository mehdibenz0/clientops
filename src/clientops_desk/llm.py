from __future__ import annotations
import json
from typing import Any
from clientops_desk.config import settings
from clientops_desk.data_access import get_client_profile
from clientops_desk.decision_engine import THEME_LABELS, classify, request_fingerprint
from clientops_desk.schemas import ClientRequest, InternalTaskDraft, ResolutionPacket, RetrievedCase, WorkflowTraceStep
from clientops_desk.tasking import build_internal_task


def _next_best_actions(theme: str, lane: str) -> list[str]:
    libraries = {
        'roster_credit_sync': [
            'Compare the latest employee roster against the active credit-assignment list.',
            'Confirm whether the newly added employees were included before the most recent sync window.',
            'Trigger or request a refresh, then re-check the three missing profiles.',
        ],
        'merchant_eligibility': [
            'Check the merchant name and category against the accepted partner scope.',
            'Confirm whether the request concerns a partner location or a general retail merchant.',
            'Send the policy-based explanation before escalating a technical incident.',
        ],
        'order_cutoff_policy': [
            'Compare the requested change against the 48-hour modification cutoff.',
            'If the cutoff has not passed, update the order window or confirm the manual override path.',
            'If the cutoff has passed, provide the earliest feasible alternative.',
        ],
        'invoice_variance_intake': [
            'Ask for the invoice number and billing month.',
            'Ask whether the discrepancy is linked to headcount, credited meals, or a one-off adjustment.',
            'Avoid sending a finance escalation until those anchors are available.',
        ],
        'dietary_preference_cutoff': [
            'Check whether preference changes were submitted before the weekly lock date.',
            'Confirm which employees were affected and whether the preview or final order is impacted.',
            'If timing explains the issue, provide the next cycle date in the response.',
        ],
        'new_or_uncertain': [
            'Preserve the request as a structured internal task.',
            'Attach the client message and the relevant account context.',
            'Avoid committing to a root cause until the owning team validates it.',
        ],
    }
    return libraries.get(theme, libraries['new_or_uncertain'])


def _clarifying_questions(theme: str, lane: str) -> list[str]:
    if lane != 'NEED_CLIENT_CLARIFICATION':
        return []
    if theme == 'invoice_variance_intake':
        return [
            'Could you share the invoice number and the billing month concerned?',
            'Does the difference relate to employee count, meal credits, or a separate line item?',
            'Do you have an expected amount or an example of the discrepancy?',
        ]
    return [
        'Which employee, order, or account reference is affected?',
        'What exact action was attempted immediately before the issue?',
        'Could you share the exact error text or a screenshot?',
    ]


def _draft_reply(lane: str, theme: str) -> str:
    if lane == 'RESOLVE_NOW' and theme == 'roster_credit_sync':
        return 'Thanks for flagging this. We can see that this resembles a roster refresh timing issue. We are checking the latest employee list against the credit assignment and will confirm the missing profiles once the refresh has been validated.'
    if lane == 'RESOLVE_NOW' and theme == 'merchant_eligibility':
        return 'Thanks for the detail. This looks consistent with a merchant eligibility question rather than a platform outage. We are checking the location against the accepted partner scope and will confirm the correct usage rule.'
    if lane == 'RESOLVE_NOW' and theme == 'order_cutoff_policy':
        return 'Thanks for reaching out. We are checking your requested change against the order modification cutoff and will confirm whether it can still be updated for the requested delivery cycle.'
    if lane == 'RESOLVE_NOW' and theme == 'dietary_preference_cutoff':
        return 'Thanks for the heads-up. We are reviewing when the dietary preference update was submitted relative to the weekly order lock so we can confirm whether it should apply to the current or next cycle.'
    if lane == 'NEED_CLIENT_CLARIFICATION':
        return 'Thanks for flagging this. To investigate it properly, could you please share the missing reference details listed below? Once we have them, we can route the request to the right path immediately.'
    return 'Thanks for reporting this. We have prepared an internal investigation with the relevant context so the right team can validate the issue before we provide a definitive answer.'


def _operator_brief(lane: str, theme: str, reason: str) -> str:
    label = THEME_LABELS.get(theme, 'Operational review')
    if lane == 'RESOLVE_NOW':
        return f'{label}: this request looks routine enough to handle from an existing playbook. {reason}'
    if lane == 'NEED_CLIENT_CLARIFICATION':
        return f'{label}: the request should not be escalated yet because the team lacks the minimum evidence required to investigate efficiently. {reason}'
    return f'{label}: preserve the request as a structured task and route it internally. {reason}'


def _likely_cause(lane: str, theme: str) -> str:
    causes = {
        'roster_credit_sync': 'A timing gap between employee onboarding and the next credit-assignment refresh.',
        'merchant_eligibility': 'The transaction may fall outside the merchant or partner acceptance scope.',
        'order_cutoff_policy': 'The requested modification may collide with the delivery cutoff window.',
        'invoice_variance_intake': 'The discrepancy cannot be interpreted until the invoice reference and variance type are known.',
        'dietary_preference_cutoff': 'Preference changes may have been submitted after the weekly order lock.',
        'new_or_uncertain': 'No existing playbook explains the symptom with enough confidence.',
    }
    return causes.get(theme, causes['new_or_uncertain'])


def _risk(theme: str, lane: str) -> str:
    if lane == 'CREATE_INTERNAL_TASK' and theme == 'new_or_uncertain':
        return 'high'
    if theme in {'invoice_variance_intake', 'merchant_eligibility'}:
        return 'medium'
    return 'low'


def _signals(lane: str, theme: str, similar: list[RetrievedCase]) -> dict[str, str]:
    if lane == 'RESOLVE_NOW':
        return {
            'estimated_handling_time': '3–5 min instead of 12–15 min',
            'handoff_quality': 'No handoff needed unless first-line checks fail',
            'knowledge_reuse': f'{len(similar)} precedent(s) surfaced',
        }
    if lane == 'NEED_CLIENT_CLARIFICATION':
        return {
            'estimated_handling_time': 'Prevents a low-quality escalation',
            'handoff_quality': 'Client intake improved before routing',
            'knowledge_reuse': 'Playbook lookup paused pending missing facts',
        }
    return {
        'estimated_handling_time': 'Cuts ticket preparation to < 2 min',
        'handoff_quality': 'Structured task created with reusable context',
        'knowledge_reuse': 'No strong precedent found',
    }


def _trace(lane: str, similar: list[RetrievedCase], task: InternalTaskDraft | None) -> list[WorkflowTraceStep]:
    return [
        WorkflowTraceStep(label='Request captured', status='done', detail='Message normalized into a structured intake packet.'),
        WorkflowTraceStep(label='Client context loaded', status='done', detail='Account profile and recent account notes attached.'),
        WorkflowTraceStep(label='Precedents scanned', status='done', detail=f'{len(similar)} similar historical case(s) ranked.'),
        WorkflowTraceStep(label='Resolution lane selected', status='done', detail=lane.replace('_', ' ').title()),
        WorkflowTraceStep(label='Internal task drafted', status='done' if task else 'skipped', detail='Escalation draft generated.' if task else 'No internal escalation required at this stage.'),
    ]


def mock_assess(issue: ClientRequest, retrieved_cases: list[dict[str, Any]]) -> ResolutionPacket:
    classification = classify(issue, retrieved_cases)
    similar = [RetrievedCase(**case) for case in retrieved_cases]
    client_context = get_client_profile(issue.client_id, issue.client_company)
    task = None
    if classification['lane'] == 'CREATE_INTERNAL_TASK':
        task = build_internal_task(issue, classification['service_theme'], classification['reason'])
    return ResolutionPacket(
        lane=classification['lane'],
        confidence=classification['confidence'],
        service_theme=classification['service_theme'],
        request_fingerprint=request_fingerprint(issue),
        operator_brief=_operator_brief(classification['lane'], classification['service_theme'], classification['reason']),
        likely_cause=_likely_cause(classification['lane'], classification['service_theme']),
        business_risk=_risk(classification['service_theme'], classification['lane']),
        next_best_actions=_next_best_actions(classification['service_theme'], classification['lane']),
        clarifying_questions=_clarifying_questions(classification['service_theme'], classification['lane']),
        draft_client_reply=_draft_reply(classification['lane'], classification['service_theme']),
        similar_cases=similar,
        internal_task=task,
        client_context=client_context,
        value_signals=_signals(classification['lane'], classification['service_theme'], similar),
        workflow_trace=_trace(classification['lane'], similar, task),
    )


def anthropic_assess(issue: ClientRequest, retrieved_cases: list[dict[str, Any]]) -> ResolutionPacket:
    if not settings.anthropic_api_key:
        raise RuntimeError('ANTHROPIC_API_KEY is required when LLM_MODE=anthropic')
    from anthropic import Anthropic
    client = Anthropic(api_key=settings.anthropic_api_key)
    client_context = get_client_profile(issue.client_id, issue.client_company)
    schema = ResolutionPacket.model_json_schema()
    payload = {
        'product_context': 'ClientOps Desk is an internal operations workspace for a B2B corporate lunch and employee-service business.',
        'issue': issue.model_dump(),
        'client_context': client_context.model_dump(),
        'similar_cases': retrieved_cases,
        'rules': [
            'Do not invent business facts that are not present in the context.',
            'Prefer RESOLVE_NOW only when precedent evidence materially supports it.',
            'Use NEED_CLIENT_CLARIFICATION when the request lacks operational anchors.',
            'Use CREATE_INTERNAL_TASK when the symptom appears new, finance-sensitive, or unsupported by playbooks.',
            'When creating an internal task, make it useful to an operations teammate without external research.',
        ],
    }
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=2200,
        temperature=0,
        system='You are the reasoning layer inside an internal B2B operations workspace. Return only JSON matching the required schema.',
        messages=[{'role': 'user', 'content': json.dumps(payload)}],
        output_config={'format': {'type': 'json_schema', 'schema': schema}},
    )
    text = ''.join(block.text for block in response.content if getattr(block, 'type', '') == 'text')
    return ResolutionPacket.model_validate_json(text)


def assess(issue: ClientRequest, retrieved_cases: list[dict[str, Any]]) -> ResolutionPacket:
    if settings.llm_mode.lower() == 'anthropic':
        return anthropic_assess(issue, retrieved_cases)
    return mock_assess(issue, retrieved_cases)
