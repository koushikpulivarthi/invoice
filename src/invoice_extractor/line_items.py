import re

NUMBER_RE = re.compile(
    r"^[+-]?\$?[+-]?[\d,]+(?:\.\d+)?%?(?:\s*(?:hrs?|hours?|units?|pcs?|x))?$", re.IGNORECASE)

STOP_RE = re.compile(
    r"(?i)^\s*(?:sub-?\s*total|grand\s+total|total\b|total\s+due|parts\s+subtotal|labou?r\s+subtotal"
    r"|taxable\s+amount|discount|sales\s+tax|tax\s*\(|tax\s*:|cgst|sgst|igst|round\s*off"
    r"|amount\s+in\s+words|payment\s+(?:information|method|details|due|terms)|bank\b"
    r"|notes?\b|terms\b|warranty|thank\s+you|balance\s+due|amount\s+due|parts\s*:?\s*$|labou?r\s*:?\s*$)"
)

HEADER_PHRASE_RE = re.compile(
    r"#|description\s+of\s+goods|description|hours\s*/\s*qty|hours|qty|quantity|rate\s*/\s*hr"
    r"|rate\s*\(inr\)|rate|unit\s*price|price|taxable\s+value|amount|hsn|code|part\s*#|operation"
    r"|total\s*\(inr\)|total|cgst\s*\d+%|sgst\s*\d+%|igst\s*\d+%|sku",
    re.IGNORECASE,
)
NUMBER_PART = r"[+-]?\$?[+-]?[\d,]+(?:\.\d+)?%?(?:\s*(?:hrs?|hours?|units?|pcs?|x)\b)?"
TRAILING_NUMBERS_RE = re.compile(r"((?:\s+" + NUMBER_PART + r")+)$", re.IGNORECASE)
OCR_ONE_RE = re.compile(r"(?<=\s)[Il](?=\s+\$?[\d,]+(?:\.\d+)?(?:\s|$))|^[Il]$")

PLACEHOLDER = "∅"

def is_number(token: str) -> bool:
    if token == PLACEHOLDER:
        return True
    token = token.strip()
    return bool(NUMBER_RE.match(token)) and any(ch.isdigit() for ch in token)

def parse_number(token: str):
    if token == PLACEHOLDER:
        return None
    core = re.sub(r"(?i)\s*(hrs?|hours?|units?|pcs?|x)$", "", token.strip())
    return float(core.replace("$", "").replace(",", "").replace("%", ""))

HEADER_WORD_RE = re.compile(
    r"#|no\.?|sr\.?\s*no\.?|s\.?\s*no\.?|sl\.?\s*no\.?|line|code|part\s*(#|no\.?)|item\s*(code|#|no\.?)|sku"
    r"|product\s*code|hsn(\s*/\s*sac)?|sac|description(\s+of\s+\w+)?|desc\.?|items?|particulars|operation"
    r"|date|timekeeper|staff|employee|person"
    r"|service|product|details|work|hours?(\s*/\s*qty)?|qty|quantity|hrs|units?|pcs"
    r"|rates?(\s*/\s*hr|\s*\(inr\))?|hourly\s+rate|unit\s*price|price|charge|fee|cost|each"
    r"|amount|taxable\s+value|(line\s+)?total(\s*\(inr\))?|cgst\s*\d+%|sgst\s*\d+%|igst\s*\d+%|tax|gst|vat",
    re.IGNORECASE,
)

def is_header_word(cell: str) -> bool:
    return bool(HEADER_WORD_RE.fullmatch(cell.strip())) and role_of(cell) is not None

def role_of(cell: str):
    c = cell.strip().lower()
    if len(c) > 40:
        return None
    if re.fullmatch(r"#|no\.?|sr\.?\s*no\.?|s\.?\s*no\.?|sl\.?\s*no\.?|line", c):
        return "index"
    if re.fullmatch(r"code|part\s*(#|no\.?)|item\s*(code|#|no\.?)|sku|product\s*code|item\s*id", c):
        return "code"
    if c.startswith("hsn") or c.startswith("sac"):
        return "hsn"
    if re.search(r"cgst|sgst|igst|\btax\b|\bgst\b|\bvat\b", c):
        return "tax"
    if re.search(r"desc|item|particular|operation|service|product|detail|work", c):
        return "desc"
    if re.search(r"^(date|timekeeper|staff|employee|person)$", c):
        return "text"
    if re.search(r"rate|price|charge|\bfee\b|\bcost\b|\beach\b", c):
        return "rate"
    if re.search(r"\bqty|quantity|\bhours?\b|\bhrs\b|\bunits?\b|\bpcs\b", c):
        return "qty"
    if "taxable" in c:
        return "taxable"
    if "amount" in c:
        return "amount"
    if "total" in c:
        return "total"
    return None

def _header_at(lines: list[str], i: int):
    line = lines[i].strip()
    if not line:
        return None

    if "|" in line or re.search(r"\s{2,}", line):
        cells = [c.strip() for c in (line.split("|") if "|" in line else re.split(r"\s{2,}", line)) if c.strip()]
        if len(cells) >= 2 and all(is_header_word(c) for c in cells):
            return cells, i + 1

    elif re.fullmatch(r"(?:\s*(?:" + HEADER_PHRASE_RE.pattern + r")\s*)+", line, re.IGNORECASE):
        cells = [m.group(0) for m in HEADER_PHRASE_RE.finditer(line)]
        if len(cells) >= 2:
            return cells, i + 1

    run = []
    j = i
    while j < len(lines) and lines[j].strip():
        cell = lines[j].strip()
        if cell.endswith("/") and j + 1 < len(lines):
            cell = f"{cell} {lines[j + 1].strip()}"
            j += 1
        if not is_header_word(cell):
            break
        run.append(cell)
        j += 1
    if len(run) >= 2 or (len(run) == 1 and run[0].strip() == "#"):
        return run, j
    return None

