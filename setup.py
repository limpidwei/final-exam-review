#!/usr/bin/env python3
"""
期末一键复习（Final Review）环境引导脚本。

Detects Python environment and installs all dependencies.
If Python isn't available, this script can't run — but the skill's
Tier 0 mode handles that gracefully without Python.

Usage:
    python setup.py              # Check + install dependencies
    python setup.py --check      # Check only, don't install
    python setup.py --install-agents  # Also run multi-agent install

For users without Python:
    Windows:  winget install Python.Python.3.12
    macOS:    brew install python@3.12
    Linux:    sudo apt install python3 python3-pip
"""

import subprocess
import sys
import os
import platform as pf

# Ensure UTF-8 output on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

REQUIREMENTS_FILE = os.path.join(os.path.dirname(__file__), "requirements.txt")

def run(cmd, **kwargs):
    """Run a command and return (success, output)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, **kwargs
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def check_python():
    """Check Python version."""
    version = sys.version_info
    print(f"  Python {version.major}.{version.minor}.{version.micro} — {'✅' if version >= (3, 9) else '⚠️ 需要 3.9+'}")

def check_pip_package(package_name: str, import_name: str = None) -> bool:
    """Check if a Python package is importable."""
    if import_name is None:
        import_name = package_name.split(">=")[0].split("[")[0]
    try:
        __import__(import_name.replace("-", "_"))
        return True
    except ImportError:
        return False

def check_dependencies():
    """Check which dependencies are installed."""
    print("\n  Dependency check:")
    packages = {
        "python-docx": "docx",
        "PyPDF2": "PyPDF2",
        "python-pptx": "pptx",
        "markdownify": "markdownify",
        "ebooklib": "ebooklib",
        "chardet": "chardet",
        "beautifulsoup4": "bs4",
    }
    optional = {
        "easyocr": "easyocr",
        "pytesseract": "pytesseract",
        "pdf2image": "pdf2image",
        "weasyprint": "weasyprint",
        "jinja2": "jinja2",
    }

    all_ok = True
    for pkg, imp in packages.items():
        ok = check_pip_package(pkg, imp)
        all_ok = all_ok and ok
        print(f"    {'✅' if ok else '❌'} {pkg}")

    print("  Optional:")
    for pkg, imp in optional.items():
        ok = check_pip_package(pkg, imp)
        print(f"    {'✅' if ok else '⬜'} {pkg}")

    return all_ok

def check_ocr_engines():
    """Check OCR engine availability."""
    print("\n  OCR engines:")
    ok = check_pip_package("easyocr", "easyocr")
    print(f"    {'✅' if ok else '⬜'} EasyOCR (GPU加速，中英混合，推荐)")

    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        print("    ✅ Tesseract (系统已安装)")
    except ImportError:
        print("    ⬜ Tesseract Python 绑定 (pip install pytesseract)")
    except Exception:
        print("    ⬜ Tesseract 引擎 (需系统安装: brew install tesseract / apt install tesseract-ocr)")

def install_dependencies():
    """Install all dependencies from requirements.txt."""
    if not os.path.exists(REQUIREMENTS_FILE):
        print("  ⚠️  requirements.txt not found. Skipping.")
        return False

    print(f"\n  Installing dependencies from {REQUIREMENTS_FILE}...")
    ok, output = run(f"{sys.executable} -m pip install -r {REQUIREMENTS_FILE}")
    if ok:
        print("  ✅ Dependencies installed.")
    else:
        print(f"  ⚠️  Some packages may have failed:\n{output[-500:]}")
    return ok

def install_agents():
    """Run multi-agent install if install.py exists."""
    install_py = os.path.join(os.path.dirname(__file__), "install.py")
    if os.path.exists(install_py):
        print("\n  Running multi-agent install...")
        ok, output = run(f"{sys.executable} {install_py}")
        if ok:
            print("  ✅ Agents configured.")
        else:
            print(f"  ⚠️  Agent install had issues:\n{output[-300:]}")
    else:
        print("  ⬜ install.py not found. Skipping agent setup.")

def print_tier_info():
    """Print tier capability summary."""
    print(f"""
  ┌─ Tier 0: 零依赖 (当前可用) ─────────────────────────────┐
  │  • 文本文件 (.md .txt .html) 直接处理                     │
  │  • 资料类型智能分类                                       │
  │  • 课程目录创建                                          │
  │  • Markdown 输出 + 复习资料生成                           │
  │  • 文件发现 (bash find/ls)                               │
  └────────────────────────────────────────────────────────┘
""")
    all_core = check_dependencies()
    if all_core:
        print(f"""
  ┌─ Tier 1: pip 依赖 (当前可用) ───────────────────────────┐
  │  • .docx .pptx .pdf .epub 文本提取                       │
  │  • 幕布 JSON → Markdown                                  │
  │  • HTML → 纯净文本                                       │
  │  • 大文件智能分段                                         │
  │  • MD/HTML/DOCX 多格式输出                               │
  └────────────────────────────────────────────────────────┘
""")
    else:
        print(f"""
  ┌─ Tier 1: pip 依赖 ⬜ 未满足 ────────────────────────────┐
  │  运行: pip install -r requirements.txt                   │
  │  或: python setup.py --install                           │
  └────────────────────────────────────────────────────────┘
""")

def main():
    print("=" * 60)
    print("  期末一键复习 — 环境检测与依赖安装")
    print("=" * 60)

    if "--check" in sys.argv:
        check_python()
        check_dependencies()
        check_ocr_engines()
        return

    if "--install-agents" in sys.argv:
        check_python()
        check_dependencies()
        install_agents()
        return

    # Default: full check + info
    check_python()
    print_tier_info()
    check_ocr_engines()

    if "--install" in sys.argv or "--full" in sys.argv:
        install_dependencies()

    print(f"""
  Quick start:
    pip install -r requirements.txt     # Tier 1
    pip install easyocr                  # Tier 2 (OCR)
    python install.py                    # Deploy to AI agents

  Without Python? The skill works in Tier 0 mode —
  Claude handles text files natively.
  To install Python:
    Windows:  winget install Python.Python.3.12
    macOS:    brew install python@3.12
    Linux:    sudo apt install python3 python3-pip
""")

if __name__ == "__main__":
    main()
