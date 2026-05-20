from __future__ import annotations
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from clientops_desk.config import settings
from clientops_desk.schemas import ClientRequest, InternalTaskDraft


def build_internal_task(issue: ClientRequest, service_theme: str, reason: str) -> InternalTaskDraft:
    priority = 'high' if any(word in issue.message.lower() for word in ['blocked', 'refund', 'balance', 'all employees']) else 'medium'
    title = f"Investigate {service_theme}: {issue.subject}"[:120]
    evidence = [
        'Original client message',
        f"Client account: {issue.client_company}",
        f"Inbound channel: {issue.channel}",
        'Any transaction or roster identifiers supplied in metadata',
    ]
    return InternalTaskDraft(
        title=title,
        priority=priority,
        suggested_team='Operations & Product Support',
        task_summary=f"{reason} Preserve the original request, validate the account context, and confirm the correct owner before replying externally.",
        evidence_to_attach=evidence,
        intake_payload={
            'client_id': issue.client_id,
            'client_company': issue.client_company,
            'subject': issue.subject,
            'message': issue.message,
            'metadata': issue.metadata,
        },
    )


def persist_task(task: InternalTaskDraft) -> Path:
    settings.generated_tasks_path.mkdir(parents=True, exist_ok=True)
    safe_title = re.sub(r'[^a-zA-Z0-9]+', '-', task.title.lower()).strip('-')[:60]
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    path = settings.generated_tasks_path / f'{stamp}-{safe_title}.json'
    path.write_text(json.dumps(task.model_dump(), indent=2), encoding='utf-8')
    return path
