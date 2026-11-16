# Invoice Extractor

Classifies invoices by sector (Health, Automobiles, Webdesign, Photography,
Consulting, Education, Retail, Hotel, Events, Logistics, GST, Other) and
exports the common and sector-specific fields to Excel.

No LLM and no external API: classification uses keyword scoring and
extraction uses label/regex rules.

## Project layout

```
invoice/
├── src/invoice_extractor/      # application package
│   ├── rules.py                # EDIT HERE: categories, keywords, fields
│   ├── classifier.py           # step 1 - choose the sector
│   ├── extractor.py            # steps 2-3 - read common + sector fields
│   ├── reader.py               # read .txt / .pdf text
│   ├── excel_writer.py         # step 4 - build the workbook
│   ├── cli.py                  # command-line entry point
│   └── __main__.py             # enables `python -m invoice_extractor`
├── tests/                      # pytest suite
├── samples/                    # synthetic sample invoices for tests
├── data/
│   ├── input/                  # put your real invoices here (git-ignored)
│   └── output/                 # generated Excel files (git-ignored)
├── docs/
│   └── adding_a_category.md
├── pyproject.toml              # package metadata and dependencies
├── requirements.txt
└── README.md
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows (use source .venv/bin/activate on Linux/macOS)
pip install -e ".[dev]"
```

## Usage

```bash
invoice-extractor data/input data/output/invoices.xlsx
# or
python -m invoice_extractor data/input data/output/invoices.xlsx
```

Input: `.txt` or `.pdf` invoices. Image files (`.jpg`, `.png`) are skipped
because they need OCR; export them to PDF or text first.

Output workbook:
- `All_Invoices` - common fields for every invoice
- One sheet per sector found (for example `Hotel`) - common fields plus that sector's columns

## Tests

```bash
pytest
```

## Tuning

Send a few real invoices and adjust the labels and keywords in
`src/invoice_extractor/rules.py`. See [docs/adding_a_category.md](docs/adding_a_category.md).
