from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path
from clientops_desk.config import settings
from clientops_desk.schemas import ClientProfile

@lru_cache(maxsize=1)
def load_clients() -> dict[str, ClientProfile]:
    raw = json.loads(Path(settings.clients_path).read_text(encoding='utf-8'))
    return {item['client_id']: ClientProfile(**item) for item in raw}

def get_client_profile(client_id: str, fallback_company: str | None = None) -> ClientProfile:
    clients = load_clients()
    if client_id in clients:
        return clients[client_id]
    return ClientProfile(
        client_id=client_id,
        company=fallback_company or 'Unmapped client',
        segment='Ad hoc / manual review',
        plan='Unknown',
        enrolled_employees=0,
        monthly_budget_chf=0,
        account_health='Needs qualification',
        last_roster_update='Unknown',
        renewal_window='Unknown',
        open_requests=0,
        relationship_owner='Unassigned',
        account_notes=['No client profile was found in the mock account registry.']
    )
