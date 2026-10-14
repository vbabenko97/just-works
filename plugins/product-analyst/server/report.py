"""Deterministic report assembly: the author's narrative above sections copied from the findings.

The author writes only the title, the answer and an optional explanation. The contract, every
published claim with its verdict, the uncertainty and the stop reason are copied field by field,
escaped so their text cannot open a heading, list, table, code block or HTML, and never rounded,
translated or summarised. A report verifier judges only the authored blocks this module lists.

The narrative is held to a strict subset of Markdown so that nothing in it can reach past its
own end: code fences are only ``` lines at the margin and must close, and headings, HTML,
images and footnotes are refused. One scanner applies these rules and splits the blocks. The
narrative itself is kept byte for byte; a form the gateway would have to rewrite, such as a
carriage return, is refused instead.
"""

import json
import re

RENDERER_VERSION = "2"
UNCERTAINTY_LABELS = (
    ("data_quality", "Data quality"),
    ("metric_definition", "Metric definition"),
    ("magnitude", "Magnitude"),
    ("cause", "Cause"),
)
INLINE = re.compile(r"([\\`*_\[\]<>|~&])")
LINE_START = re.compile(r"^(\d+)([.)])|^([#>+=-])")
CODE_SAFE = re.compile(r"[A-Za-z0-9_.:-]+")
LINE_ENDS = re.compile(r"\r\n?")
# Blockquote and list markers, which can hold a heading or a fence after them.
CONTAINERS = re.compile(r"^(?:\s*(?:>|[-*+](?=\s)|\d+[.)](?=\s)))*\s*")
HEADING = re.compile(r"#{1,6}(\s|$)")
SETEXT = re.compile(r"(=+|-+)\s*")
FENCE_LIKE = re.compile(r"`{3,}|~{3,}")
FENCE_OPEN = re.compile(r"```[A-Za-z0-9_+.-]*")
FENCE_CLOSE = "```"
# A CommonMark closing fence: up to three spaces, three or more backticks, nothing else.
CLOSES_IN_COMMONMARK = re.compile(r" {0,3}`{3,}\s*")
HTML = re.compile(r"<[A-Za-z/?!]")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")


def _lines(text: str) -> list[str]:
    return [line.rstrip() for line in LINE_ENDS.sub("\n", text).split("\n")]


def _scan(text: str) -> tuple[list[str], list[tuple[int, int, str]]]:
    """Errors in authored text, and its lines grouped into blocks as (first, last, kind)."""
    lines = text.split("\n")
    errors, spans, current, fence = [], [], None, None
    for offset, line in enumerate(lines):
        if fence is not None:
            if line == FENCE_CLOSE:
                spans.append((fence, offset, "code"))
                fence = None
            elif CLOSES_IN_COMMONMARK.fullmatch(line):
                errors.append(f"line {offset + 1} could close the code block; write exactly ```")
            continue
        body = CONTAINERS.sub("", line, count=1)
        if FENCE_LIKE.match(body):
            if current:
                spans.append(current)
                current = None
            if FENCE_OPEN.fullmatch(line):
                fence = offset
            else:
                errors.append(
                    f"line {offset + 1} is a code fence; open one with ``` and an optional "
                    "language at the start of a line, and close it with ```"
                )
            continue
        if HEADING.match(body) or (line.strip() and SETEXT.fullmatch(CONTAINERS.sub("", line))):
            errors.append(f"line {offset + 1} is a heading; the gateway writes the headings")
        if HTML.search(line):
            errors.append(f"line {offset + 1} holds HTML; write < followed by a space")
        if "![" in line or "[^" in line:
            errors.append(f"line {offset + 1} holds an image or a footnote")
        stripped = line.strip()
        separator = stripped.startswith("|") and set(stripped) <= set("|:- ") and "-" in stripped
        if not stripped:
            if current:
                spans.append(current)
            current = None
        elif separator and current:
            current = (current[0], offset, current[2])
        elif current is None or LIST_ITEM.match(line) or stripped.startswith("|"):
            if current:
                spans.append(current)
            current = (offset, offset, "text")
        else:
            current = (current[0], offset, current[2])
    if fence is not None:
        errors.append(f"the code block opened on line {fence + 1} is not closed")
    if current:
        spans.append(current)
    return errors, spans


