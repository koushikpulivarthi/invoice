"""Command-line entry point.

    invoice-extractor <input_folder_or_file> <output.xlsx>
    python -m invoice_extractor <input_folder_or_file> <output.xlsx>
"""
import argparse
import hashlib
import sys
from pathlib import Path

from .excel_writer import write_workbook
from .extractor import extract_line_items, process_text
from .reader import SUPPORTED_SUFFIXES, read_documents


def collect_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    return sorted(p for p in input_path.iterdir()
                  if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES)


def invoice_key(row: dict, text: str) -> str:
    """Identity of an invoice: its invoice number, or its text if it has no number."""
    number = (row.get("Invoice No") or "").strip().upper()
    if number:
        return f"no:{number}"
    return "text:" + hashlib.sha1(" ".join(text.split()).lower().encode("utf-8")).hexdigest()


def unique_items(items: list[dict]) -> list[dict]:
    """Drop repeated rows inside one invoice (same description, qty and amount)."""
    seen = set()
    result = []
    for item in items:
        key = (item["File Name"], item["Description"].lower(), item.get("Qty"), item.get("Amount"))
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def run(input_path: Path, output_file: Path) -> int:
    rows = []
    line_items = []
    seen_invoices: dict[str, str] = {}
    for path in collect_files(input_path):
        try:
            documents = read_documents(path)     # a PDF may hold several invoices
        except Exception as exc:                 # keep going if one file is broken
            print(f"[ERROR] {path.name}: {exc}")
            continue

        for number, text in enumerate(documents, start=1):
            name = path.name if len(documents) == 1 else f"{path.name} (invoice {number}/{len(documents)})"
            row = process_text(name, text)

            key = invoice_key(row, text)
            if key in seen_invoices:             # same invoice in another file/format
                print(f"[DUPLICATE] {name} is the same invoice as {seen_invoices[key]} - skipped")
                continue
            seen_invoices[key] = name

            rows.append(row)
            items = unique_items([dict(item, **{"File Name": name}) for item in extract_line_items(text)])
            for line_no, item in enumerate(items, start=1):
                item.update({"Invoice No": row.get("Invoice No", ""),
                             "Invoice Date": row.get("Invoice Date", ""),
                             "Category": row["Category"], "Line No": line_no})
                line_items.append(item)
            print(f"{name:45} -> {row['Category']:12} ({len(items)} line items)")

    if not rows:
        print(f"No supported invoices found in {input_path}")
        print(f"Supported types: {', '.join(sorted(SUPPORTED_SUFFIXES))}")
        return 1

    try:
        write_workbook(rows, output_file, line_items)
    except PermissionError:
        print(f"Cannot write {output_file}. Close it in Excel and run again.")
        return 1

    print(f"\nSaved {len(rows)} invoice(s) and {len(line_items)} line item(s) to {output_file}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Classify invoices (PDF, Word, text, images) and export fields to Excel.")
    parser.add_argument("input_path", type=Path, help="an invoice file, or a folder of invoices")
    parser.add_argument("output_file", type=Path, help="path of the .xlsx file to create")
    args = parser.parse_args(argv)

    if not args.input_path.exists():
        print(f"Input not found: {args.input_path}")
        return 1
    return run(args.input_path, args.output_file)


if __name__ == "__main__":
    sys.exit(main())
