import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from invoice_extractor.excel_writer import write_workbook
from invoice_extractor.extractor import extract_line_items, process_text
from invoice_extractor.reader import SUPPORTED_SUFFIXES, read_documents

INPUT_DIR = ROOT / "data" / "input"
PROCESSED_DIR = ROOT / "data" / "processed"
FAILED_DIR = ROOT / "data" / "failed"
OUTPUT_FILE = ROOT / "data" / "output" / "invoices.xlsx"
INDEX_NAME = "processed_index.json"

def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()

def load_index(processed_dir: Path) -> dict:
    index_file = processed_dir / INDEX_NAME
    if not index_file.exists():
        return {}
    return json.loads(index_file.read_text(encoding="utf-8"))

def save_index(processed_dir: Path, index: dict) -> None:
    (processed_dir / INDEX_NAME).write_text(
        json.dumps(index, indent=1, ensure_ascii=False, default=str), encoding="utf-8")

def move_to_folder(path: Path, folder: Path) -> Path:
    target = folder / path.name
    counter = 2
    while target.exists():
        target = folder / f"{path.stem}_{counter}{path.suffix}"
        counter += 1
    shutil.move(str(path), str(target))
    return target

def move_to_failed(path: Path, failed_dir: Path, reason: str) -> None:
    failed_dir.mkdir(parents=True, exist_ok=True)
    target = move_to_folder(path, failed_dir)
    target.with_name(target.name + ".error.txt").write_text(
        f"{path.name} could not be processed:\n{reason}\n", encoding="utf-8")

def collect_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    return sorted(p for p in input_path.iterdir()
                  if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES)

def invoice_key(row: dict, text: str) -> str:
    number = (row.get("Invoice No") or "").strip().upper()
    if number:
        return f"no:{number}"
    return "text:" + hashlib.sha1(" ".join(text.split()).lower().encode("utf-8")).hexdigest()

def unique_items(items: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for item in items:
        key = (item["File Name"], item["Description"].lower(), item.get("Qty"), item.get("Amount"))
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result

def run(input_path: Path, output_file: Path, processed_dir: Path | None = None,
        failed_dir: Path | None = None) -> int:
    index = load_index(processed_dir) if processed_dir else {}
    seen_invoices: dict[str, str] = {key: rec["name"] for rec in index.values() for key in rec["keys"]}
    new_records: dict[str, dict] = {}
    to_move: list[tuple[Path, str | None]] = []
    duplicate_files = 0
    failed_files = 0

    for path in collect_files(input_path):
        digest = file_hash(path)
        if digest in index or digest in new_records:
            print(f"[DUPLICATE] {path.name} was already processed - not scanned again")
            duplicate_files += 1
            to_move.append((path, None))
            continue

        reason = None
        try:
            documents = read_documents(path)
        except Exception as exc:
            reason = str(exc)
        if reason is None and not any(doc.strip() for doc in documents):
            reason = "no text could be read from this file (empty, or a scan too unclear for OCR)"
        if reason is not None:
            print(f"[ERROR] {path.name}: {reason}")
            failed_files += 1
            if failed_dir:
                try:
                    move_to_failed(path, failed_dir, reason)
                except OSError as exc:
                    print(f"  could not move {path.name} to {failed_dir}: {exc}")
            continue

        record = {"name": path.name, "rows": [], "line_items": [], "keys": []}
        for number, text in enumerate(documents, start=1):
            name = path.name if len(documents) == 1 else f"{path.name} (invoice {number}/{len(documents)})"
            row = process_text(name, text)

            key = invoice_key(row, text)
            if key in seen_invoices:
                print(f"[DUPLICATE] {name} is the same invoice as {seen_invoices[key]} - skipped")
                continue
            seen_invoices[key] = name
            record["keys"].append(key)

            record["rows"].append(row)
            items = unique_items([dict(item, **{"File Name": name}) for item in extract_line_items(text)])
            for line_no, item in enumerate(items, start=1):
                item.update({"Invoice No": row.get("Invoice No", ""),
                             "Invoice Date": row.get("Invoice Date", ""),
                             "Category": row["Category"], "Line No": line_no})
                record["line_items"].append(item)
            print(f"{name:45} -> {row['Category']:12} ({len(items)} line items)")

        new_records[digest] = record
        to_move.append((path, digest))

    if failed_files:
        print(f"\n{failed_files} file(s) could not be processed - see {failed_dir}")

    all_records = list(index.values()) + list(new_records.values())
    rows = [row for rec in all_records for row in rec["rows"]]
    line_items = [item for rec in all_records for item in rec["line_items"]]

    if not rows:
        print(f"No supported invoices found in {input_path}")
        print(f"Supported types: {', '.join(sorted(SUPPORTED_SUFFIXES))}")
        return 1

    try:
        write_workbook(rows, output_file, line_items)
    except PermissionError:
        print(f"Cannot write {output_file}. Close it in Excel and run again.")
        return 1

    if processed_dir:
        processed_dir.mkdir(parents=True, exist_ok=True)
        for path, digest in to_move:
            move_to_folder(path, processed_dir)
        index.update(new_records)
        save_index(processed_dir, index)

    if not new_records and duplicate_files:
        print(f"\nNothing new: {duplicate_files} file(s) were already processed and skipped.")
    print(f"\nSaved {len(rows)} invoice(s) and {len(line_items)} line item(s) to {output_file}")
    return 0

def main(argv: list[str] | None = None) -> int:
    if argv:
        parser = argparse.ArgumentParser(
            description="Classify invoices (PDF, Word, text, images) and export fields to Excel.")
        parser.add_argument("input_path", type=Path, help="an invoice file, or a folder of invoices")
        parser.add_argument("output_file", type=Path, help="path of the .xlsx file to create")
        args = parser.parse_args(argv)
        if not args.input_path.exists():
            print(f"Input not found: {args.input_path}")
            return 1
        return run(args.input_path, args.output_file)

    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FAILED_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Reading invoices from: {INPUT_DIR}")
    return run(INPUT_DIR, OUTPUT_FILE, PROCESSED_DIR, FAILED_DIR)

if __name__ == "__main__":
    args = sys.argv[1:]
    exit_code = main(args or None)
    if not args and sys.stdin and sys.stdin.isatty():
        try:
            input("\nPress Enter to close...")
        except EOFError:
            pass
    sys.exit(exit_code)
