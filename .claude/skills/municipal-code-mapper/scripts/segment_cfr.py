"""Regulation (CFR-style) segmentation, used by segment.py when the profile's style is "cfr".

Differences from the municipal-code style:
  - The unit is a section "§ 99.31 Title?" and the chapter field holds the section number, so scope
    filters and graph colors group by section. `division` is the subpart letter.
  - A provision is one paragraph at any depth. Its id is the section plus the label path, for
    example 99.31.a.1.i.B, and a definition is 99.3.<term-slug> with its own paragraphs below it.
  - Paragraph labels nest (a) lowercase letter, (1) number, (i) roman, (A) uppercase letter, then
    numbers and romans again. A label is accepted only where the sequence allows it, so a wrapped line
    that starts "(b) of this section" stays part of the sentence.
  - Page furniture is removed, wrapped lines are joined, words split by a hyphen across columns are
    rejoined, and "(Authority: ...)" and "[nn FR ...]" lines become the section's history.
"""
import re

LEVELS = ["alpha_l", "num", "roman_l", "alpha_u", "num", "roman_l", "roman_u"]
ROMAN = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100}
TRAIL_OPEN = re.compile(r"(?<![;:.—])\s(?:paragraphs?|under|and|or|of|by|to|through|with|also|in|at)$|,$|§$")


def _roman(s):
    total, prev = 0, 0
    for ch in reversed(s.lower()):
        v = ROMAN[ch]
        total += -v if v < prev else v
        prev = max(prev, v)
    return total


def _fits(label, level):
    kind = LEVELS[level - 1]
    if kind == "alpha_l":
        return bool(re.fullmatch(r"[a-z]", label))
    if kind == "alpha_u":
        return bool(re.fullmatch(r"[A-Z]", label))
    if kind == "num":
        return bool(re.fullmatch(r"\d{1,3}", label))
    if kind == "roman_l":
        return bool(re.fullmatch(r"[ivxlc]+", label))
    return bool(re.fullmatch(r"[IVXLC]+", label))


def _val(label, level):
    kind = LEVELS[level - 1]
    if kind == "alpha_l":
        return ord(label) - 96
    if kind == "alpha_u":
        return ord(label) - 64
    if kind == "num":
        return int(label)
    return _roman(label)


def place(stack, label):
    """Return the new label stack if `label` can follow `stack`, else None."""
    d = len(stack)
    for k in range(d, 0, -1):                      # next sibling at some depth, deepest first
        if _fits(label, k) and _fits(stack[k - 1], k) and _val(label, k) == _val(stack[k - 1], k) + 1:
            return stack[:k - 1] + [label]
    if d < len(LEVELS) and _fits(label, d + 1) and _val(label, d + 1) == 1:   # first child
        return stack + [label]
    return None


def slug(term):
    return re.sub(r"[^a-z0-9]+", "-", term.lower()).strip("-")


LABEL_CHAIN = re.compile(r"^((?:\([A-Za-z0-9]{1,4}\))+)\s*(.*)$")
NOTE_START = re.compile(r"^NOTE( TO § [\d.]+)?:")


def filter_noise(raw, prof):
    """Return [(line_no, text)] for the lines that are not page furniture, and the noise count."""
    noise = [re.compile(x) for x in prof["noise"]]
    cap = prof.get("isolated_noise_max_chars", 16)
    out, dropped = [], 0
    for i, line in enumerate(raw):
        s = line.strip()
        if not s:
            continue
        prev_blank = i == 0 or not raw[i - 1].strip()
        next_blank = i + 1 >= len(raw) or not raw[i + 1].strip()
        if any(n.match(s) for n in noise) or (prev_blank and next_blank and len(s) <= cap and not s.startswith(("§", "Subpart"))):
            dropped += 1
            continue
        out.append((i + 1, s))
    return out, dropped


def join_hyphens(entries):
    """Rejoin a word split across lines, even across removed page furniture. Returns (entries, joins)."""
    out, joins = [], []
    for no, s in entries:
        if out and re.search(r"[A-Za-z]-$", out[-1][1]) and re.match(r"[a-z]", s):
            prev_no, prev = out[-1]
            word = re.search(r"([A-Za-z]+)-$", prev).group(1) + re.match(r"[a-z]+", s).group(0)
            joins.append(f"line {prev_no}: joined '{word}'")
            out[-1] = (prev_no, prev[:-1] + s)
        else:
            out.append((no, s))
    return out, joins


