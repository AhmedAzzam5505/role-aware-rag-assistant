"""Generates Figure 1 (architecture) as SVG, matching the code at v1.6.1.

    python docs/figures/make_fig1.py docs/architecture.svg
"""
import html
import sys

W, H = 1700, 2240
FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"
C = {  # category: (fill, stroke, title colour, subtitle colour)
    "agent": ("#eeedfc", "#5b52c7", "#2f2896", "#4a42b8"),
    "rag": ("#e3f4ec", "#2f7d5b", "#16503a", "#22704f"),
    "check": ("#fdf1dc", "#b7791f", "#6e450b", "#8a5a12"),
    "eval": ("#e7eef9", "#2f5f9e", "#183a66", "#275290"),
    "ui": ("#f8f8f7", "#c9c9c6", "#1c1c1c", "#4a4a48"),
}
out = []


def esc(t):
    return html.escape(t)


def box(x, y, w, h, kind, title, lines=(), title_size=29, sub_size=21):
    fill, stroke, tc, sc = C[kind]
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    n = 1 + len(lines)
    total = title_size + len(lines) * (sub_size + 9)
    ty = y + h / 2 - total / 2 + title_size * 0.85
    cx = x + w / 2
    out.append(f'<text x="{cx}" y="{ty:.0f}" text-anchor="middle" font-family="{FONT}" font-size="{title_size}" '
               f'font-weight="600" fill="{tc}">{esc(title)}</text>')
    for i, line in enumerate(lines):
        out.append(f'<text x="{cx}" y="{ty + (i + 1) * (sub_size + 9) + 4:.0f}" text-anchor="middle" '
                   f'font-family="{FONT}" font-size="{sub_size}" fill="{sc}">{esc(line)}</text>')


def arrow(d, dashed=False, color="#7c7c7a", both=False, width=2.4):
    dash = ' stroke-dasharray="9 7"' if dashed else ""
    start = ' marker-start="url(#ahs)"' if both else ""
    out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{dash} marker-end="url(#ah)"{start}/>')


def label(x, y, text, size=21, anchor="start", color="#3d3d3b", weight="400", italic=False):
    st = ' font-style="italic"' if italic else ""
    for i, t in enumerate(text.split("\n")):
        out.append(f'<text x="{x}" y="{y + i * (size + 6)}" text-anchor="{anchor}" font-family="{FONT}" '
                   f'font-size="{size}" font-weight="{weight}" fill="{color}"{st}>{esc(t)}</text>')


out.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
out.append('<defs>'
           '<marker id="ah" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="9" markerHeight="9" orient="auto">'
           '<path d="M1,1 L11,6 L1,11" fill="none" stroke="#7c7c7a" stroke-width="2"/></marker>'
           '<marker id="ahs" viewBox="0 0 12 12" refX="2" refY="6" markerWidth="9" markerHeight="9" orient="auto">'
           '<path d="M11,1 L1,6 L11,11" fill="none" stroke="#7c7c7a" stroke-width="2"/></marker>'
           '</defs>')
