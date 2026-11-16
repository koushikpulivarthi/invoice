"""Line-item extraction for each table layout seen in the client's invoices."""
from invoice_extractor.cli import unique_items
from invoice_extractor.line_items import parse_line_items

PIPE_TABLE = """# | DESCRIPTION | HOURS / QTY | RATE | AMOUNT
1 | Custom web application development - Sprint 4 | 80 | $135.00 | $10,800.00
2 | QA testing and bug fixing | 32 | $95.00 | $3,040.00
Subtotal: $13,840.00
"""

ONE_CELL_PER_LINE = """Description
Qty
Rate
Amount
Cloud migration - discovery & planning
40 hrs
$120.00
$4,800.00
Strategy workshop (2 days)
2
$2,400.00
$4,800.00
Subtotal
$9,600.00
"""

PART_CODES_AND_LABOR = """PARTS
Part #
Description
Qty
Unit Price
Amount
BP-4421
Front brake pads, ceramic (set)
1
$89.95
$89.95
OF-5W30
Full synthetic oil 5W-30 (qt)
5
$9.80
$49.00
LABOR
Code
Operation
Hours
Rate / hr
Amount
L1
Replace front pads and rotors; clean and lube slides
1.8
$125.00
$225.00
Parts subtotal
$138.95
"""

GST_TABLE = """#
Description of Goods
HSN
Qty
Rate (INR)
Taxable Value
CGST 9%
SGST 9%
Total (INR)
1
Ergonomic office chair, mesh back
9401
12
4,850.00
58,200.00
5,238.00
5,238.00
68,676.00
2
Height-adjustable study desk 120x60
cm
9403
12
6,200.00
74,400.00
6,696.00
6,696.00
87,792.00
Total
205,350.00
"""

SPLIT_HEADER = """#
DESCRIPTION
HOURS /
QTY
RATE
AMOUNT
1
Cloud migration - discovery & planning
40 hrs
$120.00
$4,800.00
Subtotal
$4,800.00
"""

TIMEKEEPER_TABLE = """Date
Timekeeper
Description of Services
Hrs
Rate
Amount
10/02
M. Reyes
Initial consultation; review of draft 5-year
commercial lease
1.5
$375.00
$562.50
Total fees
$562.50
"""


def test_pipe_separated_rows():
    items = parse_line_items(PIPE_TABLE)
    assert [(i["Description"], i["Qty"], i["Unit Price"], i["Amount"]) for i in items] == [
        ("Custom web application development - Sprint 4", 80.0, 135.0, 10800.0),
        ("QA testing and bug fixing", 32.0, 95.0, 3040.0),
    ]


def test_one_cell_per_line_with_units_and_stop_at_subtotal():
    items = parse_line_items(ONE_CELL_PER_LINE)
    assert len(items) == 2
    assert items[0]["Description"] == "Cloud migration - discovery & planning"
    assert items[0]["Qty"] == 40.0          # "40 hrs" is read as the number 40
    assert items[1]["Amount"] == 4800.0


def test_part_codes_and_second_table_are_both_read():
    items = parse_line_items(PART_CODES_AND_LABOR)
    assert [i["Code / HSN"] for i in items] == ["BP-4421", "OF-5W30", "L1"]
    assert items[2]["Qty"] == 1.8 and items[2]["Unit Price"] == 125.0
    assert items[2]["Description"].startswith("Replace front pads")


def test_gst_table_keeps_hsn_tax_and_wrapped_description():
    items = parse_line_items(GST_TABLE)
    assert len(items) == 2                  # the "Total" row is not an item
    assert items[0]["Code / HSN"] == 9401.0
    assert items[0]["Amount"] == 58200.0
    assert items[0]["Line Tax"] == 10476.0  # CGST + SGST
    assert items[0]["Line Total"] == 68676.0
    assert items[1]["Description"] == "Height-adjustable study desk 120x60 cm"


def test_header_split_over_two_lines():
    items = parse_line_items(SPLIT_HEADER)
    assert items and items[0]["Qty"] == 40.0 and items[0]["Amount"] == 4800.0


def test_timekeeper_and_date_columns_go_to_extra_info():
    items = parse_line_items(TIMEKEEPER_TABLE)
    assert items[0]["Extra Info"] == "10/02 | M. Reyes"
    assert items[0]["Description"] == "Initial consultation; review of draft 5-year commercial lease"
    assert items[0]["Qty"] == 1.5


def test_repeated_rows_inside_one_invoice_are_removed():
    items = [
        {"File Name": "a.pdf", "Description": "Support", "Qty": 1.0, "Amount": 100.0},
        {"File Name": "a.pdf", "Description": "support", "Qty": 1.0, "Amount": 100.0},
        {"File Name": "b.pdf", "Description": "Support", "Qty": 1.0, "Amount": 100.0},
    ]
    assert len(unique_items(items)) == 2
