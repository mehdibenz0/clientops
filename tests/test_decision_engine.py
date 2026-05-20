from clientops_desk.decision_engine import classify, is_under_specified
from clientops_desk.schemas import ClientRequest


def make_issue(**kwargs):
    base = dict(
        client_id='test-client',
        client_company='Test Client SA',
        requester_role='Admin',
        subject='Question',
        message='A detailed request that should contain enough operational context for triage.',
        metadata={},
    )
    base.update(kwargs)
    return ClientRequest(**base)


def test_invoice_without_reference_needs_clarification():
    issue = make_issue(subject='Invoice looks wrong', message='Our invoice looks wrong this month. Please help.')
    assert is_under_specified(issue) is True


def test_strong_retrieval_resolves_now():
    issue = make_issue(subject='Employees missing lunch credits', message='Three employees were added after our roster sync and are missing credits.')
    result = classify(issue, [{'case_id': 'CASE-001', 'category': 'roster_credit_sync', 'score': 0.42}])
    assert result['lane'] == 'RESOLVE_NOW'


def test_refund_low_match_creates_task():
    issue = make_issue(subject='Balance did not update', message='A refund was reversed but the credit balance did not update after 48 hours.')
    result = classify(issue, [{'case_id': 'CASE-099', 'category': 'merchant_eligibility', 'score': 0.12}])
    assert result['lane'] == 'CREATE_INTERNAL_TASK'
