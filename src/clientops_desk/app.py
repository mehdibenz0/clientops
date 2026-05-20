from __future__ import annotations
from fastapi import FastAPI
from clientops_desk.data_access import get_client_profile
from clientops_desk.llm import assess
from clientops_desk.retrieval import search_similar_cases
from clientops_desk.schemas import ClientProfile, ClientRequest, ResolutionPacket
from clientops_desk.tasking import persist_task

app = FastAPI(
    title='ClientOps Desk API',
    version='1.0.0',
    description='Structured request analysis, knowledge reuse, and internal task drafting for a B2B operations workspace.',
)

@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}

@app.get('/clients/{client_id}', response_model=ClientProfile)
def client(client_id: str) -> ClientProfile:
    return get_client_profile(client_id)

@app.post('/analyze', response_model=ResolutionPacket)
def analyze(issue: ClientRequest) -> ResolutionPacket:
    retrieved = search_similar_cases(issue, top_k=3)
    packet = assess(issue, retrieved)
    if packet.internal_task is not None:
        persist_task(packet.internal_task)
    return packet