out.append(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')

# ---------------------------------------------------------------- left: interface
box(50, 80, 330, 150, "ui", "User", ["Student, lecturer or admin"])
box(50, 330, 330, 170, "ui", "Streamlit web app", ["choose role + university,", "ask, compare A and B"])
arrow("M215,230 L215,326")
label(232, 285, "question")

box(50, 1210, 330, 170, "ui", "Final answer", ["answer + sources", "or \"I can't help\""])
arrow("M215,1210 L215,506")
label(232, 840, "response\nshown to user")

# ---------------------------------------------------------------- middle top: login and API
box(470, 80, 400, 150, "ui", "Login · auth.py", ["signed token (HMAC, 8 h)", "carries the role"])
arrow("M380,380 C425,380 425,155 466,155")
label(436, 292, "POST /login", size=20, anchor="start")
box(470, 330, 400, 170, "ui", "FastAPI backend", ["role read from the token,", "never from the request"])
arrow("M380,450 L466,450")
label(392, 548, "POST /ask {question, version,", size=19)
label(392, 572, "dataset} + token", size=19)
arrow("M670,230 L670,326", dashed=True)
label(686, 285, "role")
arrow("M670,500 L670,596")
label(686, 556, "question + role + university")

# ---------------------------------------------------------------- orchestrator and agents
out.append('<rect x="440" y="600" width="460" height="980" rx="28" fill="none" stroke="#5b52c7" stroke-width="2.4" stroke-dasharray="12 9"/>')
label(480, 660, "Orchestrator", size=29, weight="600", color="#1c1c1c")
label(480, 696, "runs the agents in order", size=21, color="#4a4a48")

box(480, 760, 380, 150, "agent", "Retriever", ["allowed chunks only:", "role + university filter, top 4"])
arrow("M670,910 L670,996")
label(686, 960, "top-k chunks")
box(480, 1000, 380, 150, "agent", "Answerer", ["writes with citations", "(sees only retrieved chunks)"])
arrow("M610,1150 L610,1226")
label(596, 1196, "draft + chunks", anchor="end")
box(480, 1230, 380, 250, "agent", "Verifier · Version B only",
    ["access register · labels", "right university · relevance", "support", "→ pass / rewrite once / block"],
    sub_size=20)
# rewrite loop
arrow("M730,1230 L730,1154")
label(744, 1196, "rewrite once")
# outputs
arrow("M480,1400 L386,1340")
label(215, 1420, "B: passed, rewritten or blocked", size=20, anchor="middle")
arrow("M480,1060 L300,1060 L300,1206", dashed=True, color="#5b52c7")
label(312, 1110, "Version A:", size=19, color="#4a42b8", weight="600")
label(312, 1134, "no checker", size=19, color="#4a42b8")

# ---------------------------------------------------------------- right: offline ingestion (RAG)
label(1355, 62, "Offline ingestion", size=24, anchor="middle", color="#3d3d3b")
box(1170, 90, 370, 160, "rag", "Documents", ["31 public university policies", "+ 7 mock staff/admin docs"])
arrow("M1355,250 L1355,326")
box(1170, 330, 370, 160, "rag", "Chunk + tag", ["2 paragraphs per chunk;", "role + university tags"])
arrow("M1355,490 L1355,566")
box(1170, 570, 370, 160, "rag", "Embeddings", ["text-embedding-3-small", "(offline: hashing, 1,024-d)"])
arrow("M1355,730 L1355,766")
box(1170, 770, 370, 160, "rag", "ChromaDB", ["role + university filter", "inside the query → rank"])
arrow("M866,835 L1164,835", both=True)
label(1015, 818, "filtered search", size=20, anchor="middle")

box(1170, 990, 370, 340, "rag", "LLM API", ["gpt-4o-mini, temperature 0", "(offline: extractive answerer,", "rule-based checks)"])
arrow("M866,1060 L1164,1060", both=True)
label(1015, 1043, "prompt / completion", size=20, anchor="middle")
arrow("M866,1310 L1164,1310", both=True)
label(1015, 1293, "judge: supported?", size=20, anchor="middle")
label(1015, 1338, "answers the question?", size=20, anchor="middle")

# ---------------------------------------------------------------- independent sources for the verifier
box(1170, 1380, 370, 130, "check", "Access register", ["roles per document, kept", "outside the index"], sub_size=20)
box(1170, 1540, 370, 130, "check", "Original documents", ["sensitivity labels", "(e.g. STAFF ONLY)"], sub_size=20)
arrow("M1164,1440 L866,1440", dashed=True, color="#b7791f")
arrow("M1164,1600 C1000,1600 950,1468 866,1466", dashed=True, color="#b7791f")
label(1035, 1424, "independent of ChromaDB tags", size=18, anchor="middle", color="#8a5a12")

# ---------------------------------------------------------------- logger
box(480, 1660, 380, 150, "ui", "Logger", ["every live query → queries.jsonl:", "latency, tokens, cost, decision"], sub_size=20)
arrow("M670,1580 L670,1656", dashed=True)
label(686, 1628, "every live query", size=20)

# ---------------------------------------------------------------- evaluation harness lane
out.append('<rect x="30" y="1860" width="1640" height="250" rx="24" fill="#f4f7fc" stroke="#2f5f9e" stroke-width="2" stroke-dasharray="10 8"/>')
label(440, 1902, "Evaluation harness (offline batch runs; logging off)", size=24, weight="600", color="#183a66")
bx = [(60, "Question sets", ["6 sets, 270 labelled", "questions"]),
      (380, "run_eval.py", ["A and B × 4 tagging", "conditions"]),
      (700, "Scoring", ["accuracy, leaks,", "refusals, support"]),
      (1020, "stats.py", ["Wilson 95% CI,", "exact McNemar"]),
      (1340, "results/ + CI", ["reproduced on", "every push"])]
for x, t, ls in bx:
    box(x, 1930, 290, 150, "eval", t, ls, title_size=26, sub_size=20)
for x in (350, 670, 990, 1310):
    arrow(f"M{x},2005 L{x + 26},2005")
# harness drives the same orchestrator
arrow("M410,1930 L410,1530 L436,1530", dashed=True, color="#2f5f9e")
label(396, 1700, "same pipeline,", size=20, color="#275290", anchor="end")
label(396, 1726, "called directly", size=20, color="#275290", anchor="end")

# ---------------------------------------------------------------- legend
items = [("agent", "Agents (major technology)"), ("rag", "RAG (supporting technology)"),
         ("check", "Independent checks"), ("eval", "Evaluation"), ("ui", "Interface and logging")]
lx = 60
for kind, text in items:
    fill, stroke, _, _ = C[kind]
    out.append(f'<rect x="{lx}" y="2160" width="30" height="30" rx="7" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    label(lx + 44, 2184, text, size=22, color="#2b2b2a")
    lx += 44 + len(text) * 11.2 + 50

out.append("</svg>")
open(sys.argv[1], "w").write("\n".join(out))
print("written", sys.argv[1])
