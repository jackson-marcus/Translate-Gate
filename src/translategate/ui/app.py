"""Streamlit demo: QA a string pair, corpus dashboard, glossary assistant."""

from __future__ import annotations

import os

import httpx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

API_URL = os.environ.get("TRANSLATEGATE_API_URL", "http://localhost:8370")

SAMPLE_SOURCE = "Your cart has {count} items ready for checkout"
SAMPLE_TARGET = "rauya korv seh items ydeara rofa zahlung"

st.set_page_config(page_title="translategate", page_icon="🌐", layout="wide")
st.title("🌐 translategate")
st.caption("Localization QA gate: terminology, placeholders, quality estimation, cited glossary")


def _ok() -> bool:
    try:
        return httpx.get(f"{API_URL}/health", timeout=3).status_code == 200
    except httpx.HTTPError:
        return False


if not _ok():
    st.error(f"API not reachable at {API_URL}. Start it with `make api`.")
    st.stop()

tab_check, tab_corpus, tab_glossary = st.tabs(
    ["✅ Check a string", "📊 Corpus dashboard", "📖 Glossary"]
)

with tab_check:
    source = st.text_area("Source (EN)", SAMPLE_SOURCE, height=80)
    target = st.text_area("Target translation", SAMPLE_TARGET, height=80)
    if st.button("Run QA gate", type="primary"):
        body = httpx.post(
            f"{API_URL}/check", json={"source": source, "target": target}, timeout=30
        ).json()
        gate = body["gate"]
        badge = {"pass": "✅ PASS", "review": "🟡 REVIEW", "block": "⛔ BLOCK"}[gate]
        c1, c2 = st.columns(2)
        c1.metric("Gate decision", badge)
        c2.metric("QE quality score", f"{body['quality_score']:.0%}")
        for f in body["findings"]:
            st.markdown(f"**[{f['severity']}] {f['check']}** (§ {f['rule_id']}) — {f['detail']}")

with tab_corpus:
    body = httpx.get(f"{API_URL}/corpus/summary", timeout=30).json()
    m = body["metrics"]
    c1, c2, c3 = st.columns(3)
    c1.metric("QE AUC", f"{m['qe_auc']:.3f}")
    c2.metric("Placeholder recall", f"{m['recall_placeholder']:.0%}")
    c3.metric("Terminology recall", f"{m['recall_terminology']:.0%}")
    recalls = {k.removeprefix("recall_"): v for k, v in m.items() if k.startswith("recall_")}
    fig = go.Figure(go.Bar(x=list(recalls.keys()), y=list(recalls.values())))
    fig.update_layout(
        height=340, yaxis_title="Detection recall vs planted defects", yaxis_tickformat=".0%"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(pd.DataFrame([body["planted_defects"]]), hide_index=True, use_container_width=True)

with tab_glossary:
    question = st.text_input("Ask the glossary", "How do I translate checkout?")
    if st.button("Ask", type="primary"):
        body = httpx.post(f"{API_URL}/glossary/ask", json={"question": question}, timeout=30).json()
        if not body["matched"]:
            st.warning("No glossary rule covers that.")
        for rule in body["rules"]:
            with st.expander(f"§ {rule['rule_id']} (score {rule['score']})", expanded=True):
                st.write(rule["body"])
