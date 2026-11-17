# Invoice Extractor

Classifies invoices by sector (Health, Automobiles, Webdesign, Photography,Consulting, Education, Retail, Hotel, Events, Logistics, GST, Other) and
exports the common and sector-specific fields to Excel.

## Project layout

```
invoice/
├── src/invoice_extractor/      # application package
│   ├── rules.py                # EDIT HERE: categories, keywords, fields
│   ├── classifier.py           # step 1 - choose the sector
│   ├── extractor.py            # steps 2-3 - read common + sector fields
│   ├── reader.py               # read .txt / .pdf text
│   └── excel_writer.py         # step 4 - build the workbook
├── main.py                     # the whole program: run it, double-click it, or give paths
├── samples/                    # synthetic sample invoices (try them with main.py)
├── data/
│   ├── input/                  # put your real invoices here (git-ignored)
│   ├── processed/              # invoices that were read successfully (git-ignored)
│   ├── failed/                 # invoices that could not be read, with a .error.txt note (git-ignored)
│   └── output/                 # generated Excel files (git-ignored)
├── pyproject.toml              # package metadata and dependencies
├── requirements.txt
└── README.md
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows (use source .venv/bin/activate on Linux/macOS)
pip install -r requirements.txt
```

## Usage

```bash
python main.py                                   # uses data/input, data/processed, data/failed, data/output
python main.py data/input data/output/invoices.xlsx   # or give your own paths
```

Input: `.txt`, `.pdf`, `.docx` and image files (`.jpg`, `.png` and similar).
Scanned PDF pages and images are read with OCR. Old `.doc` files must be saved as `.docx` first.

A file that cannot be read, or has no text in it, is moved to `data/failed/` with a
`<name>.error.txt` file saying why. Fix or replace it, then put it back in `data/input/`.

Output workbook:
- `All_Invoices` - common fields for every invoice
- One sheet per sector found (for example `Hotel`) - common fields plus that sector's columns

## Tuning

Send a few real invoices and adjust the labels and keywords in
`src/invoice_extractor/rules.py`.
