#!/usr/bin/env python3
"""
OCR tool with auto-fallback for 期末一键复习（Final Review）.

Usage:
    python ocr_tool.py --input image.png --lang chi_sim+eng
    python ocr_tool.py --input scanned.pdf --mode pdf --pages 1-10
    python ocr_tool.py --input dir/ --batch
    python ocr_tool.py --check-engines          # Check available OCR engines

Output: JSON {text, confidence, engine, per_page: [{page, text, conf}]}
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

SUPPORTED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}

def check_paddleocr() -> bool:
    """Check if PaddleOCR is available."""
    try:
        import paddleocr  # noqa: F401
        return True
    except ImportError:
        return False

def check_tesseract() -> bool:
    """Check if Tesseract is available."""
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        return version is not None
    except ImportError:
        return False
    except Exception:
        return False

def check_easyocr() -> bool:
    """Check if EasyOCR is available."""
    try:
        import easyocr
        return True
    except ImportError:
        return False

# PaddleOCR reader is expensive to initialize — reuse across calls (batch/PDF)
_paddle_reader = None

def ocr_with_paddleocr(image_path: str, languages: list) -> dict:
    """Run OCR with PaddleOCR (best Chinese accuracy)."""
    from paddleocr import PaddleOCR

    global _paddle_reader
    if _paddle_reader is None:
        lang = "ch" if any(l.startswith("chi") for l in languages) else "en"
        # enable_mkldnn=False: paddlepaddle 3.3.x crashes on Windows CPU oneDNN
        # (ConvertPirAttribute2RuntimeAttribute) — required workaround.
        _paddle_reader = PaddleOCR(
            lang=lang,
            enable_mkldnn=False,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )

    results = _paddle_reader.predict(input=image_path)

    text_parts = []
    confidences = []
    for r in results:
        text_parts.extend(r["rec_texts"])
        confidences.extend(float(s) for s in r["rec_scores"])

    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    text = "\n".join(text_parts)
    return {
        "text": text,
        "confidence": round(avg_conf, 4),
        "engine": "paddleocr",
        "per_page": [{"page": 1, "text": text, "confidence": round(avg_conf, 4)}],
    }

def ocr_with_easyocr(image_path: str, languages: list) -> dict:
    """Run OCR with EasyOCR."""
    import easyocr
    import numpy as np
    from PIL import Image, ImageEnhance, ImageFilter

    # Preprocess image
    img = Image.open(image_path)
    # Convert to RGB if needed
    if img.mode != "RGB":
        img = img.convert("RGB")
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)
    # Sharpen
    img = img.filter(ImageFilter.SHARPEN)

    # Convert to numpy array
    img_array = np.array(img)

    # Map language codes to EasyOCR format
    # EasyOCR uses language codes: ch_sim, en, etc.
    lang_map = {
        "chi_sim": "ch_sim",
        "chi_tra": "ch_tra",
        "eng": "en",
        "jpn": "ja",
        "kor": "ko",
    }
    easyocr_langs = [lang_map.get(l, l) for l in languages]
    if not easyocr_langs:
        easyocr_langs = ["ch_sim", "en"]

    reader = easyocr.Reader(easyocr_langs, gpu=True)
    results = reader.readtext(img_array)

    text_parts = []
    confidences = []
    for bbox, text, conf in results:
        text_parts.append(text)
        confidences.append(conf)

    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    return {
        "text": "\n".join(text_parts),
        "confidence": round(avg_conf, 4),
        "engine": "easyocr",
        "per_page": [{"page": 1, "text": "\n".join(text_parts), "confidence": round(avg_conf, 4)}],
    }

def ocr_with_tesseract(image_path: str, languages: list) -> dict:
    """Run OCR with Tesseract."""
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter

    # Preprocess
    img = Image.open(image_path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)
    img = img.filter(ImageFilter.SHARPEN)

    # Build language string for Tesseract
    lang_str = "+".join(languages) if languages else "chi_sim+eng"

    # Get OCR data with confidence
    data = pytesseract.image_to_data(img, lang=lang_str, output_type=pytesseract.Output.DICT)

    text_parts = []
    confidences = []
    for i, text in enumerate(data["text"]):
        conf = int(data["conf"][i]) if data["conf"][i] != "-1" else 0
        if text.strip():
            text_parts.append(text.strip())
            confidences.append(conf)

    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    # Normalize to 0-1
    avg_conf = avg_conf / 100.0

    # Also get full text for fallback
    full_text = pytesseract.image_to_string(img, lang=lang_str)

    return {
        "text": full_text.strip(),
        "confidence": round(avg_conf, 4),
        "engine": "tesseract",
        "per_page": [{"page": 1, "text": full_text.strip(), "confidence": round(avg_conf, 4)}],
    }

_ENGINES = {
    "paddleocr": (check_paddleocr, ocr_with_paddleocr),
    "easyocr": (check_easyocr, ocr_with_easyocr),
    "tesseract": (check_tesseract, ocr_with_tesseract),
}

# Auto priority: best Chinese accuracy first, lightest dependency as last resort.
# This is only a default — callers can pin any engine via --engine.
_AUTO_PRIORITY = ["paddleocr", "easyocr", "tesseract"]

def _engine_error(message: str) -> dict:
    return {"text": "", "confidence": 0.0, "engine": "none", "error": message, "per_page": []}

def ocr_image(image_path: str, languages: Optional[list] = None, engine: str = "auto") -> dict:
    """OCR a single image. engine='auto' tries engines by priority; or pin one explicitly."""
    if languages is None:
        languages = ["chi_sim", "eng"]

    if engine != "auto":
        if engine not in _ENGINES:
            return _engine_error(f"Unknown engine '{engine}'. Available: {list(_ENGINES)}")
        check, run = _ENGINES[engine]
        if not check():
            return _engine_error(f"Requested engine '{engine}' is not installed")
        try:
            return run(image_path, languages)
        except Exception as e:
            return _engine_error(f"{engine} OCR failed: {e}")

    for name in _AUTO_PRIORITY:
        check, run = _ENGINES[name]
        if not check():
            continue
        try:
            return run(image_path, languages)
        except Exception as e:
            print(f"{name} failed: {e}", file=sys.stderr)
            print("Falling back to next engine...", file=sys.stderr)

    return _engine_error(
        "No OCR engine available. Install one of:\n"
        "  paddleocr:    pip install paddlepaddle paddleocr  (best Chinese)\n"
        "  easyocr:      pip install easyocr\n"
        "  tesseract:    pip install pytesseract + system Tesseract"
    )

def ocr_pdf(pdf_path: str, pages: Optional[str] = None, languages: Optional[list] = None,
            engine: str = "auto") -> dict:
    """OCR a scanned PDF by converting pages to images first."""
    try:
        from pdf2image import convert_from_path
    except ImportError:
        return {
            "text": "",
            "confidence": 0.0,
            "engine": "none",
            "error": "pdf2image not installed. Run: pip install pdf2image\n"
                     "Also requires poppler: https://github.com/oschwartz10612/poppler-windows/releases/",
            "per_page": [],
        }

    if languages is None:
        languages = ["chi_sim", "eng"]

    # Parse page range
    page_range = None
    if pages:
        parts = pages.split("-")
        if len(parts) == 2:
            page_range = (int(parts[0]), int(parts[1]))
        else:
            page_range = (1, int(parts[0]))

    try:
        if page_range:
            images = convert_from_path(pdf_path, first_page=page_range[0], last_page=page_range[1])
        else:
            images = convert_from_path(pdf_path)
    except Exception as e:
        return {
            "text": "",
            "confidence": 0.0,
            "engine": "none",
            "error": f"Failed to convert PDF pages to images: {e}",
            "per_page": [],
        }

    per_page = []
    all_text = []
    all_confidences = []

    for i, img in enumerate(images):
        # Save temp image
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            img.save(tmp.name, "PNG")
            tmp_path = tmp.name

        result = ocr_image(tmp_path, languages, engine)
        os.unlink(tmp_path)

        per_page.append({
            "page": i + 1,
            "text": result["text"],
            "confidence": result["confidence"],
        })
        all_text.append(f"--- Page {i+1} ---\n{result['text']}")
        all_confidences.append(result["confidence"])

    avg_conf = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
    return {
        "text": "\n\n".join(all_text),
        "confidence": round(avg_conf, 4),
        "engine": result.get("engine", "unknown"),
        "per_page": per_page,
    }

def ocr_batch(directory: str, languages: Optional[list] = None, engine: str = "auto") -> list:
    """Batch OCR all images in a directory."""
    results = []
    dir_path = Path(directory)
    for ext in SUPPORTED_IMAGE_EXTS:
        for img_path in dir_path.glob(f"*{ext}"):
            result = ocr_image(str(img_path), languages, engine)
            result["file"] = str(img_path)
            results.append(result)
    return results

def main():
    parser = argparse.ArgumentParser(description="OCR tool for 期末一键复习（Final Review）")
    parser.add_argument("--input", "-i", help="Input image/PDF file or directory (for --batch)")
    parser.add_argument("--mode", "-m", choices=["image", "pdf", "batch"], default="image",
                        help="OCR mode")
    parser.add_argument("--lang", default="chi_sim+eng",
                        help="Languages (Tesseract format: chi_sim+eng, or comma-separated: chi_sim,eng)")
    parser.add_argument("--engine", default="auto",
                        choices=["auto", "paddleocr", "easyocr", "tesseract"],
                        help="OCR engine. 'auto' (default) picks best available; pin one to override")
    parser.add_argument("--pages", help="Page range for PDF (e.g., 1-10 or 5)")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--check-engines", action="store_true",
                        help="Check available OCR engines and exit")
    args = parser.parse_args()

    if args.check_engines:
        info = {
            "paddleocr": {"available": check_paddleocr(), "install": "pip install paddlepaddle paddleocr"},
            "easyocr": {"available": check_easyocr(), "install": "pip install easyocr"},
            "tesseract": {"available": check_tesseract(), "install": "pip install pytesseract + system Tesseract"},
        }
        print(json.dumps(info, indent=2, ensure_ascii=False))
        return

    if not args.input:
        parser.print_help()
        sys.exit(1)

    # Parse languages
    languages = [l.strip() for l in args.lang.replace("+", ",").split(",") if l.strip()]

    if args.mode == "batch":
        results = ocr_batch(args.input, languages, args.engine)
    elif args.mode == "pdf":
        results = ocr_pdf(args.input, args.pages, languages, args.engine)
    else:
        results = ocr_image(args.input, languages, args.engine)

    output = json.dumps(results, indent=2, ensure_ascii=False, default=str)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"OCR results written to {args.output}", file=sys.stderr)
    else:
        print(output)

if __name__ == "__main__":
    main()
