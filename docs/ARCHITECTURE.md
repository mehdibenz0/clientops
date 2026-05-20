# Architecture

```mermaid
flowchart LR
    A[Client message] --> B[ClientOps API]
    B --> C[Client context registry]
    B --> D[Playbook retrieval]
    C --> E[Resolution layer]
    D --> E
    E --> F{Decision lane}
    F -->|Resolve now| G[Operator workspace + draft reply]
    F -->|Need clarification| H[Client questions]
    F -->|Create task| I[Structured internal task]
    I --> J[Task JSON / n8n handoff]
    K[Streamlit UI] --> B
    L[n8n webhook] --> B
```

## Core services

- `FastAPI`: exposes the request analysis API.
- `TF-IDF retrieval`: ranks similar historical playbook cases in offline demo mode.
- `Decision layer`: selects a resolution lane in a deterministic demo-safe way.
- `Claude integration`: optional live reasoning layer with structured JSON output.
- `Streamlit UI`: makes the product story visually obvious.
- `n8n workflow`: demonstrates API orchestration and downstream routing.

## Design choices

- **Offline-first demo:** the project works without paid API access.
- **Model optionality:** setting `LLM_MODE=anthropic` upgrades the reasoning layer while preserving the same data contract.
- **Human-visible outputs:** every lane creates something an operator can inspect, not only an abstract classification.
- **Contextual escalation:** escalations carry request text, account context, and a structured task draft.
