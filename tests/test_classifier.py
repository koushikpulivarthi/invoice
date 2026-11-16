from pathlib import Path

import pytest

from invoice_extractor.classifier import classify

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


@pytest.mark.parametrize("sample, expected", [
    ("hotel_01.txt", "Hotel"),
    ("health_01.txt", "Health"),
    ("logistics_01.txt", "Logistics"),
    ("retail_01.txt", "Retail"),
    ("gst_generic_01.txt", "GST"),
])
def test_sample_classification(sample, expected):
    text = (SAMPLES / sample).read_text(encoding="utf-8")
    assert classify(text) == expected


def test_plain_text_is_other():
    assert classify("Just some random words about nothing.") == "Other"


def test_heading_keyword_outweighs_body_mentions():
    # "photography" appears once in the heading (3 points); "consulting" twice in the body (2 points)
    text = "PHOTOGRAPHY INVOICE\nLine 1\nLine 2\nLine 3\nLine 4\nconsulting consulting"
    assert classify(text) == "Photography"