def narrative_errors(narrative: object) -> list[str]:
    """What makes a narrative unusable; the gateway, not the author, writes every heading."""
    if not isinstance(narrative, dict):
        return ["narrative must be an object with title, answer and explanation"]
    errors = []
    unknown = sorted(set(narrative) - {"title", "answer", "explanation"})
    if unknown:
        errors.append("narrative has unknown fields: " + ", ".join(unknown))
    title, answer = narrative.get("title"), narrative.get("answer")
    explanation = narrative.get("explanation", "")
    if not isinstance(title, str) or not title.strip() or re.search(r"[\r\n]", title):
        errors.append("narrative.title must be one nonempty line")
    elif HTML.search(title) or "![" in title or "[^" in title:
        errors.append("narrative.title holds HTML, an image or a footnote")
    if not isinstance(answer, str) or not answer.strip():
        errors.append("narrative.answer must be nonempty text")
    if not isinstance(explanation, str):
        errors.append("narrative.explanation must be text, empty when there is none")
    for field in ("answer", "explanation"):
        text = narrative.get(field)
        if not isinstance(text, str):
            continue
        if "\r" in text:
            errors.append(f"narrative.{field} holds a carriage return; end every line with \\n")
        problems, _ = _scan(text.replace("\r", "\n"))
        errors += [f"narrative.{field}: {problem}" for problem in problems]
    return errors


def normalised(narrative: dict) -> dict:
    """The narrative as stored: byte for byte, trailing spaces of a line break included, with an
    absent explanation recorded as empty. Nothing the author wrote is rewritten."""
    return {
        "title": narrative["title"],
        "answer": narrative["answer"],
        "explanation": narrative.get("explanation", ""),
    }


def _escape(value: object) -> list[str]:
    """Copied text as Markdown lines that show the same characters and open no structure."""
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    lines = []
    for line in _lines(INLINE.sub(r"\\\1", text)):
        line = line.lstrip()
        lines.append(LINE_START.sub(lambda m: f"{m[1]}\\{m[2]}" if m[1] else f"\\{m[3]}", line))
    return lines


def _one_line(value: object) -> str:
    return " ".join(line for line in _escape(value) if line)


def _item(label: object, value: object) -> list[str]:
    first, *rest = _escape(value) if value != "" else ["(empty)"]
    return [f"- {_one_line(label)}: {first}"] + [f"  {line}" if line else "" for line in rest]


def _codes(values: list) -> str:
    if not values:
        return "none"
    return ", ".join(
        f"`{value}`" if CODE_SAFE.fullmatch(str(value)) else _one_line(value) for value in values
    )


def authored(narrative: dict) -> tuple[list[str], list[dict]]:
    """The report's first lines, written by the author, and their blocks with report lines."""
    lines = [f"# {narrative['title']}", ""]
    blocks = [
        {
            "block_id": "title",
            "section": "title",
            "start_line": 1,
            "end_line": 1,
            "text": narrative["title"],
        }
    ]
    for section in ("answer", "explanation"):
        text = narrative[section]
        if not text:
            continue
        first = len(lines) + 1
        section_lines = text.split("\n")
        blocks += [
            {
                "block_id": f"{section}-{number}",
                "section": section,
                "start_line": first + start,
                "end_line": first + end,
                "text": "\n".join(section_lines[start : end + 1]),
            }
            for number, (start, end, _) in enumerate(_scan(text)[1], start=1)
        ]
        lines += section_lines + [""]
    return lines, blocks


def render(narrative: dict, contract: dict, findings: dict) -> tuple[str, list[dict]]:
    """Assemble report.md from a normalised narrative and the published findings.

    Returns the report text and its authored blocks. The same inputs give the same bytes.
    """
    lines, blocks = authored(narrative)
    lines += ["## Contract", ""]
    for key in sorted(contract):
        lines += _item(key, contract[key])
    lines += ["", "## Claims", ""]
    if not findings["claims"]:
        lines += ["No claims.", ""]
    for claim in findings["claims"]:
        verdict = claim["verdict"]
        lines += [f"### Claim {_one_line(claim['id'])}", ""]
        lines += _item("Kind", claim.get("kind", "data"))
        lines += _item("Text", claim["text"])
        lines.append(f"- Evidence: {_codes(claim.get('evidence_ids', []))}")
        lines.append(f"- Context statements: {_codes(claim.get('context_refs', []))}")
        lines.append(f"- Verifier verdict: {verdict['verdict']}")
        lines.append(f"- Verifier evidence: {_codes(verdict.get('evidence_ids', []))}")
        lines += _item("Verifier limitations", verdict.get("limitations", ""))
        for field, label in UNCERTAINTY_LABELS:
            lines += _item(f"Uncertainty, {label.lower()}", claim["uncertainty"][field])
        lines.append("")
    lines += ["## Uncertainty", ""]
    for field, label in UNCERTAINTY_LABELS:
        lines += _item(label, findings["uncertainty"][field])
    lines += ["", "## Stop reason", "", findings["stop_reason"], ""]
    return "\n".join(lines), blocks
