"""
Heuristic filler for Task 3 — fallback when LLM is unavailable.

- Extracts text from a PDF (uses the same extract_text_from_pdfs from the Streamlit app)
- Finds placeholders in a .docx template
- Attempts to extract key:value pairs from the report text with regex heuristics
- Maps keys to placeholders by simple normalization and token matching
- Fills the template and writes an output .docx

Usage:
  python task_3_heuristic_fill.py --template <template.docx> --pdf <report.pdf> --output <out.docx>
"""
import argparse
import re
import os
from io import BytesIO

from task_3_glr_streamlit import (
    extract_text_from_docx,
    extract_text_from_pdfs,
    find_placeholders,
    fill_docx_template,
)
from docx import Document


def extract_key_value_pairs(text: str) -> dict:
    """Heuristic extraction of key:value from text.

    Looks for lines like:
      Key: value
      Key - value
      Key — value
      Key\tvalue
    """
    pairs = {}
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    # regex for key separators
    sep_re = re.compile(r"^\s*(?P<k>[^:\-—\t]{2,80}?)\s*[:\-—\t]\s*(?P<v>.+)$")
    for i, line in enumerate(lines):
        m = sep_re.match(line)
        if m:
            k = m.group('k').strip()
            v = m.group('v').strip()
            pairs[k] = v
            continue
        # also handle cases like "KEY\nVALUE" (two-line pair)
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            # short key followed by non-short value
            if len(line) < 60 and len(next_line) > 0 and len(next_line) < 500:
                # treat as key/value
                pairs[line] = next_line
    return pairs


def normalize_key(k: str) -> str:
    k = k.lower()
    k = re.sub(r"[^a-z0-9]", "", k)
    return k


def map_placeholders(placeholders, kv_pairs):
    # normalize kv keys
    norm_map = {normalize_key(k): v for k, v in kv_pairs.items()}
    result = {}
    for ph in placeholders:
        ph_norm = normalize_key(ph)
        # direct match
        if ph_norm in norm_map:
            result[ph] = norm_map[ph_norm]
            continue
        # substring match
        found = None
        for k_norm, v in norm_map.items():
            if ph_norm in k_norm or k_norm in ph_norm:
                found = v
                break
        if found:
            result[ph] = found
            continue
        # token overlap
        ph_tokens = set([t for t in re.split(r'[_\-]', ph_norm) if t])
        best = None
        best_score = 0
        for k_norm, v in norm_map.items():
            k_tokens = set(re.findall(r'[a-z0-9]+', k_norm))
            score = len(ph_tokens & k_tokens)
            if score > best_score:
                best_score = score
                best = v
        if best_score > 0:
            result[ph] = best
        else:
            result[ph] = ""
    return result


def run(template_path, pdf_path, out_path):
    with open(template_path, 'rb') as f:
        template_bytes = f.read()
    template_text, _ = extract_text_from_docx(BytesIO(template_bytes))

    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    reports_text = extract_text_from_pdfs([BytesIO(pdf_bytes)])

    placeholders = find_placeholders(template_text)
    print(f"Placeholders: {placeholders}")

    kv = extract_key_value_pairs(reports_text)
    print(f"Extracted {len(kv)} heuristic key/value pairs")
    # show first few
    for i, (k, v) in enumerate(kv.items()):
        if i >= 20:
            break
        print(f"  {k}: {v}")

    mapping = map_placeholders(placeholders, kv)
    print("Mapping to placeholders:")
    print(mapping)

    # Fill and save
    doc = Document(BytesIO(template_bytes))
    filled = fill_docx_template(doc, mapping)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    filled.save(out_path)
    print(f"Saved heuristic-filled document to: {out_path}")


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--template', required=True)
    p.add_argument('--pdf', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    run(args.template, args.pdf, args.output)
