"""Streamlit web UI. Run the API first, then:  streamlit run app.py"""
import os

import httpx
import streamlit as st

API = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="UniAssist (role-aware)", page_icon="🎓")
st.title("🎓 UniAssist")
st.caption("Role-aware multi-agent RAG assistant · CSIT305 research prototype (mock documents only)")

with st.sidebar:
    st.header("Log in (demo)")
    username = st.selectbox("Demo account", ["student1", "lecturer1", "admin1"])
    if st.button("Log in") or "role" not in st.session_state:
        r = httpx.post(f"{API}/login", json={"username": username}).json()
        st.session_state.role = r["role"]
    st.success(f"Logged in as **{username}** (role: {st.session_state.role})")
    version = st.radio("Pipeline version", ["B", "A"],
                       format_func=lambda v: {"A": "A: role filter only", "B": "B: role filter + verifier"}[v])
    show_debug = st.checkbox("Show agent trace", value=True)

q = st.text_input("Ask a university question", placeholder="How do I apply for special consideration?")
if q:
    res = httpx.post(f"{API}/ask", json={"question": q, "role": st.session_state.role, "version": version},
                     timeout=60).json()
    st.markdown(f"**Answer:** {res['answer']}")
    for i, s in enumerate(res["sources"], 1):
        st.markdown(f"[{i}] {s['title']}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Verifier", res["verifier_decision"])
    c2.metric("Latency", f"{res['latency_s'] * 1000:.0f} ms")
    c3.metric("Cost", f"${res['cost_usd']:.5f}")
    if show_debug:
        with st.expander("Agent trace"):
            st.json({k: res[k] for k in ("retrieved", "verifier_reasons", "revisions", "tokens_in", "tokens_out", "mode")})
