"""
Simple internal heuristic "LLM" for Task 3 — rule-based field proposal and mapping.
This is NOT a neural LLM. It uses regex and heuristics to propose fields and extract values
from provided report text. It's intended as an offline fallback or as an alternative when
external LLMs must not be used.

Functions:
- propose_fields_from_template(template_text) -> List[str]
- map_fields_from_reports(fields, reports_text) -> Dict[str,str]

The heuristics are intentionally conservative but cover common insurance fields.
"""
from typing import List, Dict
import re

COMMON_LABELS = [
    'policy', 'policy_number', 'policy #', 'policy no', 'policy number',
    'claim', 'claim_number', 'claim #', 'claim no', 'claim number',
    'insured', 'insured_name', 'name', 'insurer',
    'date', 'date_of_loss', 'date_taken', 'loss_date',
    'address', 'phone', 'email', 'agent', 'adjuster', 'amount', 'estimate'
]

# regex helpers
RE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
RE_PHONE = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b")
RE_DATE = re.compile(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|[A-Za-z]{3,9} \d{1,2},? \d{4})\b")
RE_CLAIM = re.compile(r"\b(?:claim(?:\s|#|no\.?|number)[:\s]*)([A-Za-z0-9\-_/]+)", re.IGNORECASE)
RE_POLICY = re.compile(r"\b(?:policy(?:\s|#|no\.?|number)[:\s]*)([A-Za-z0-9\-_/]+)", re.IGNORECASE)


def _tokenize_lines(text: str):
    return [l.strip() for l in text.splitlines() if l.strip()]


def propose_fields_from_template(template_text: str) -> List[str]:
    """Propose short field names from a template by scanning for placeholder-like tokens
    and headings. Returns a deduped list of candidate field names.
    """
    fields = []

    # 1) Look for explicit {{placeholders}}
    placeholders = re.findall(r"\{\{\s*([^}\s]+)\s*\}\}", template_text)
    for p in placeholders:
        fields.append(p.strip())

    # 2) Headings / bold-looking inline labels (lines with colon)
    for line in _tokenize_lines(template_text):
        if ':' in line:
            key = line.split(':', 1)[0]
            key = re.sub(r"[^A-Za-z0-9_ ]", '', key).strip().lower()
            if key:
                key = key.replace(' ', '_')
                if key not in fields:
                    fields.append(key)

    # 3) Common labels fallback
    for lab in COMMON_LABELS:
        norm = re.sub(r"[^A-Za-z0-9_]+", '_', lab).strip('_')
        if norm and norm not in fields:
            fields.append(norm)

    # Keep order but limited to a reasonable number
    return fields[:60]


def _first_regex_match(pattern, text: str):
    m = pattern.search(text)
    if m:
        if m.groups():
            return m.group(1).strip()
        return m.group(0).strip()
    return None


def map_fields_from_reports(fields: List[str], reports_text: str) -> Dict[str, str]:
    """Attempt to map each field to a value found in reports_text using heuristics.
    Returns a dict mapping each field to the best guess (or empty string).
    """
    out = {}
    text = reports_text or ''

    lines = _tokenize_lines(text)
    joined = '\n'.join(lines)

    for f in fields:
        key = f.lower()
        value = ''

        # direct label search: lines containing the field name
        pattern = re.compile(rf"{re.escape(key)}[:\s-]+(.+)", re.IGNORECASE)
        for line in lines:
            m = pattern.search(line)
            if m:
                value = m.group(1).strip()
                break

        # common field heuristics
        if not value:
            if 'email' in key:
                value = _first_regex_match(RE_EMAIL, joined) or ''
            elif 'phone' in key or 'tel' in key:
                value = _first_regex_match(RE_PHONE, joined) or ''
            elif 'date' in key or 'loss_date' in key or 'taken' in key:
                value = _first_regex_match(RE_DATE, joined) or ''
            elif 'claim' in key:
                value = _first_regex_match(RE_CLAIM, joined) or _first_regex_match(RE_POLICY, joined) or ''
            elif 'policy' in key:
                value = _first_regex_match(RE_POLICY, joined) or ''
            elif 'address' in key:
                # naive: look for lines containing street-like keywords
                for line in lines:
                    if re.search(r"\d+\s+\w+\s+(Street|St|Ave|Avenue|Blvd|Road|Rd)\\b", line, re.IGNORECASE):
                        value = line.strip()
                        break
            else:
                # fallback: try to extract a short phrase near a known label in text
                for label in COMMON_LABELS:
                    if label in joined.lower():
                        # find the label line and take next token sequence
                        for i, line in enumerate(lines):
                            if label in line.lower():
                                # try the same line after colon
                                if ':' in line:
                                    parts = line.split(':', 1)
                                    if parts[1].strip():
                                        value = parts[1].strip()
                                        break
                                # else try next line
                                if i + 1 < len(lines):
                                    value = lines[i+1].strip()
                                    break
                        if value:
                            break

        # final trim and safety
        if value:
            # keep value short if it's long
            if len(value) > 300:
                value = value[:300] + '...'
            out[f] = value
        else:
            out[f] = ''

    return out


if __name__ == '__main__':
    # small self-test
    tmpl = "Policy: {{policy_number}}\nInsured: {{insured_name}}\nDate of loss: {{date}}"
    reports = "Claim #: 12345\nInsured: John Doe\nDate: 11/13/2024\nContact: john@example.com, 555-123-4567"
    print(propose_fields_from_template(tmpl))
    print(map_fields_from_reports(['policy_number','insured_name','date'], reports))