def segment_cfr(raw_lines, prof):
    """Returns (sections, footnotes, stats, unassigned, warnings, titles, clean_text)."""
    entries, noise = filter_noise(raw_lines, prof)
    entries, joins = join_hyphens(entries)
    head = re.compile(prof["section_heading"])
    subpart = re.compile(prof["subpart"])
    sub_q = re.compile(prof["subpart_question"])
    auth = re.compile(prof["authority"])
    src = re.compile(prof["source_note"])
    stop = re.compile(prof["stop"])
    defsecs = set(prof.get("definition_sections", []))
    stats = {"lines": len(raw_lines), "blank": sum(1 for x in raw_lines if not x.strip()), "noise": noise, "structure": 0, "heading": 0,
             "history": 0, "body": 0, "note": 0, "footnote": 0, "front_matter_text": 0}
    sections, unassigned, warnings = [], [], [f"{j}" for j in joins]
    sec = division = cur = None
    stack, base = [], []
    paras = []
    in_note = False
    last_text = ""
    trailing = 0

    def start_para(path, text, no):
        nonlocal cur
        cur = {"path": list(path), "text": text}
        sec["provisions"].append(cur)

    i = 0
    n = len(entries)
    DEF_START = [
        re.compile(r"^([A-Z][A-Za-z’' \-]{2,60}?)\s+The term\b"),
        re.compile(r"^([A-Z][A-Za-z’' \-]{1,60})\.\s+\(a\)\s"),
        re.compile(r"^([A-Z][A-Za-z’' \-]{1,60}?)(?:,[^.]{0,80}?,)?\s+(?:means|includes|has the same meaning|refers to)\b"),
    ]

    def def_start(idx):
        """Term of a definition that starts at entries[idx], or None. Looks ahead up to 4 short lines."""
        text = entries[idx][1]
        if not re.match(r"[A-Z]", text) or LABEL_CHAIN.match(text):
            return None
        for look in range(0, 5):
            if idx + look >= n:
                break
            cand = " ".join(e[1] for e in entries[idx:idx + look + 1])
            for rx in DEF_START:
                m = rx.match(cand)
                if m:
                    return m.group(1).strip()
            if len(text) > 45 and look == 0:       # a long first line that did not match is not a term line
                break
        return None

    while i < n:
        no, s = entries[i]
        if len(sections) >= prof.get("stop_after_sections", 3) and stop.match(s):
            trailing = n - i
            break
        m = subpart.match(s)
        if m:
            division = m.group(1)
            stats["structure"] += 1
            if sub_q.match(m.group(2).strip()) and not s.rstrip().endswith("?"):
                j = i + 1
                while j < n and j - i < 7 and not entries[j - 1][1].rstrip().endswith("?"):
                    j += 1
                i = j
            else:
                i += 1
            continue
        m = head.match(s)
        if m:
            title, j = m.group(2), i + 1
            while not re.search(r"[?.]$", title) and j < n and j - i < 5 and not head.match(entries[j][1]):
                title += " " + entries[j][1]
                j += 1
            sec = {"section": m.group(1), "heading": title.rstrip("?.").strip(), "chapter": m.group(1), "division": division,
                   "article": None, "provisions": [], "history": [], "notes": [], "line": no}
            sections.append(sec)
            cur, stack, base = None, [], []
            in_note = False
            stats["heading"] += 1
            i = j
            continue
        if sec is None:
            stats["front_matter_text"] += 1
            unassigned.append((no, s, "front_matter"))
            i += 1
            continue
        if auth.match(s) or src.match(s):
            closer = ")" if auth.match(s) else "]"
            text, depth = s, s.count("(") - s.count(")") if closer == ")" else (0 if s.rstrip().endswith("]") else 1)
            j = i + 1
            while depth > 0 and j < n and j - i < 6:
                text += " " + entries[j][1]
                depth += (entries[j][1].count("(") - entries[j][1].count(")")) if closer == ")" else (-1 if entries[j][1].rstrip().endswith("]") else 0)
                j += 1
            sec["history"].append(text)
            stats["history"] += 1
            cur = None if cur is None else cur            # history does not end the open paragraph's text
            i = j
            continue
        if NOTE_START.match(s):
            in_note = True
            sec["notes"].append(s)
            stats["note"] += 1
            i += 1
            continue
        if in_note:
            mm_n = LABEL_CHAIN.match(s)
            work_n = None
            if mm_n and mm_n.group(2) and not mm_n.group(2)[0].islower():
                work_n = list(stack)
                for lab in re.findall(r"\(([A-Za-z0-9]+)\)", mm_n.group(1)):
                    work_n = place(work_n, lab)
                    if work_n is None:
                        break
            if work_n is None and not (sec["section"] in defsecs and def_start(i)):
                sec["notes"][-1] += " " + s          # still inside the note
                stats["note"] += 1
                i += 1
                continue
            in_note = False
        term = def_start(i) if sec["section"] in defsecs else None
        prev_complete = last_text == "" or re.search(r"[.)\]?;”\"]$", last_text) is not None or (not base and last_text.endswith(":"))
        if term and (prev_complete or not sec["provisions"]):
            base, stack = [slug(term)], []
            inline = re.match(r"^([A-Z][A-Za-z’' \-]{1,60})\.\s+\(a\)\s+(.*)$", s)
            if inline:                        # "Education records. (a) The term means ..." the first label is inline
                start_para(base, inline.group(1) + ".", no)
                stack = ["a"]
                start_para(base + stack, inline.group(2), no)
                last_text = inline.group(2)
            else:
                start_para(base, s, no)
                last_text = s
            stats["body"] += 1
            i += 1
            continue
        mm = LABEL_CHAIN.match(s)
        if mm and not (last_text and TRAIL_OPEN.search(last_text)):
            labels = re.findall(r"\(([A-Za-z0-9]+)\)", mm.group(1))
            rest = mm.group(2)
            work = list(stack)
            ok = bool(rest) and not rest[0].islower()
            for lab in labels if ok else []:
                work = place(work, lab)
                if work is None:
                    break
            if ok and work is not None:
                stack = work
                start_para(base + stack, rest, no)
                last_text = rest
                stats["body"] += 1
                i += 1
                continue
            if ok:
                warnings.append(f"line {no}: label {mm.group(1)} does not fit the paragraph sequence in {sec['section']}; kept as running text")
        if cur is None:
            start_para(base + stack, s, no)
        else:
            cur["text"] += " " + s
        last_text = s
        stats["body"] += 1
        i += 1
    if trailing:
        warnings.append(f"{trailing} lines after the appendix marker were not segmented")
    for sc in sections:
        for p in sc["provisions"]:
            p["label"] = ".".join(p.pop("path")) or None
            p["text"] = re.sub(r"\s+", " ", p["text"]).strip()
    titles = {s["section"]: s["heading"] for s in sections}
    clean = "\n".join(e[1] for e in entries) + "\n"
    return sections, [], stats, unassigned, warnings, titles, clean
