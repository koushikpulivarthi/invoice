from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from .rules import CATEGORIES, COMMON_COLUMNS, DEFAULT_CATEGORY, LINE_ITEM_COLUMNS

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
HEADER_FONT = Font(bold=True, color="FFFFFF")
NUMBER_FORMAT = "#,##0.00"
MAX_WIDTH = 45

def _write_sheet(wb: Workbook, title: str, columns: list[str], rows: list[dict]) -> None:
    ws = wb.create_sheet(title[:31])
    ws.append(columns)
    for cell in ws[1]:
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for row in rows:
        ws.append([row.get(column, "") for column in columns])

    for idx, column in enumerate(columns, start=1):
        longest = max([len(column)] + [len(str(r.get(column, ""))) for r in rows])
        ws.column_dimensions[ws.cell(row=1, column=idx).column_letter].width = min(longest + 3, MAX_WIDTH)
        for (cell,) in ws.iter_rows(min_row=2, min_col=idx, max_col=idx):
            if isinstance(cell.value, (int, float)):
                cell.number_format = NUMBER_FORMAT

    for line in ws.iter_rows(min_row=1, max_row=ws.max_row, max_col=len(columns)):
        for cell in line:
            cell.border = BORDER
            if cell.row > 1:
                cell.alignment = Alignment(vertical="top", wrap_text=isinstance(cell.value, str))

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

def write_workbook(rows: list[dict], out_path: Path, line_items: list[dict] | None = None) -> None:
    wb = Workbook()
    wb.remove(wb.active)
    _write_sheet(wb, "All_Invoices", COMMON_COLUMNS, rows)

    for category in list(CATEGORIES) + [DEFAULT_CATEGORY]:
        cat_rows = [r for r in rows if r["Category"] == category]
        if not cat_rows:
            continue
        extra = list(CATEGORIES[category]["fields"]) if category in CATEGORIES else []
        _write_sheet(wb, category, COMMON_COLUMNS + extra, cat_rows)

    if line_items:
        _write_sheet(wb, "Line Items", LINE_ITEM_COLUMNS, line_items)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
