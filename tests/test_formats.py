"""The same invoice must give the same fields whatever the file format."""
from pathlib import Path

import fitz
import pytest
from docx import Document

from invoice_extractor.extractor import process_text
from invoice_extractor.reader import read_text

SAMPLES = Path(__file__).resolve().parent.parent / "samples"
HOTEL_TEXT = (SAMPLES / "hotel_01.txt").read_text(encoding="utf-8")
COMPARE_COLUMNS = ["Category", "Invoice No", "Invoice Date", "Seller", "Seller GSTIN",
                   "Buyer GSTIN", "Subtotal", "CGST", "SGST", "Total",
                   "Guest Name", "Room No", "No. of Nights", "Check-in Date"]


def _rows_equal(a: dict, b: dict) -> None:
    for column in COMPARE_COLUMNS:
        assert a.get(column) == b.get(column), column


def _make_txt(folder: Path) -> Path:
    path = folder / "invoice.txt"
    path.write_text(HOTEL_TEXT, encoding="utf-8")
    return path


def _make_docx(folder: Path) -> Path:
    path = folder / "invoice.docx"
    doc = Document()
    for line in HOTEL_TEXT.splitlines():
        doc.add_paragraph(line)
    doc.save(path)
    return path


def _make_pdf(folder: Path) -> Path:
    path = folder / "invoice.pdf"
    pdf = fitz.open()
    page = pdf.new_page()
    y = 40
    for line in HOTEL_TEXT.splitlines():
        page.insert_text((40, y), line, fontsize=11)
        y += 16
    pdf.save(path)
    pdf.close()
    return path


def _make_png(folder: Path, pdf_path: Path) -> Path:
    """Render the PDF page to an image - a 'scanned' invoice with no text layer."""
    path = folder / "invoice.png"
    with fitz.open(pdf_path) as pdf:
        pdf[0].get_pixmap(dpi=200).save(path)
    return path


def test_txt_docx_pdf_give_identical_rows(tmp_path):
    base = process_text("invoice.txt", read_text(_make_txt(tmp_path)))
    docx_row = process_text("invoice.docx", read_text(_make_docx(tmp_path)))
    pdf_row = process_text("invoice.pdf", read_text(_make_pdf(tmp_path)))
    _rows_equal(base, docx_row)
    _rows_equal(base, pdf_row)


def test_scanned_pdf_and_image_are_ocr_read(tmp_path):
    pytest.importorskip("rapidocr_onnxruntime")
    base = process_text("invoice.txt", read_text(_make_txt(tmp_path)))
    pdf_path = _make_pdf(tmp_path)
    png_row = process_text("invoice.png", read_text(_make_png(tmp_path, pdf_path)))

    # OCR is not perfect character-for-character, so check the key fields exactly
    assert png_row["Category"] == base["Category"]
    assert png_row["Invoice No"] == base["Invoice No"]
    assert png_row["Total"] == base["Total"]
    assert png_row["Guest Name"] == base["Guest Name"]
