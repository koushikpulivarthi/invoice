# Adding or changing a category

All rules live in `src/invoice_extractor/rules.py`.

1. Add an entry to `CATEGORIES`:

```python
"Automobiles": {
    "keywords": ["vehicle", "garage", "workshop", ...],   # words that identify the sector
    "fields": {
        "Vehicle No": {"regex": PLATE_RE},                 # a pattern found anywhere
        "Odometer (km)": {"labels": [r"odometer"], "type": "number"},  # "Label: value"
    },
},
```

2. Keywords: words in the first lines of the invoice count three times, so put the
   sector name in the heading when possible.

3. Field labels: write them as they appear in the invoice, as regular expressions.
   Use `^` at the start to match only at the beginning of a line.

4. Run `pytest` and then the tool on your sample invoices to confirm the new columns.

To mark a category as a fallback (used only when nothing else matches), set `"generic": True`.