def _columns(cells: list[str]) -> list[dict]:
    return [{"name": cell, "role": role_of(cell) or "other"} for cell in cells]

def _is_valid_header(columns: list[dict]) -> bool:
    roles = {c["role"] for c in columns}
    return "desc" in roles and bool(roles & {"qty", "rate", "amount", "taxable", "total"})

def _line_cells(line: str, has_index: bool) -> list[str]:
    s = line.strip()
    if "|" in s:
        cells = [c.strip() for c in s.split("|") if c.strip()]
    elif re.search(r"\s{2,}", s):
        cells = [c for c in re.split(r"\s{2,}", s) if c]
    else:
        m = TRAILING_NUMBERS_RE.search(s)
        if m and m.start() > 0 and not is_number(s):
            cells = [s[:m.start()].strip()] + re.findall(NUMBER_PART, m.group(1), re.IGNORECASE)
        else:
            cells = [s]

    if has_index and cells and not is_number(cells[0]):
        m = re.match(r"^(\d{1,4})\s+(.+)$", cells[0])
        if m:
            cells[0:1] = [m.group(1), m.group(2)]
    return cells

def _parse_tokens(tokens: list[str], columns: list[dict]) -> list[dict]:
    rows = []
    i = 0
    n = len(tokens)
    while i < n:
        start = i
        values = {"desc": []}
        cells_by_col = []
        for col in columns:
            role = col["role"]
            if role == "index":
                if i < n and is_number(tokens[i]):
                    i += 1
                cells_by_col.append(None)
            elif role == "desc":
                while i < n and not is_number(tokens[i]):
                    values["desc"].append(tokens[i])
                    i += 1
                cells_by_col.append(None)
            elif role in ("code", "text"):
                if i < n and not is_number(tokens[i]):
                    cells_by_col.append(tokens[i])
                    i += 1
                else:
                    cells_by_col.append(None)
            else:
                if i < n and is_number(tokens[i]):
                    cells_by_col.append(parse_number(tokens[i]))
                    i += 1
                else:
                    cells_by_col.append(None)
        if i == start:
            i += 1
            continue
        description = " ".join(values["desc"]).strip()
        if description or any(v is not None for v in cells_by_col):
            rows.append({"desc": description, "cells": cells_by_col, "columns": columns})
    return rows

def _to_item(row: dict) -> dict:
    by_role: dict[str, list] = {}
    for col, value in zip(row["columns"], row["cells"]):
        if value is not None:
            by_role.setdefault(col["role"], []).append(value)

    def first(*roles):
        for role in roles:
            if by_role.get(role):
                return by_role[role][0]
        return ""

    tax_values = [v for v in by_role.get("tax", []) if isinstance(v, float)]
    amount = first("amount", "taxable", "total")
    total = first("total")
    rate = first("rate")
    qty = first("qty")
    if qty == "" and rate != "" and amount != "" and abs(rate - amount) < 0.005:
        qty = 1.0
    return {
        "Code / HSN": first("code", "hsn"),
        "Extra Info": " | ".join(str(v) for v in by_role.get("text", [])),
        "Description": re.sub(r"\s+", " ", row["desc"]).strip(" |"),
        "Qty": qty,
        "Unit Price": first("rate"),
        "Amount": amount,
        "Line Tax": round(sum(tax_values), 2) if tax_values else "",
        "Line Total": total if total != amount else "",
    }

def parse_line_items(text: str) -> list[dict]:
    lines = [OCR_ONE_RE.sub("1", line) for line in text.splitlines()]
    items: list[dict] = []
    i = 0
    while i < len(lines):
        header = _header_at(lines, i)
        if header is None:
            i += 1
            continue
        cells, next_index = header
        columns = _columns(cells)
        if not _is_valid_header(columns):
            i = next_index
            continue

        has_index = any(c["role"] == "index" for c in columns)
        body = []
        k = next_index
        while k < len(lines) and not STOP_RE.match(lines[k]) and _header_at(lines, k) is None:
            body.append(lines[k])
            k += 1

        items.extend(_parse_body(body, columns, has_index))
        i = k
    return [_to_item(row) for row in items]

NUMERIC_ROLES = ("qty", "rate", "amount", "taxable", "total", "tax", "hsn", "other")

def _pad_missing_numbers(cells: list[str], columns: list[dict], has_index: bool) -> list[str]:
    offset = 1 if has_index and cells and is_number(cells[0]) else 0
    head, body = cells[:offset], cells[offset:]
    expected = sum(1 for c in columns if c["role"] in NUMERIC_ROLES)
    positions = [i for i, c in enumerate(body) if is_number(c)]
    missing = expected - len(positions)
    if missing > 0 and positions:
        first = positions[0]
        body = body[:first] + [PLACEHOLDER] * missing + body[first:]
    return head + body

def _parse_body(body: list[str], columns: list[dict], has_index: bool) -> list[dict]:
    rows = []
    buffer_tokens: list[str] = []
    for line in body:
        if not line.strip():
            continue
        cells = _line_cells(line, has_index)
        if sum(is_number(c) for c in cells) >= 2:
            if buffer_tokens:
                rows.extend(_parse_tokens(buffer_tokens, columns))
                buffer_tokens = []
            cells = _pad_missing_numbers(cells, columns, has_index)
            rows.extend(_parse_tokens(cells, columns))
        else:
            buffer_tokens.append(line.strip())
    if buffer_tokens:
        rows.extend(_parse_tokens(buffer_tokens, columns))
    return rows
