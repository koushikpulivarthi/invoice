from pathlib import Path

from openpyxl import load_workbook

from invoice_extractor.cli import run

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def test_workbook_has_all_and_category_sheets(tmp_path):
    out = tmp_path / "result.xlsx"
    assert run(SAMPLES, out) == 0

    wb = load_workbook(out)
    assert wb.sheetnames[0] == "All_Invoices"
    for name in ["Hotel", "Health", "Logistics", "Retail", "GST"]:
        assert name in wb.sheetnames

    all_ws = wb["All_Invoices"]
    assert all_ws.max_row - 1 == len(list(SAMPLES.glob("*.txt")))   # one row per sample invoice

    hotel = wb["Hotel"]
    headers = [c.value for c in hotel[1]]
    assert "Guest Name" in headers and "Check-in Date" in headers
    assert "Patient Name" not in headers    # other sectors' columns stay out
