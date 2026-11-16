"""Streamlit web UI. Run the API first, then:  streamlit run app.py"""
import os

import httpx
import streamlit as st

API = os.getenv("API_URL", "http://localhost:8000")
ACCOUNTS = ["student1", "lecturer1", "admin1"]
VERSIONS = ["B", "A"]
VERSION_LABELS = {"A": "A: role filter only", "B": "B: role filter + verifier"}

st.set_page_config(page_title="UniAssist (role-aware)", page_icon="🎓")
st.title("🎓 UniAssist")
st.caption("Role-aware multi-agent RAG assistant · CSIT305 research prototype (mock documents only)")


def api_call(path, **kwargs):
    """POST to the API. Shows a readable error and stops the page instead of a traceback."""
    try:
        r = httpx.post(f"{API}{path}", timeout=60, **kwargs)
    except httpx.HTTPError as e:
        st.error(f"Cannot reach the API at {API} ({type(e).__name__}). "
                 "Start it with `uvicorn api:app --port 8000`.")
        st.stop()
    return r


def detail(r):
    try:
        d = r.json().get("detail", r.text)
    except ValueError:
        d = r.text
    if isinstance(d, list):  # pydantic validation errors
        d = "; ".join(e.get("msg", str(e)) for e in d)
    return d


def login(username):
    r = api_call("/login", json={"username": username})
    if r.status_code != 200:
        st.error(f"Login failed: {detail(r)}")
        st.stop()
    data = r.json()
    st.session_state.update(user=username, role=data["role"], token=data["token"])


# Optional URL parameters (?user=student1&version=A&q=...) make demos and screenshots repeatable.
# Unknown values fall back to the defaults instead of crashing the page.
qp = st.query_params
qp_user = qp.get("user", "student1")
qp_version = qp.get("version", "B")

with st.sidebar:
    st.header("Log in (demo)")
    username = st.selectbox("Demo account", ACCOUNTS,
                            index=ACCOUNTS.index(qp_user) if qp_user in ACCOUNTS else 0)
    if st.button("Log in") or st.session_state.get("user") != username:
        login(username)
    st.success(f"Logged in as **{username}** (role: {st.session_state.role})")
    version = st.radio("Pipeline version", VERSIONS,
                       index=VERSIONS.index(qp_version) if qp_version in VERSIONS else 0,
                       format_func=VERSION_LABELS.get)
    show_debug = st.checkbox("Show agent trace", value=True)

q = st.text_input("Ask a university question", value=qp.get("q", ""), max_chars=500,
                  placeholder="How do I apply for special consideration?")
if q.strip():
    def ask():
        return api_call("/ask", json={"question": q, "version": version},
                        headers={"Authorization": f"Bearer {st.session_state.token}"})

    r = ask()
    if r.status_code == 401:  # token expired (8 h) or the API restarted with a new key
        login(username)
        r = ask()
    if r.status_code != 200:
        st.error(f"The API returned {r.status_code}: {detail(r)}")
        st.stop()
    res = r.json()
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
