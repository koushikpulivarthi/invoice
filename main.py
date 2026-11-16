"""Run the invoice extractor with no arguments.

    1. Put invoices (.pdf, .docx, .txt, images) in  data/input/
    2. Run this file:  python main.py   (or double-click it)
    3. Result is saved to  data/output/invoices.xlsx
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))  # works even if the package was not installed

from invoice_extractor.cli import run  # noqa: E402

INPUT_DIR = ROOT / "data" / "input"
OUTPUT_FILE = ROOT / "data" / "output" / "invoices.xlsx"


def main() -> int:
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Reading invoices from: {INPUT_DIR}")
    code = run(INPUT_DIR, OUTPUT_FILE)
    return code


if __name__ == "__main__":
    exit_code = main()
    if sys.stdin and sys.stdin.isatty():  # keep the window open when double-clicked
        try:
            input("\nPress Enter to close...")
        except EOFError:
            pass
    sys.exit(exit_code)
