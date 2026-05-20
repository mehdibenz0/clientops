# Security notes

- No secrets are committed. Use `.env` locally.
- The repository ships in `LLM_MODE=mock` so the demo does not depend on external data sharing.
- Live model mode should only be used with synthetic or approved test inputs.
- Generated escalation task JSONs are written to `data/generated_tasks/`, which is git-ignored.
- In a real deployment, the task handoff should use authenticated APIs, audit logs, and data retention rules.
