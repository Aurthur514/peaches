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

    def _clean_token(tok: str) -> str:
        t = re.sub(r"[^A-Za-z0-9_ ]", '', tok).strip().lower()
        t = re.sub(r"\s+", '_', t)
        # drop extremely long tokens
        if len(t) > 40:
            return ''
        return t

    # 1) Look for explicit {{placeholders}}
    placeholders = re.findall(r"\{\{\s*([^}\s]+)\s*\}\}", template_text)
    for p in placeholders:
        c = _clean_token(p)
        if c and c not in fields:
            fields.append(c)

    # 2) Headings / inline labels (lines with colon)
    for line in _tokenize_lines(template_text):
        if ':' in line:
            key = line.split(':', 1)[0]
            k = _clean_token(key)
            if k and k not in fields:
                fields.append(k)

    # 3) Common labels fallback, canonicalized
    for lab in COMMON_LABELS:
        norm = re.sub(r"[^A-Za-z0-9_]+", '_', lab).strip('_')
        if norm and norm not in fields:
            fields.append(norm)

    # Canonicalize similar labels and dedupe while preserving order
    def _canonicalize(name: str) -> str:
        n = name.lower()
        if 'policy' in n:
            return 'policy_number'
        if 'claim' in n:
            return 'claim_number'
        if 'insured' in n or n == 'name':
            return 'insured_name'
        if 'date' in n or 'loss' in n:
            return 'date'
        if 'phone' in n or 'tel' in n:
            return 'phone'
        if 'email' in n:
            return 'email'
        return n

    seen = set()
    out = []
    for f in fields:
        cf = _canonicalize(f)
        if cf and cf not in seen:
            seen.add(cf)
            out.append(cf)

    return out[:60]


def propose_fields_with_confidence(template_text: str):
    """Return a list of (field_name, confidence) tuples sorted by confidence desc.
    Confidence: placeholders=1.0, heading=0.8, common_label=0.5
    """
    fields = []

    def _clean_token(tok: str) -> str:
        t = re.sub(r"[^A-Za-z0-9_ ]", '', tok).strip().lower()
        t = re.sub(r"\s+", '_', t)
        if len(t) > 40:
            return ''
        return t

    # placeholders (highest confidence)
    placeholders = re.findall(r"\{\{\s*([^}\s]+)\s*\}\}", template_text)
    for p in placeholders:
        c = _clean_token(p)
        if c:
            fields.append((c, 1.0))

    # headings / labels
    for line in _tokenize_lines(template_text):
        if ':' in line:
            key = line.split(':', 1)[0]
            k = _clean_token(key)
            if k:
                fields.append((k, 0.8))

    # common labels fallback
    for lab in COMMON_LABELS:
        norm = re.sub(r"[^A-Za-z0-9_]+", '_', lab).strip('_')
        if norm:
            fields.append((norm, 0.5))

    # canonicalize and dedupe keeping max confidence per canonical name
    def _canonicalize(name: str) -> str:
        n = name.lower()
        if 'policy' in n:
            return 'policy_number'
        if 'claim' in n:
            return 'claim_number'
        if 'insured' in n or n == 'name':
            return 'insured_name'
        if 'date' in n or 'loss' in n:
            return 'date'
        if 'phone' in n or 'tel' in n:
            return 'phone'
        if 'email' in n:
            return 'email'
        return n

    agg = {}
    for name, conf in fields:
        cn = _canonicalize(name)
        if not cn:
            continue
        agg[cn] = max(agg.get(cn, 0.0), conf)

    out = sorted(agg.items(), key=lambda x: x[1], reverse=True)
    return out


def _first_regex_match(pattern, text: str):
    m = pattern.search(text)
    if m:
        if m.groups():
            return m.group(1).strip()
        return m.group(0).strip()
    return None


