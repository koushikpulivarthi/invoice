import re

from .classifier import classify
from .line_items import parse_line_items
from .rules import BLOCK_LABELS, CATEGORIES, COMMON_FIELDS, DEFAULT_CATEGORY, GSTIN_RE

NUMBER_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")

BILL_TO_RE = re.compile(r"Bill\s*To:?[ \t]*\r?\n?[ \t]*([^\n]+)\n([^\n]+)\n([^\n]+)", re.IGNORECASE)
SELLER_HEADER_RE = re.compile(r"^(?:SAMPLE\s+)?INVOICE[ \t]*\r?\n([^\n]+)", re.IGNORECASE | re.MULTILINE)
ZIP_LINE_RE = re.compile(r"^[^\n]*\b[A-Z]{2}\s+\d{5}(?:-\d{4})?\b[^\n]*$", re.MULTILINE)
LINE_ITEM_RE = re.compile(
    r"^\s*(?P<desc>[A-Za-z][^\n]*?)\s+(?P<qty>\d+(?:\.\d+)?)\s+\$?(?P<unit>[\d,]+\.\d{2})\s+\$?(?P<amount>[\d,]+\.\d{2})\s*$",
    re.MULTILINE,
)
BUYER_MARKER_RE = re.compile(r"Bill\s*To|Customer\s*Name|Buyer", re.IGNORECASE)

def find_value(text: str, labels: list[str]) -> str:
    for label in labels:
        anchored = label.startswith("^")
        label = label.lstrip("^")
        prefix = r"^[ \t]*" if anchored else r"\b"
        pattern = (prefix + r"(?:" + label + r")"
                   r"(?:[ \t]*\([^)\r\n]*\)|[ \t]*@[ \t]*[\d.]+%)?"
                   r"[ \t]*[:\-][ \t]*([^\r\n]+)")
        for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
            value = re.split(r"\s{2,}|\t|\|", match.group(1).strip())[0]
            value = re.sub(r"^(?:Rs\.?|INR|₹)\s*", "", value).strip()
            if value:
                return value
    return ""

def extract_field(text: str, spec: dict):
    if "regex" in spec:
        match = re.search(spec["regex"], text)
        value = match.group(spec.get("group", 0)) if match else ""
    else:
        value = find_value(text, spec["labels"])

    if spec.get("type") == "number":
        match = NUMBER_RE.search(value) if value else None
        return float(match.group(0).replace(",", "")) if match else ""
    return value

def _party_blocks(text: str) -> dict:
    result = {"Seller": "", "Seller Address": "", "Buyer": "", "Buyer Address": ""}

    header = SELLER_HEADER_RE.search(text)
    if header and ":" not in header.group(1):
        result["Seller"] = header.group(1).strip()

    marker = BUYER_MARKER_RE.search(text)
    before_buyer = text[:marker.start()] if marker else text
    zip_line = ZIP_LINE_RE.search(before_buyer)
    if zip_line:
        result["Seller Address"] = zip_line.group(0).strip()

    bill_to = BILL_TO_RE.search(text)
    if bill_to and not any(":" in line for line in bill_to.groups()):
        result["Buyer"] = bill_to.group(1).strip()
        result["Buyer Address"] = f"{bill_to.group(2).strip()}, {bill_to.group(3).strip()}"
    return result

def extract_common(text: str) -> dict:
    row = {column: extract_field(text, spec) for column, spec in COMMON_FIELDS.items()}

    gstins = re.findall(GSTIN_RE, text)
    row["Seller GSTIN"] = gstins[0] if gstins else ""
    row["Buyer GSTIN"] = gstins[1] if len(gstins) > 1 else ""

    for column, value in _party_blocks(text).items():
        if not row.get(column):
            row[column] = value

    for column, label in BLOCK_LABELS.items():
        if not row.get(column):
            match = re.search(rf"(?im)(?:^|\|)[ \t]*(?:{label})[ \t]*\r?\n[ \t]*([^|\r\n]+)", text)
            if match:
                value = match.group(1).strip()
                if COMMON_FIELDS.get(column, {}).get("type") == "number":
                    number = NUMBER_RE.search(value)
                    value = float(number.group(0).replace(",", "")) if number else ""
                row[column] = value
    return row

def extract_line_items(text: str) -> list[dict]:
    items = parse_line_items(text)
    return items if items else _extract_line_items_regex(text)

def _extract_line_items_regex(text: str) -> list[dict]:
    items = []
    for match in LINE_ITEM_RE.finditer(text):
        items.append({
            "Description": match.group("desc").strip(),
            "Qty": float(match.group("qty")),
            "Unit Price": float(match.group("unit").replace(",", "")),
            "Amount": float(match.group("amount").replace(",", "")),
        })
    return items

def process_text(file_name: str, text: str) -> dict:
    category = classify(text)
    row = {"File Name": file_name, "Category": category}
    row.update(extract_common(text))
    if category in CATEGORIES:
        for column, spec in CATEGORIES[category]["fields"].items():
            row[column] = extract_field(text, spec)
    return row
#  hello