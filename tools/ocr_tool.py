#!/usr/bin/env python3
"""
OCR tool with auto-fallback for law-import skill.

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

def ocr_image(image_path: str, languages: Optional[list] = None) -> dict:
    """OCR a single image, auto-selecting engine."""
    if languages is None:
        languages = ["chi_sim", "eng"]

    # Try EasyOCR first (better for Chinese), fall back to Tesseract
    if check_easyocr():
        try:
            return ocr_with_easyocr(image_path, languages)
        except Exception as e:
            print(f"EasyOCR failed: {e}", file=sys.stderr)
            print("Falling back to Tesseract...", file=sys.stderr)

    if check_tesseract():
        try:
            return ocr_with_tesseract(image_path, languages)
        except Exception as e:
            return {
                "text": "",
                "confidence": 0.0,
                "engine": "none",
                "error": f"Tesseract OCR failed: {e}",
                "per_page": [],
            }

    return {
        "text": "",
        "confidence": 0.0,
        "engine": "none",
        "error": "No OCR engine available. Install EasyOCR: pip install easyocr\n"
                 "Or Tesseract: https://github.com/UB-Mannheim/tesseract/wiki",
        "per_page": [],
    }

def ocr_pdf(pdf_path: str, pages: Optional[str] = None, languages: Optional[list] = None) -> dict:
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

        result = ocr_image(tmp_path, languages)
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

def ocr_batch(directory: str, languages: Optional[list] = None) -> list:
    """Batch OCR all images in a directory."""
    results = []
    dir_path = Path(directory)
    for ext in SUPPORTED_IMAGE_EXTS:
        for img_path in dir_path.glob(f"*{ext}"):
            result = ocr_image(str(img_path), languages)
            result["file"] = str(img_path)
            results.append(result)
    return results

def main():
    parser = argparse.ArgumentParser(description="OCR tool for law-import skill")
    parser.add_argument("--input", "-i", help="Input image/PDF file or directory (for --batch)")
    parser.add_argument("--mode", "-m", choices=["image", "pdf", "batch"], default="image",
                        help="OCR mode")
    parser.add_argument("--lang", default="chi_sim+eng",
                        help="Languages (Tesseract format: chi_sim+eng, or comma-separated: chi_sim,eng)")
    parser.add_argument("--pages", help="Page range for PDF (e.g., 1-10 or 5)")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--check-engines", action="store_true",
                        help="Check available OCR engines and exit")
    args = parser.parse_args()

    if args.check_engines:
        info = {
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
        results = ocr_batch(args.input, languages)
    elif args.mode == "pdf":
        results = ocr_pdf(args.input, args.pages, languages)
    else:
        results = ocr_image(args.input, languages)

    output = json.dumps(results, indent=2, ensure_ascii=False, default=str)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"OCR results written to {args.output}", file=sys.stderr)
    else:
        print(output)

if __name__ == "__main__":
    main()
