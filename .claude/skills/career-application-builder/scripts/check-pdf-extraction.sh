#!/usr/bin/env bash
#
# Extract the text layer from a CV PDF and report what a parser would see.
#
# This is a smoke test, not a compatibility certification. It cannot tell you
# whether any particular employer's system will parse the file — vendors and
# versions differ. What it can tell you is whether the file has a usable text
# layer, whether expected sections survive extraction, and what order the text
# comes out in. Read the extracted text; that is the actual deliverable here.
#
# Usage: check-pdf-extraction.sh <file.pdf> [output.txt]

set -euo pipefail

# The extracted text is a full CV: name, contact details, employment history.
# Write it owner-only rather than inheriting a permissive default umask.
umask 077

PDF="${1:-}"
OUT="${2:-}"

if [[ -z "$PDF" ]]; then
    echo "usage: $(basename "$0") <file.pdf> [output.txt]" >&2
    exit 64
fi

if [[ ! -f "$PDF" ]]; then
    echo "error: no such file: $PDF" >&2
    exit 66
fi

if ! command -v pdftotext >/dev/null 2>&1; then
    echo "error: pdftotext not found. Install poppler:" >&2
    echo "  macOS:  brew install poppler" >&2
    echo "  Debian: apt install poppler-utils" >&2
    exit 69
fi

OUT="${OUT:-${PDF%.pdf}.extracted.txt}"

pdftotext -layout "$PDF" "$OUT"
# umask only governs newly created files — an existing $OUT keeps its old mode.
chmod 600 "$OUT"

WORDS=$(wc -w < "$OUT" | tr -d ' ')
LINES=$(wc -l < "$OUT" | tr -d ' ')

echo "=== extraction ==="
echo "source:    $PDF"
echo "text out:  $OUT"
echo "extracted: $WORDS words, $LINES lines"
echo

if [[ "$WORDS" -eq 0 ]]; then
    echo "FAIL: no text extracted. The PDF likely contains images of text rather than"
    echo "      text, or the text layer is missing. A parser gets nothing from this file."
    exit 1
fi

if [[ "$WORDS" -lt 150 ]]; then
    echo "WARN: only $WORDS words extracted, which is short for a CV. Some content may"
    echo "      be trapped in tables, text boxes, or graphics that did not extract."
    echo
fi

echo "=== section headings, in extracted order (English + German) ==="
# Umlauts are spelled as explicit alternations because grep -i only case-folds
# non-ASCII reliably under a UTF-8 locale, and this may run under LC_ALL=C.
EN='(work[[:space:]]+)?(experience|employment|education|skills|projects|publications|certifications|summary|profile|languages|references)'
DE='(berufserfahrung|ausbildung|kenntnisse|f[äÄ]higkeiten|sprachen|projekte|zusammenfassung|lebenslauf|praktika|weiterbildung|publikationen|pers[öÖ]nliche[[:space:]]+daten|profil)'
FOUND=$(grep -niE "^[[:space:]]*(${EN}|${DE})[[:space:]]*:?[[:space:]]*\$" "$OUT" || true)

if [[ -z "$FOUND" ]]; then
    echo "none found on their own lines."
    echo
    echo "This is worth a look. Either the CV uses non-standard headings, or headings"
    echo "are merging with adjacent text during extraction. Parsers rely on these to"
    echo "segment the document."
    echo
    echo "Note: only English and German headings are recognised here. A CV in another"
    echo "language will report none found without anything being wrong."
else
    echo "$FOUND" | sed 's/^/  line /'
fi
echo

echo "=== contact details ==="
EMAIL_LINE=$(grep -nEm1 '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' "$OUT" | cut -d: -f1 || true)
if [[ -n "$EMAIL_LINE" ]]; then
    if [[ "$EMAIL_LINE" -le 15 ]]; then
        echo "  email found at line $EMAIL_LINE (near top — good)"
    else
        echo "  WARN: email first appears at line $EMAIL_LINE. Contact details should be"
        echo "        near the top of the extracted text. If they are visually at the top"
        echo "        of the page but extract late, they may be in a header or text box,"
        echo "        which parsers frequently drop."
    fi
else
    echo "  WARN: no email address in the extracted text. If the CV shows one, it is not"
    echo "        surviving extraction — check for headers, text boxes, or icon graphics."
fi
echo

echo "=== first 25 lines as extracted ==="
head -25 "$OUT" | sed 's/^/  | /'
echo
echo "Read $OUT in full. Check that employers, titles, and dates stay adjacent to each"
echo "other rather than pooling into separate blocks — that pattern indicates a table or"
echo "multi-column layout that scrambled during extraction."
