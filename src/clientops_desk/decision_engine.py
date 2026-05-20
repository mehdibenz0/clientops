from __future__ import annotations
import hashlib
from typing import Any
from clientops_desk.schemas import ClientRequest, ResolutionLane

VAGUE_MARKERS = [
    'does not work',
    "doesn't work",
    'wrong',
    'issue',
    'problem',
    'please help',
]

THEME_LABELS = {
    'roster_credit_sync': 'Employee credit activation',
    'merchant_eligibility': 'Merchant eligibility check',
    'order_cutoff_policy': 'Service cutoff exception',
    'invoice_variance_intake': 'Invoice variance intake',
    'dietary_preference_cutoff': 'Preference timing mismatch',
    'new_or_uncertain': 'Unclassified operational case',
}


def request_fingerprint(issue: ClientRequest) -> str:
    seed = f"{issue.client_id}|{issue.subject}|{issue.message}".encode('utf-8')
    return hashlib.sha1(seed).hexdigest()[:12].upper()


def is_under_specified(issue: ClientRequest) -> bool:
    text = f"{issue.subject} {issue.message}".lower()
    very_short = len(issue.message.strip()) < 70
    vague = any(marker in text for marker in VAGUE_MARKERS)
    invoice_like = any(token in text for token in ['invoice', 'billing', 'charged'])
    has_invoice_reference = bool(issue.metadata.get('invoice_number'))
    no_context_refs = not any(issue.metadata.get(key) for key in ['employee_reference', 'order_id', 'transaction_id', 'invoice_number'])
    return (very_short and vague) or (invoice_like and not has_invoice_reference and no_context_refs)


def classify(issue: ClientRequest, retrieved_cases: list[dict[str, Any]]) -> dict[str, Any]:
    top_case = retrieved_cases[0] if retrieved_cases else None
    top_score = float(top_case['score']) if top_case else 0.0
    if is_under_specified(issue):
        return {
            'lane': 'NEED_CLIENT_CLARIFICATION',
            'confidence': 0.88,
            'service_theme': 'invoice_variance_intake' if 'invoice' in issue.message.lower() else 'new_or_uncertain',
            'reason': 'The request does not contain enough operational anchors to take a safe next step.',
        }
    refund_or_balance = any(token in issue.message.lower() for token in ['refund', 'reversed', 'balance did not', 'credit balance'])
    if refund_or_balance and top_score < 0.28:
        return {
            'lane': 'CREATE_INTERNAL_TASK',
            'confidence': 0.84,
            'service_theme': 'new_or_uncertain',
            'reason': 'The request points to a financial reconciliation path that is not strongly covered by the current playbook library.',
        }
    if top_case and top_score >= 0.16:
        return {
            'lane': 'RESOLVE_NOW',
            'confidence': min(0.96, round(0.68 + top_score, 2)),
            'service_theme': top_case['category'],
            'reason': f"The message materially matches precedent {top_case['case_id']}.",
        }
    return {
        'lane': 'CREATE_INTERNAL_TASK',
        'confidence': 0.79,
        'service_theme': 'new_or_uncertain',
        'reason': 'No playbook case is close enough to recommend a routine resolution.',
    }
