from fastapi.testclient import TestClient
from clientops_desk.app import app

client = TestClient(app)


def test_health():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_analysis_returns_resolution_packet():
    payload = {
        'client_id': 'leman-consulting',
        'client_company': 'Leman Consulting SA',
        'requester_role': 'HR Operations Manager',
        'channel': 'email',
        'subject': 'New employees missing lunch credits',
        'message': 'We added 12 employees this week but only 9 received their lunch credits. Could you check the three missing profiles?',
        'metadata': {'employee_reference': 'multiple', 'roster_batch': 'MAY-W3'}
    }
    response = client.post('/analyze', json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body['lane'] in {'RESOLVE_NOW', 'NEED_CLIENT_CLARIFICATION', 'CREATE_INTERNAL_TASK'}
    assert body['client_context']['company'] == 'Léman Consulting SA'
