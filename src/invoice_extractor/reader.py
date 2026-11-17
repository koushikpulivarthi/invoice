import re
from pathlib import Path

try:
    import pymupdf as fitz
except ImportError:
    import fitz
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

from . import ocr

TEXT_SUFFIXES = {".txt"}
PDF_SUFFIXES = {".pdf"}
WORD_SUFFIXES = {".docx"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
SUPPORTED_SUFFIXES = TEXT_SUFFIXES | PDF_SUFFIXES | WORD_SUFFIXES | IMAGE_SUFFIXES

MIN_PDF_TEXT_CHARS = 20
OCR_DPI = 200

def read_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix in PDF_SUFFIXES:
        return _read_pdf(path)
    if suffix in WORD_SUFFIXES:
        return _read_docx(path)
    if suffix in IMAGE_SUFFIXES:
        return ocr.ocr_image(path)
    raise ValueError(f"unsupported file type '{suffix}' (old .doc files: save as .docx)")

def _read_pdf(path: Path) -> str:
    return "\n".join(_read_pdf_pages(path))

def _read_pdf_pages(path: Path) -> list[str]:
    pages = []
    with fitz.open(path) as pdf:
        for page in pdf:
            text = page.get_text("text").strip()
            if len(text) < MIN_PDF_TEXT_CHARS:
                pixmap = page.get_pixmap(dpi=OCR_DPI, alpha=False)
                text = ocr.ocr_image(_pixmap_to_pil(pixmap))
            pages.append(text)
    return pages

INVOICE_NO_RE = re.compile(r"invoice\s*(?:no|number)\.?\s*:\s*([A-Z0-9][A-Z0-9/\-]*)", re.IGNORECASE)

def group_pages(pages: list[str]) -> list[str]:
    documents: list[str] = []
    last_key = None
    for page in pages:
        match = INVOICE_NO_RE.search(page)
        key = match.group(1) if match else None
        if documents and (key is None or key == last_key):
            documents[-1] += "\n" + page
        else:
            documents.append(page)
        if key:
            last_key = key
    return documents

BAD_CHAR = "�"

def read_documents(path: Path) -> list[str]:
    if path.suffix.lower() == ".pdf":
        docs = group_pages(_read_pdf_pages(path))
    else:
        docs = [read_text(path)]
    return [doc.replace(BAD_CHAR, "–") for doc in docs]

def _pixmap_to_pil(pixmap):
    from PIL import Image
    return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)

def _read_docx(path: Path) -> str:
    document = Document(str(path))
    lines = []
    for child in document.element.body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            lines.append(Paragraph(child, document).text)
        elif tag == "tbl":
            lines.extend(_table_lines(Table(child, document)))
    return "\n".join(lines)

def _table_lines(table: Table) -> list[str]:
    lines = []
    for row in table.rows:
        cells = [cell.text.strip() for cell in row.cells]
        cells = [cell for cell in cells if cell]
        if len(cells) == 2:
            lines.append(f"{cells[0]}: {cells[1]}")
        elif cells:
            lines.append(" | ".join(cells))
    return lines
