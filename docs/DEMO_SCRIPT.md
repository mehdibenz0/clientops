# 90-second demo script

## Opening

> I built ClientOps Desk as a product mockup for a fictionalized family B2B corporate meal-services business. The idea was simple: frontline teams lose time not only on hard cases, but on routine requests where they still need to find context, search precedents, and decide what to do next.

## Demo 1 — routine request handled from precedent

Use **Roster sync · missing lunch credits**.

Show:
- incoming request;
- client 360° card;
- decision lane `Resolve Now`;
- similar past cases surfaced;
- drafted client reply.

Say:

> This is the kind of request that should not become a mini-project. The workspace surfaces the most likely playbook path and gives the operator a response that is grounded in the client context.

## Demo 2 — clarification instead of poor escalation

Use **Invoice discrepancy · insufficient detail**.

Show:
- lane `Need Client Clarification`;
- missing questions;
- prevented escalation.

Say:

> I wanted the system to be useful operationally, not just impressive. Here it refuses to create noise for finance because the request lacks the minimum references.

## Demo 3 — new/sensitive issue becomes a structured handoff

Use **Refund ledger · balance not restored**.

Show:
- lane `Create Internal Task`;
- task card;
- downloadable JSON;
- workflow trace.

Say:

> When the issue is novel or finance-sensitive, the product does not fake certainty. It drafts a clean handoff for the right internal team.

## Close

> The technical stack is FastAPI, a retrieval layer, optional Claude structured outputs, a polished operator UI, and an n8n handoff path. But the project was intentionally designed from the business workflow backwards.
