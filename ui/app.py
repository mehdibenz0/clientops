from __future__ import annotations

import json
import os
from pathlib import Path

import requests
import streamlit as st

API_URL = os.environ.get("CLIENTOPS_API_URL", "http://localhost:8000/analyze")
BASE = Path(__file__).resolve().parents[1]
SAMPLE_DIR = BASE / "data" / "sample_requests"

st.set_page_config(
    page_title="ClientOps Desk",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    :root {
        --bg: #0b1020;
        --panel: rgba(255, 255, 255, 0.055);
        --panel-strong: rgba(255, 255, 255, 0.09);
        --border: rgba(255, 255, 255, 0.11);
        --text-soft: rgba(255, 255, 255, 0.74);
    }
    .stApp {
        background:
            radial-gradient(circle at 15% 8%, rgba(79, 70, 229, 0.25), transparent 28%),
            radial-gradient(circle at 84% 5%, rgba(14, 165, 233, 0.18), transparent 24%),
            linear-gradient(180deg, #08101f 0%, #0b1020 46%, #111827 100%);
        color: white;
    }
    [data-testid="stSidebar"] {
        background: rgba(5, 10, 22, 0.95);
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    .hero {
        padding: 1.35rem 1.45rem;
        background: linear-gradient(135deg, rgba(99,102,241,0.28), rgba(14,165,233,0.18));
        border: 1px solid var(--border);
        border-radius: 28px;
        margin-bottom: 1rem;
        box-shadow: 0 22px 80px rgba(0,0,0,0.22);
    }
    .hero h1 { font-size: 2.6rem; margin: 0; line-height: 1.05; }
    .hero p { margin: 0.55rem 0 0; color: var(--text-soft); font-size: 1.06rem; max-width: 920px; }
    .pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.35rem 0.65rem;
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.16);
        background: rgba(255,255,255,0.08);
        color: rgba(255,255,255,0.92);
        font-size: 0.78rem;
        font-weight: 650;
        margin-bottom: 0.75rem;
    }
    .glass {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 24px;
        padding: 1rem 1.1rem;
        box-shadow: 0 18px 50px rgba(0,0,0,0.18);
    }
    .metric-grid {
        display:grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.85rem;
        margin: 1rem 0 1.2rem;
    }
    .metric-card {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 0.95rem 1rem;
    }
    .metric-card .label { color: var(--text-soft); font-size: 0.78rem; text-transform: uppercase; letter-spacing: .06em; }
    .metric-card .value { font-size: 1.7rem; font-weight: 750; margin-top: .35rem; }
    .metric-card .note { color: rgba(255,255,255,0.62); font-size: .8rem; margin-top: .25rem; }
    .lane {
        display:inline-flex;
        padding:.42rem .72rem;
        border-radius:999px;
        font-weight:750;
        font-size:.78rem;
        letter-spacing:.04em;
        border:1px solid rgba(255,255,255,.14);
    }
    .lane-resolve { background: rgba(34,197,94,.16); color:#bbf7d0; }
    .lane-clarify { background: rgba(250,204,21,.16); color:#fde68a; }
    .lane-task { background: rgba(244,63,94,.16); color:#fecdd3; }
    .section-title { font-weight: 760; font-size: 1.05rem; margin: 0 0 .75rem; }
    .soft { color: var(--text-soft); }
    .timeline-card {
        border-left: 3px solid rgba(99,102,241,0.8);
        padding: .7rem .85rem;
        margin-bottom: .65rem;
        background: rgba(255,255,255,0.045);
        border-radius: 0 18px 18px 0;
    }
    .trace-row {
        display:flex;
        align-items:flex-start;
        gap:.75rem;
        padding:.7rem .15rem;
        border-bottom:1px dashed rgba(255,255,255,.10);
    }
    .trace-bullet {
        width: 14px; height: 14px; border-radius: 999px;
        margin-top:.25rem;
        background: rgba(34,197,94,.82);
        box-shadow: 0 0 0 5px rgba(34,197,94,.12);
        flex: 0 0 auto;
    }
    .trace-skipped { background: rgba(148,163,184,.8); box-shadow: 0 0 0 5px rgba(148,163,184,.12); }
    .task-card {
        padding: 1rem;
        border-radius: 20px;
        background: rgba(244,63,94,.09);
        border: 1px solid rgba(244,63,94,.22);
    }
    .reply-card {
        padding: 1rem;
        border-radius: 20px;
        background: rgba(14,165,233,.11);
        border: 1px solid rgba(14,165,233,.23);
        line-height: 1.55;
    }
    .side-brand { font-size: 1.3rem; font-weight: 800; margin-bottom:.2rem; }
    .side-subtitle { color: rgba(255,255,255,.68); font-size:.9rem; margin-bottom:1rem; }
    .stButton button { border-radius: 14px !important; font-weight: 750 !important; min-height: 3rem; }
    .stTextArea textarea, .stTextInput input { border-radius: 14px !important; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

SCENARIOS = {
    "Roster sync · missing lunch credits": "roster_missing_credits.json",
    "Merchant scope · card refused at café": "merchant_decline.json",
    "Cutoff request · change next Tuesday order": "order_cutoff_change.json",
    "Invoice discrepancy · insufficient detail": "invoice_needs_clarification.json",
    "Dietary update · meal preview mismatch": "dietary_preference_timing.json",
    "Refund ledger · balance not restored": "refund_balance_novel.json",
}


def load_payload(filename: str) -> dict:
    return json.loads((SAMPLE_DIR / filename).read_text(encoding="utf-8"))


with st.sidebar:
    st.markdown('<div class="side-brand">🧭 ClientOps Desk</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="side-subtitle">Internal operations mockup for a fictionalized family B2B corporate meal-services business.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    selected = st.selectbox("Demo scenario", list(SCENARIOS.keys()))
    st.caption("Choose a realistic request and inspect how the workspace routes it.")
    st.markdown("---")
    st.markdown("**Demo environment**")
    st.success("API workspace ready")
    st.info("Live model: mock mode by default")
    st.markdown("---")
    st.markdown("**What to notice**")
    st.markdown("- Context before decisions\n- Playbook reuse\n- Clean handoffs, not chatbot fluff")

payload = load_payload(SCENARIOS[selected])

st.markdown(
    """
<div class="hero">
    <div class="pill">Product mockup · B2B client operations · portfolio-ready</div>
    <h1>ClientOps Desk</h1>
    <p>A polished internal workspace that turns recurring client requests into fast decisions, context-rich replies, and escalation drafts only when the case truly needs one.</p>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="metric-grid">
    <div class="metric-card"><div class="label">Mock accounts</div><div class="value">42</div><div class="note">Corporate lunch clients</div></div>
    <div class="metric-card"><div class="label">Requests today</div><div class="value">18</div><div class="note">7 still untriaged</div></div>
    <div class="metric-card"><div class="label">Routine case target</div><div class="value">&lt; 5m</div><div class="note">From intake to first response</div></div>
    <div class="metric-card"><div class="label">Escalation quality</div><div class="value">Structured</div><div class="note">Context travels with the task</div></div>
</div>
""",
    unsafe_allow_html=True,
)

input_col, preview_col = st.columns([1.12, 0.88], gap="large")
with input_col:
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Incoming client request</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    payload["client_company"] = c1.text_input("Client company", payload["client_company"])
    payload["requester_role"] = c2.text_input("Requester role", payload["requester_role"])
    payload["subject"] = st.text_input("Subject", payload["subject"])
    payload["message"] = st.text_area("Message", payload["message"], height=190)
    run = st.button("Analyse request", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
with preview_col:
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Preview before analysis</div>', unsafe_allow_html=True)
    st.markdown(f"**Client account:** {payload['client_company']}")
    st.markdown(f"**Request channel:** `{payload['channel']}`")
    metadata_keys = ", ".join(payload.get("metadata", {}).keys()) or "none"
    st.markdown(f"**Operational context present:** `{metadata_keys}`")
    st.markdown(
        '<p class="soft">The workspace combines the raw message with client context and relevant historical precedents before it suggests a next move.</p>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

if run:
    try:
        response = requests.post(API_URL, json=payload, timeout=45)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        st.error(f"Could not reach the API: {exc}")
        st.stop()

    lane = data["lane"]
    lane_class = (
        "lane-resolve"
        if lane == "RESOLVE_NOW"
        else "lane-clarify"
        if lane == "NEED_CLIENT_CLARIFICATION"
        else "lane-task"
    )
    lane_label = lane.replace("_", " ").title()
    st.markdown("---")
    top_a, top_b, top_c, top_d = st.columns([1.15, 0.7, 0.9, 0.95])
    with top_a:
        st.markdown(
            f'<div class="glass"><div class="section-title">Decision lane</div><span class="lane {lane_class}">{lane_label}</span><p class="soft" style="margin-top:.8rem;">{data["service_theme"].replace("_", " ").title()}</p></div>',
            unsafe_allow_html=True,
        )
    with top_b:
        st.metric("Confidence", f"{data['confidence']:.0%}")
        st.progress(float(data["confidence"]))
    with top_c:
        st.metric("Business risk", data["business_risk"].title())
        st.caption(f"Fingerprint {data['request_fingerprint']}")
    with top_d:
        st.metric("Likely speed gain", data["value_signals"]["estimated_handling_time"])
        st.caption(data["value_signals"]["handoff_quality"])

    overview, reply, precedents, task, trace = st.tabs(
        ["Resolution workspace", "Draft reply", "Similar precedents", "Internal task", "Workflow trace"]
    )
    with overview:
        left, right = st.columns([1.08, 0.92], gap="large")
        with left:
            st.markdown('<div class="glass">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Operator brief</div>', unsafe_allow_html=True)
            st.write(data["operator_brief"])
            st.markdown("**Likely cause**")
            st.write(data["likely_cause"])
            st.markdown("**Next best actions**")
            for idx, step in enumerate(data["next_best_actions"], start=1):
                st.markdown(f"{idx}. {step}")
            if data["clarifying_questions"]:
                st.markdown("**What to ask the client**")
                for question in data["clarifying_questions"]:
                    st.markdown(f"- {question}")
            st.markdown("</div>", unsafe_allow_html=True)
        with right:
            context = data["client_context"]
            st.markdown('<div class="glass">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Client 360°</div>', unsafe_allow_html=True)
            st.markdown(f"**{context['company']}**")
            k1, k2 = st.columns(2)
            k1.metric("Employees", context["enrolled_employees"])
            formatted_budget = f"CHF {context['monthly_budget_chf']:,}".replace(",", "'")
            k2.metric("Monthly budget", formatted_budget)
            st.markdown(f"**Plan:** {context['plan']}")
            st.markdown(f"**Health:** {context['account_health']}")
            st.markdown(f"**Last roster update:** {context['last_roster_update']}")
            st.markdown(f"**Renewal window:** {context['renewal_window']}")
            st.markdown(f"**Relationship owner:** {context['relationship_owner']}")
            st.markdown("**Account notes**")
            for note in context["account_notes"]:
                st.markdown(f"- {note}")
            st.markdown("</div>", unsafe_allow_html=True)
    with reply:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Client-facing draft</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="reply-card">{data["draft_client_reply"]}</div>', unsafe_allow_html=True)
        st.download_button(
            "Download reply as .txt",
            data["draft_client_reply"],
            file_name="client_reply.txt",
            use_container_width=False,
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with precedents:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Similar historical cases surfaced</div>', unsafe_allow_html=True)
        for case in data["similar_cases"]:
            st.markdown(
                f'''<div class="timeline-card"><strong>{case['case_id']} · {case['title']}</strong><br>
                <span class="soft">Relevance {case['score']:.0%} · {case['why_relevant']}</span><br>
                <span>{case['previous_resolution']}</span></div>''',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
    with task:
        if data["internal_task"]:
            internal_task = data["internal_task"]
            st.markdown('<div class="task-card">', unsafe_allow_html=True)
            st.markdown(f"### {internal_task['title']}")
            st.markdown(
                f"**Priority:** `{internal_task['priority'].upper()}` &nbsp;&nbsp; **Team:** `{internal_task['suggested_team']}`"
            )
            st.write(internal_task["task_summary"])
            st.markdown("**Evidence to attach**")
            for item in internal_task["evidence_to_attach"]:
                st.markdown(f"- {item}")
            st.download_button(
                "Download internal task JSON",
                json.dumps(internal_task, indent=2),
                file_name="internal_task.json",
            )
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.success(
                "No internal task is needed. The case can be handled from the resolution workspace or by asking for missing client details."
            )
    with trace:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Workflow trace</div>', unsafe_allow_html=True)
        for step in data["workflow_trace"]:
            bullet = "trace-bullet trace-skipped" if step["status"] == "skipped" else "trace-bullet"
            st.markdown(
                f'''<div class="trace-row"><div class="{bullet}"></div><div><strong>{step['label']}</strong><br><span class="soft">{step['detail']}</span></div></div>''',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("Choose a scenario, edit the message if you want, and press “Analyse request”.")