def map_fields_from_reports(fields: List[str], reports_text: str):
    """Attempt to map each field to a value found in reports_text using heuristics.
    Returns a tuple (mapping_dict, audit_dict). audit_dict maps field -> {'rule':..., 'snippet':...}
    """
    mapping = {}
    audit = {}
    text = reports_text or ''

    lines = _tokenize_lines(text)
    joined = '\n'.join(lines)

    for f in fields:
        key = f.lower()
        value = ''
        reason = 'none'
        snippet = ''

        # direct label search: lines containing the field name
        pattern = re.compile(rf"{re.escape(key)}[:\s-]+(.+)", re.IGNORECASE)
        for line in lines:
            m = pattern.search(line)
            if m:
                value = m.group(1).strip()
                reason = 'label_line'
                snippet = line.strip()
                break

        # common field heuristics
        if not value:
            if 'email' in key:
                v = _first_regex_match(RE_EMAIL, joined)
                if v:
                    value, reason, snippet = v, 'regex_email', v
            elif 'phone' in key or 'tel' in key:
                v = _first_regex_match(RE_PHONE, joined)
                if v:
                    value, reason, snippet = v, 'regex_phone', v
            elif 'date' in key or 'loss' in key or 'taken' in key:
                v = _first_regex_match(RE_DATE, joined)
                if v:
                    value, reason, snippet = v, 'regex_date', v
            elif 'claim' in key:
                v = _first_regex_match(RE_CLAIM, joined) or _first_regex_match(RE_POLICY, joined)
                if v:
                    value, reason, snippet = v, 'regex_claim_policy', v
            elif 'policy' in key:
                v = _first_regex_match(RE_POLICY, joined)
                if v:
                    value, reason, snippet = v, 'regex_policy', v
            elif 'address' in key:
                # improved: look for lines containing street-like keywords and stitch following line(s)
                for i, line in enumerate(lines):
                    if re.search(r"\d+\s+\w+\s+(Street|St|Ave|Avenue|Blvd|Road|Rd|Ln|Court|Ct)\\b", line, re.IGNORECASE):
                        addr = line.strip()
                        # append next line if it looks like city/state/zip
                        if i + 1 < len(lines):
                            next_line = lines[i+1].strip()
                            if re.search(r"\b[A-Za-z]+,?\s*[A-Za-z]{2}\b|\d{5}(-\d{4})?", next_line):
                                addr = addr + ', ' + next_line
                        value, reason, snippet = addr, 'line_address', addr
                        break
            else:
                # fallback: try to extract a short phrase near a known label in text
                for label in COMMON_LABELS:
                    if label in joined.lower():
                        for i, line in enumerate(lines):
                            if label in line.lower():
                                if ':' in line:
                                    parts = line.split(':', 1)
                                    if parts[1].strip():
                                        value, reason, snippet = parts[1].strip(), 'label_colon_fallback', parts[1].strip()
                                        break
                                if i + 1 < len(lines):
                                    value, reason, snippet = lines[i+1].strip(), 'label_next_line_fallback', lines[i+1].strip()
                                    break
                        if value:
                            break

        # assign confidence based on rule
        conf = 0.0
        if reason == 'label_line':
            conf = 0.90
        elif reason.startswith('regex_'):
            conf = 0.95
        elif reason in ('regex_claim_policy', 'regex_policy'):
            conf = 0.92
        elif reason == 'line_address':
            conf = 0.90
        elif reason == 'label_colon_fallback':
            conf = 0.70
        elif reason == 'label_next_line_fallback':
            conf = 0.60
        elif reason == 'not_found':
            conf = 0.0
        else:
            conf = 0.50

        if value:
            if len(value) > 300:
                value = value[:300] + '...'
            mapping[f] = value
            audit[f] = {'rule': reason, 'snippet': snippet, 'confidence': round(conf, 2)}
        else:
            mapping[f] = ''
            audit[f] = {'rule': 'not_found', 'snippet': '', 'confidence': 0.0}

    return mapping, audit

    return mapping, audit


if __name__ == '__main__':
    # small self-test
    tmpl = "Policy: {{policy_number}}\nInsured: {{insured_name}}\nDate of loss: {{date}}"
    reports = "Claim #: 12345\nInsured: John Doe\nDate: 11/13/2024\nContact: john@example.com, 555-123-4567"
    print(propose_fields_from_template(tmpl))
    print(map_fields_from_reports(['policy_number','insured_name','date'], reports))
