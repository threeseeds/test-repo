#!/usr/bin/env python3
"""Normalize a municipal code source into plain text plus a provenance record.

Inputs: .txt/.md, .html/.htm, .docx, .pdf (needs pdftotext), '-' for stdin, or an http(s) URL.
Output (in --out): source.txt (blank-line separated paragraphs, tables as Markdown rows)
and provenance.json (origin, sha256, retrieval time, size, and code-supplement currency
if the text states one).

URL fetching is best effort: code publishers often render with JavaScript or block
automated clients. On failure this exits with code 2 and tells you to supply a file or
pasted text instead; it never guesses at content.

Usage:
  ingest.py INPUT --out RUN_DIR
"""
import argparse, datetime, hashlib, html.parser, json, os, re, shutil, subprocess, sys, urllib.request, zipfile
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fileio import read_text, write_text, read_json, write_json


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def clean(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace(" ", " ").replace("​", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def docx_text(path):
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    body = root.find(W + "body")
    out = []

    def para(p):
        parts = []
        for node in p.iter():
            if node.tag == W + "t":
                parts.append(node.text or "")
            elif node.tag == W + "tab":
                parts.append(" ")
            elif node.tag in (W + "br", W + "cr"):
                parts.append("\n")
        return "".join(parts).strip()

    for el in body:
        if el.tag == W + "p":
            t = para(el)
            if t:
                out.append(t)
        elif el.tag == W + "tbl":
            rows = []
            for tr in el.iter(W + "tr"):
                rows.append([" ".join(para(p) for p in tc.iter(W + "p")).strip() for tc in tr.findall(W + "tc")])
            if rows:
                lines = ["| " + " | ".join(r) + " |" for r in rows]
                lines.insert(1, "|" + "|".join(" --- " for _ in rows[0]) + "|")
                out.append("\n".join(lines))
    return "\n\n".join(out)


class _Html(html.parser.HTMLParser):
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "table"}

    def __init__(self):
        super().__init__(); self.out = []; self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif tag in self.BLOCK:
            self.out.append("\n\n" if tag != "br" else "\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip = max(0, self.skip - 1)
        elif tag in self.BLOCK:
            self.out.append("\n\n")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def html_text(raw):
    p = _Html(); p.feed(raw)
    return re.sub(r"[ \t]*\n[ \t]*", "\n", "".join(p.out))


def pdf_text(path):
    if not shutil.which("pdftotext"):
        sys.exit("pdftotext is not installed; convert the PDF to text or DOCX and pass that instead")
    return subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True, check=True).stdout


def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "municipal-code-mapper/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            ctype = r.headers.get("Content-Type", "")
    except Exception as e:
        sys.stderr.write(f"Could not fetch {url}: {e}\nProvide the code as a file (.docx/.pdf/.html/.txt) or pasted text instead.\n")
        sys.exit(2)
    text = raw.decode("utf-8", errors="replace")
    if "html" in ctype or text.lstrip().lower().startswith(("<!doctype", "<html")):
        text = html_text(text)
        if len(text) < 800 or re.search(r"enable javascript|requires javascript", text, re.I):
            sys.stderr.write(f"{url} returned a page with almost no text; it is probably rendered with JavaScript.\n"
                             "Download the chapter or title as a file and pass that instead.\n")
            sys.exit(2)
    return text


def currency(text):
    out = {}
    m = re.findall(r"\(Supp\. No\. (\d+)\)", text)
    if m:
        out["supplement"] = sorted(set(m), key=int)[-1]
    m = re.findall(r"Created: (\d{4}-\d\d-\d\d)", text)
    if m:
        out["created"] = max(m)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    src = a.input
    if src == "-":
        text, fmt, raw = sys.stdin.read(), "stdin", None
    elif re.match(r"^https?://", src):
        text, fmt = fetch(src), "url"; raw = text.encode()
    else:
        if not os.path.exists(src):
            sys.exit(f"no such file: {src}")
        ext = os.path.splitext(src)[1].lower()
        with open(src, "rb") as fh:
            raw = fh.read()
        if ext == ".docx":
            text, fmt = docx_text(src), "docx"
        elif ext in (".html", ".htm"):
            text, fmt = html_text(raw.decode("utf-8", errors="replace")), "html"
        elif ext == ".pdf":
            text, fmt = pdf_text(src), "pdf"
        elif ext in (".txt", ".md", ".text", ""):
            text, fmt = raw.decode("utf-8", errors="replace"), "text"
        else:
            sys.exit(f"unsupported file type {ext}; use .docx, .pdf, .html or .txt")
    text = clean(text)
    if len(text) < 200:
        sys.exit("extracted almost no text; the source may be a scan or an empty export")
    os.makedirs(a.out, exist_ok=True)
    write_text(os.path.join(a.out, "source.txt"), text)
    prov = {"origin": src if src != "-" else "stdin", "format": fmt, "sha256": hashlib.sha256(raw if raw is not None else text.encode()).hexdigest(),
            "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "chars": len(text), "lines": text.count("\n"), "currency": currency(text)}
    write_json(os.path.join(a.out, "provenance.json"), prov)
    print(f"wrote {a.out}/source.txt ({prov['chars']} chars, {prov['lines']} lines, format {fmt}); currency {prov['currency'] or 'not stated'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
