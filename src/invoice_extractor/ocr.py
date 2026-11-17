from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image

@lru_cache(maxsize=1)
def _engine():
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as exc:
        raise RuntimeError("OCR is not installed (pip install rapidocr_onnxruntime)") from exc
    return RapidOCR()

def load_image(source) -> np.ndarray:
    image = source if isinstance(source, Image.Image) else Image.open(Path(source))
    rgb = np.array(image.convert("RGB"))
    return rgb[:, :, ::-1]

def ocr_image(source) -> str:
    result, _ = _engine()(load_image(source))
    if not result:
        return ""

    items = []
    for box, text, _score in result:
        ys = [point[1] for point in box]
        xs = [point[0] for point in box]
        items.append({"y": sum(ys) / 4, "h": max(ys) - min(ys), "x": min(xs), "text": text})
    items.sort(key=lambda item: item["y"])

    lines = []
    for item in items:
        if lines and abs(item["y"] - lines[-1]["y"]) <= 0.5 * max(item["h"], lines[-1]["h"]):
            lines[-1]["parts"].append(item)
        else:
            lines.append({"y": item["y"], "h": item["h"], "parts": [item]})

    output = []
    for line in lines:
        parts = sorted(line["parts"], key=lambda part: part["x"])
        output.append(" ".join(part["text"] for part in parts))
    return "\n".join(output)
