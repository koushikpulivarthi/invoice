from pathlib import Path

from invoice_extractor.extractor import find_value, process_text

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def _row(sample):
    return process_text(sample, (SAMPLES / sample).read_text(encoding="utf-8"))


def test_hotel_fields():
    row = _row("hotel_01.txt")
    assert row["Invoice No"] == "HTL/2026/0456"
    assert row["Seller GSTIN"] == "29ABCDE1234F1Z5"
    assert row["Buyer GSTIN"] == "27AAACT2727Q1ZV"
    assert row["Total"] == 15120.0
    assert row["CGST"] == 810.0
    assert row["No. of Nights"] == 3.0
    assert row["Check-in Date"] == "10-11-2026"


def test_health_date_not_taken_from_admission_date():
    row = _row("health_01.txt")
    assert row["Invoice Date"] == "05/11/2026"
    assert row["Admission Date"] == "01/11/2026"
    assert row["Patient Name"] == "Meena Devi"


def test_bill_no_does_not_pick_up_eway_bill():
    row = _row("logistics_01.txt")
    assert row["Invoice No"] == ""
    assert row["E-Way Bill No"] == "331122334455"
    assert row["Vehicle No"] == "MH12AB1234"
    assert row["IGST"] == 4320.0


def test_subtotal_is_not_read_as_total():
    text = "Sub Total: 1000.00\nTotal: 1180.00"
    assert find_value(text, [r"^total"]) == "1180.00"


def test_category_columns_only_for_detected_category():
    row = _row("retail_01.txt")
    assert row["Store Name"] == "FreshMart Andheri"
    assert "Guest Name" not in row
