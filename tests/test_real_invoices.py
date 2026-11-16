"""Tests built from the invoice layouts in the client's batch (INV-2026-30x, Sample_Invoice_1-4, 3_fictional)."""
from invoice_extractor.extractor import extract_line_items, process_text
from invoice_extractor.reader import group_pages

CUSTOMER_LAYOUT = """INVOICE
Invoice Number: INV-2026-308
Customer Name: Daniel Anderson
Company Name: FutureGrid AI
Phone: 555-308-8808
Email: accounts@futuregridai.com
Address: 980 Digital Way, Morristown, NJ 07960
Total Amount: $14,280.95
"""

SAMPLE_LAYOUT = """INVOICE
BlueRiver Analytics LLC
125 Business Plaza, Newark, NJ 07102
Phone: (555) 555-1000
accounts@company.com

Bill To:
David Wilson
410 Customer Avenue
Edison, NJ 08817

Invoice No: INV-2026-104
Invoice Date: 01-Nov-2026
Due Date: 15-Nov-2026
Terms: Net 15
Description Qty Unit Price Amount
Dashboard Development 1 $2,200.00 $2,200.00
Data Integration 2 $950.00 $1,900.00
Training Session 1 $750.00 $750.00
Subtotal: $4,850.00
NJ Tax (6.625%): $321.31
Total Due: $5,171.31
Payment Method: Bank Transfer
Bank: Garden State Bank
Account: XXXX4521
Routing: XXXX8899
"""

FICTIONAL_PAGE_1 = """SAMPLE INVOICE
Seller: TechNova Solutions LLC
123 Business Ave, Newark, NJ 07102
Phone: +1 (555) 123-4567
Email: billing@example.com
Bill To: Sarah Johnson
456 Customer Street
Edison, NJ 08817
Invoice Number: INV-2026-002
Invoice Date: 01-Nov-2026
Due Date: 16-Nov-2026
Terms: Net 15 Days
Subtotal: $5,900.00
Tax (6.625%): $390.88
Total Due: $6,290.88
Bank: Example Bank
"""

FICTIONAL_PAGE_2 = FICTIONAL_PAGE_1.replace("INV-2026-002", "INV-2026-003").replace("Sarah Johnson", "Michael Brown")


def test_customer_layout_fields():
    row = process_text("INV-2026-308.pdf", CUSTOMER_LAYOUT)
    assert row["Invoice No"] == "INV-2026-308"
    assert row["Buyer"] == "Daniel Anderson"
    assert row["Buyer Company"] == "FutureGrid AI"
    assert row["Buyer Address"] == "980 Digital Way, Morristown, NJ 07960"
    assert row["Phone"] == "555-308-8808"
    assert row["Email"] == "accounts@futuregridai.com"
    assert row["Total"] == 14280.95
    assert row["Seller"] == ""          # not wrongly taken from "Customer Name"


def test_sample_layout_seller_buyer_and_money():
    row = process_text("Sample_Invoice_4.pdf", SAMPLE_LAYOUT)
    assert row["Seller"] == "BlueRiver Analytics LLC"
    assert row["Seller Address"] == "125 Business Plaza, Newark, NJ 07102"
    assert row["Buyer"] == "David Wilson"
    assert row["Buyer Address"] == "410 Customer Avenue, Edison, NJ 08817"
    assert row["Subtotal"] == 4850.0
    assert row["Tax"] == 321.31
    assert row["Tax Rate (%)"] == 6.625
    assert row["Total"] == 5171.31
    assert row["Payment Terms"] == "Net 15"
    assert row["Payment Method"] == "Bank Transfer"
    assert row["Bank"] == "Garden State Bank"
    assert row["Account No"] == "XXXX4521"
    assert row["Routing No"] == "XXXX8899"
    assert row["Invoice Date"] == "01-Nov-2026"
    assert row["Due Date"] == "15-Nov-2026"


def test_line_items_are_extracted():
    items = extract_line_items(SAMPLE_LAYOUT)
    assert [i["Description"] for i in items] == ["Dashboard Development", "Data Integration", "Training Session"]
    assert {k: items[1][k] for k in ("Description", "Qty", "Unit Price", "Amount")} == {
        "Description": "Data Integration", "Qty": 2.0, "Unit Price": 950.0, "Amount": 1900.0}


def test_fictional_seller_and_tax_rate():
    row = process_text("3_fictional_invoices.pdf", FICTIONAL_PAGE_1)
    assert row["Seller"] == "TechNova Solutions LLC"
    assert row["Seller Address"] == "123 Business Ave, Newark, NJ 07102"
    assert row["Buyer"] == "Sarah Johnson"
    assert row["Buyer Address"] == "456 Customer Street, Edison, NJ 08817"
    assert row["Email"] == "billing@example.com"
    assert row["Tax"] == 390.88


def test_multi_invoice_pdf_is_split_per_invoice_number():
    pages = [FICTIONAL_PAGE_1, FICTIONAL_PAGE_2]
    documents = group_pages(pages)
    assert len(documents) == 2
    assert "INV-2026-002" in documents[0] and "INV-2026-003" in documents[1]


def test_page_without_invoice_number_continues_previous_invoice():
    documents = group_pages([FICTIONAL_PAGE_1, "Continued terms and conditions text"])
    assert len(documents) == 1
