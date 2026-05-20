from clientops_desk.schemas import ClientRequest
from clientops_desk.retrieval import search_similar_cases


def test_roster_issue_surfaces_credit_sync_case():
    issue = ClientRequest(
        client_id='leman-consulting',
        client_company='Leman Consulting SA',
        requester_role='HR Manager',
        subject='New employees missing lunch credits',
        message='We added employees to the roster but three people did not receive their monthly lunch credit.',
        metadata={'employee_reference': 'EMP-123'}
    )
    results = search_similar_cases(issue)
    assert results
    assert results[0]['category'] == 'roster_credit_sync'
