"""Builds the real-document corpus from public university policy pages.

The documents belong to their universities, so the repository stores only the list of sources
(`data/real/manifest.csv`) and this script. Running it downloads each page or PDF, extracts the text
and writes `data/real/docs/<doc_id>.md` (not committed, see .gitignore). `data/real/hashes.csv`
records a SHA-256 of every extracted text, so anyone re-running the script can see whether a
university has changed a page since our results were produced.

    python -m src.fetch_real              # download + extract; reports pages that changed
    python -m src.fetch_real --offline    # re-extract from the cached downloads in data/real/raw
    python -m src.fetch_real --write-hashes   # record the current hashes (done once, by us)
"""
import argparse
import csv
import hashlib
import io
import re
import sys
import time
import urllib.request
from html.parser import HTMLParser

from . import config

REAL_DIR = config.ROOT / "data" / "real"
RAW_DIR = REAL_DIR / "raw"
DOCS_DIR = REAL_DIR / "docs"
MANIFEST = REAL_DIR / "manifest.csv"
HASHES = REAL_DIR / "hashes.csv"
USER_AGENT = "Mozilla/5.0 (compatible; CSIT305-research-dataset-builder)"

SKIP_TAGS = {"script", "style", "noscript", "nav", "header", "footer", "aside", "form", "svg"}  # not "button": an unclosed <button> on the UNSW page hid the whole page
BLOCK_TAGS = {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "td", "th", "dt", "dd", "blockquote", "pre",
              "div", "section", "article", "br", "tr"}
MIN_PARA_CHARS = 30


def read_manifest():
    with open(MANIFEST, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ------------------------------------------------------------------ extraction
class _TextExtractor(HTMLParser):
    """Collects text blocks, skipping navigation, scripts and other page furniture."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.blocks, self.buf = [], []
        self.in_main = 0
        self.saw_main = False

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self.skip += 1
        if tag in ("main", "article"):
            self.in_main += 1
            self.saw_main = True
        if tag in BLOCK_TAGS:
            self._flush()

    def handle_endtag(self, tag):
        if tag in BLOCK_TAGS:
            self._flush()
        if tag in ("main", "article") and self.in_main:
            self.in_main -= 1
        if tag in SKIP_TAGS and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.buf.append(data)

    def _flush(self):
        text = re.sub(r"\s+", " ", "".join(self.buf)).strip()
        if text:
            self.blocks.append((text, self.in_main > 0))
        self.buf = []


def html_to_paragraphs(html):
    p = _TextExtractor()
    p.feed(html)
    p._flush()
    blocks = [t for t, in_main in p.blocks if in_main] if p.saw_main else [t for t, _ in p.blocks]
    return _clean(blocks)


def pdf_to_paragraphs(data):
    from pypdf import PdfReader
    lines = []
    for page in PdfReader(io.BytesIO(data)).pages:
        lines += (page.extract_text() or "").splitlines()
        lines.append("")  # page break ends a paragraph
    paras, cur = [], []
    for line in lines:
        line = line.strip()
        starts_new = bool(re.match(r"^(\d+(\.\d+)*[.)]?\s|[•\-–▪●]\s|[a-z]\)\s|\([a-z0-9]+\)\s)", line))
        if not line or (starts_new and cur):
            if cur:
                paras.append(" ".join(cur))
            cur = [line] if line else []
            continue
        cur.append(line)
        if line.endswith((".", ":", ";")) and len(" ".join(cur)) > 200:
            paras.append(" ".join(cur))
            cur = []
    if cur:
        paras.append(" ".join(cur))
    return _clean(paras)


# Page furniture that is not policy text. Table-of-contents lines ("2.4. Elite Athletes ....... 5")
# are short and full of keywords, so they outranked the real text in search (found in v1.2 testing).
JUNK = re.compile(r"\.{5,}|…{2,}|(\. ){4,}|Jump to Navigation|Jump to Content|^Policy Directory >"
                  r"|/ Document / Policy Directory$", re.I)


def _clean(blocks):
    out, seen = [], set()
    for b in blocks:
        b = re.sub(r"\s+", " ", b).strip()
        b = re.sub(r"(\w)- (\w)", r"\1\2", b)  # words split across PDF lines
        if len(b) < MIN_PARA_CHARS or re.fullmatch(r"(page )?\d+( of \d+)?", b, re.I) or JUNK.search(b):
            continue
        if b in seen:  # repeated headers, footers and menus
            continue
        seen.add(b)
        out.append(b)
    return out


# ------------------------------------------------------------------ main
def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def build(offline=False, delay=1.0):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    results = {}
    for row in read_manifest():
        raw = RAW_DIR / f"{row['doc_id']}.{row['format']}"
        if not offline:
            raw.write_bytes(fetch(row["url"]))
            time.sleep(delay)  # be polite to the university servers
        data = raw.read_bytes()
        paras = pdf_to_paragraphs(data) if row["format"] == "pdf" else html_to_paragraphs(
            data.decode("utf-8", errors="replace"))
        body = "\n\n".join(paras)
        header = "\n".join([
            "---",
            f"title: {row['title']} ({row['university']})",
            "allowed_roles: student, lecturer, admin",
            "sensitivity: public",
            f"source: {row['url']}",
            f"retrieved: {time.strftime('%Y-%m-%d')}",
            "---",
        ])
        (DOCS_DIR / f"{row['doc_id']}.md").write_text(header + "\n" + body + "\n", encoding="utf-8")
        results[row["doc_id"]] = (hashlib.sha256(body.encode()).hexdigest(), len(paras), len(body.split()))
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="re-extract from data/real/raw only")
    ap.add_argument("--write-hashes", action="store_true")
    args = ap.parse_args()
    results = build(offline=args.offline)
    known = {}
    if HASHES.exists():
        known = {r["doc_id"]: r["sha256"] for r in csv.DictReader(open(HASHES, encoding="utf-8"))}
    changed = 0
    for doc_id, (sha, n_paras, n_words) in results.items():
        status = "new" if doc_id not in known else ("same" if known[doc_id] == sha else "CHANGED")
        changed += status == "CHANGED"
        print(f"{doc_id:40s} {n_paras:4d} paragraphs {n_words:6d} words  {status}")
    if args.write_hashes:
        with open(HASHES, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["doc_id", "sha256", "paragraphs", "words", "recorded"])
            for doc_id, (sha, n_paras, n_words) in results.items():
                w.writerow([doc_id, sha, n_paras, n_words, time.strftime("%Y-%m-%d")])
        print(f"hashes written to {HASHES}")
    elif changed:
        print(f"\n{changed} document(s) differ from the versions our results used (data/real/hashes.csv). "
              "Results on the real corpus may not match the latest results/runN exactly.", file=sys.stderr)


if __name__ == "__main__":
    main()
