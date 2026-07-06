#!/usr/bin/env python3
"""
Cross-platform WeChat/QQ file discovery tool for 期末一键复习（Final Review）.

Usage:
    python file_finder.py --platform wechat          # Auto-discover WeChat download folders
    python file_finder.py --platform qq              # Auto-discover QQ download folders
    python file_finder.py --scan ~/Downloads          # Scan a specific directory
    python file_finder.py --scan-all                  # Scan all common download locations
    python file_finder.py --list-platforms            # List supported platforms and paths

Output: JSON array of {path, size_bytes, mtime, platform, source_dir}
"""

import argparse
import json
import os
import sys
import platform as pf
import glob as glob_mod
from pathlib import Path
from datetime import datetime, timedelta

# Load platform path definitions
CONFIG_PATH = Path(__file__).parent.parent / "config" / "platform_paths.json"

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def expand_path(path_str: str) -> str:
    """Expand ~ and %VAR% in paths to absolute."""
    # Handle ~ for Unix
    path_str = os.path.expanduser(path_str)
    # Handle %VAR% for Windows
    if pf.system() == "Windows":
        import re
        def repl(match):
            var = match.group(1)
            return os.environ.get(var, match.group(0))
        path_str = re.sub(r'%(\w+)%', repl, path_str)
    return os.path.abspath(path_str)

def get_platform_key() -> str:
    system = pf.system()
    if system == "Windows":
        return "windows"
    elif system == "Darwin":
        return "macos"
    else:
        return "linux"

def find_wechat_dirs(config: dict) -> list:
    """Find all WeChat file directories on the current system."""
    results = []
    plat_key = get_platform_key()
    plat_config = config.get("wechat", {}).get(plat_key, {})

    if not plat_config:
        return results

    bases = [expand_path(b) for b in plat_config.get("candidate_bases", [])]
    wxid_pattern = plat_config.get("wxid_pattern", "wxid_*")
    subdirs = plat_config.get("subdirs", {})

    for base in bases:
        if not os.path.isdir(base):
            continue
        # Enumerate wxid directories
        wxid_glob = os.path.join(base, wxid_pattern)
        wxid_dirs = glob_mod.glob(wxid_glob)
        for wxid_dir in wxid_dirs:
            if not os.path.isdir(wxid_dir):
                continue
            for subdir_name, subdir_rel in subdirs.items():
                subdir_path = os.path.join(wxid_dir, subdir_rel)
                if os.path.isdir(subdir_path):
                    file_count = count_files(subdir_path)
                    if file_count > 0:
                        results.append({
                            "path": os.path.abspath(subdir_path),
                            "wxid": os.path.basename(wxid_dir),
                            "type": subdir_name,
                            "file_count": file_count,
                            "mtime": os.path.getmtime(subdir_path),
                            "platform": "wechat",
                            "source_dir": subdir_path,
                        })

    # Check custom path from Windows registry (if available)
    if plat_key == "windows":
        reg_key = plat_config.get("custom_path_registry_key")
        if reg_key:
            try:
                import winreg
                key_path = reg_key.replace("HKEY_CURRENT_USER\\", "")
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
                custom_path, _ = winreg.QueryValueEx(key, "")
                winreg.CloseKey(key)
                if custom_path and os.path.isdir(custom_path):
                    file_count = count_files(custom_path)
                    if file_count > 0:
                        results.append({
                            "path": os.path.abspath(custom_path),
                            "type": "custom_download_path",
                            "file_count": file_count,
                            "mtime": os.path.getmtime(custom_path),
                            "platform": "wechat",
                            "source_dir": custom_path,
                        })
            except Exception:
                pass  # Registry read failed, skip

    return results

def find_qq_dirs(config: dict) -> list:
    """Find all QQ file directories on the current system."""
    results = []
    plat_key = get_platform_key()
    plat_config = config.get("qq", {}).get(plat_key, {})

    if not plat_config:
        return results

    bases = [expand_path(b) for b in plat_config.get("candidate_bases", [])]
    qq_pattern = plat_config.get("qq_number_pattern", "[0-9]*")
    subdirs = plat_config.get("subdirs", {})

    for base in bases:
        if not os.path.isdir(base):
            continue
        # Enumerate QQ number directories
        qq_glob = os.path.join(base, qq_pattern)
        qq_dirs = glob_mod.glob(qq_glob)
        for qq_dir in qq_dirs:
            if not os.path.isdir(qq_dir):
                continue
            for subdir_name, subdir_rel in subdirs.items():
                subdir_path = os.path.join(qq_dir, subdir_rel)
                if os.path.isdir(subdir_path):
                    file_count = count_files(subdir_path)
                    if file_count > 0:
                        results.append({
                            "path": os.path.abspath(subdir_path),
                            "qq_number": os.path.basename(qq_dir),
                            "type": subdir_name,
                            "file_count": file_count,
                            "mtime": os.path.getmtime(subdir_path),
                            "platform": "qq",
                            "source_dir": subdir_path,
                        })

    return results

def count_files(directory: str, recursive: bool = True) -> int:
    """Count files in a directory (optionally recursive)."""
    count = 0
    try:
        if recursive:
            for root, dirs, files in os.walk(directory):
                count += len(files)
                if count > 10000:  # cap to avoid excessive scanning
                    return count
        else:
            count = len([f for f in os.listdir(directory)
                        if os.path.isfile(os.path.join(directory, f))])
    except (PermissionError, OSError):
        pass
    return count

COURSE_KEYWORDS = [
    # 通用课程资料
    "课件", "ppt", "slide", "讲义", "笔记", "note", "阅读", "reading",
    "复习", "考试", "期末", "重点", "考纲", "大纲", "往年", "真题",
    "课程", "lecture", "tutorial", "handout", "material", "作业", "quiz",
    # 法学相关（仍支持）
    "法", "律", "诉", "权", "刑", "民", "商", "宪",
    "合同", "侵权", "犯罪", "证据", "判决", "案例",
    "law", "legal", "court", "justice", "civil", "criminal",
    "contract", "tort", "constitution", "procedure", "evidence",
]

DOCUMENT_EXTENSIONS = {
    ".docx", ".pdf", ".txt", ".md", ".pptx", ".json",
    ".doc", ".xmind", ".html", ".epub", ".png", ".jpg", ".jpeg",
}

EXCLUDE_PATTERNS = ["安装", "setup", "license", "readme", "~$"]

def scan_directory(directory: str, max_files: int = 50, days: int = 90) -> list:
    """Scan a directory for course-related document files."""
    results = []
    cutoff_time = datetime.now() - timedelta(days=days)
    directory = expand_path(directory)

    if not os.path.isdir(directory):
        return results

    try:
        for root, dirs, files in os.walk(directory):
            # Skip hidden/system directories
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]

            for filename in files:
                if len(results) >= max_files:
                    break

                filepath = os.path.join(root, filename)
                ext = os.path.splitext(filename)[1].lower()

                # File type filter
                if ext not in DOCUMENT_EXTENSIONS:
                    continue

                # Size filter
                try:
                    size = os.path.getsize(filepath)
                    if size < 1024:  # skip < 1KB
                        continue
                    if size > 100 * 1024 * 1024:  # skip > 100MB
                        continue
                except OSError:
                    continue

                # Exclude patterns
                name_lower = filename.lower()
                if any(p in name_lower for p in EXCLUDE_PATTERNS):
                    continue
                if filename.startswith("~$"):
                    continue
                if ext in (".tmp", ".crdownload"):
                    continue

                # Course keyword relevance (lightweight filename check)
                relevance = sum(1 for kw in COURSE_KEYWORDS if kw.lower() in name_lower)
                # Also check parent dir names for context
                parent_dirs = root.replace(directory, "").lower()
                relevance += sum(1 for kw in COURSE_KEYWORDS if kw.lower() in parent_dirs)

                # Modified time
                try:
                    mtime = os.path.getmtime(filepath)
                    mtime_dt = datetime.fromtimestamp(mtime)
                except OSError:
                    mtime = 0
                    mtime_dt = datetime.min

                results.append({
                    "path": os.path.abspath(filepath),
                    "filename": filename,
                    "size_bytes": size,
                    "extension": ext,
                    "mtime": mtime,
                    "mtime_iso": mtime_dt.isoformat(),
                    "relevance_score": relevance,
                    "source_dir": root,
                })

            if len(results) >= max_files:
                break

    except (PermissionError, OSError):
        pass

    # Sort by relevance (desc), then mtime (desc)
    results.sort(key=lambda x: (-x["relevance_score"], -x["mtime"]))
    return results[:max_files]

def scan_generic(config: dict, max_files: int = 50) -> list:
    """Scan all common download locations."""
    plat_key = get_platform_key()
    fallback_paths = config.get("generic_fallback", {}).get(plat_key, [])
    all_results = []

    for path_str in fallback_paths:
        path = expand_path(path_str)
        if os.path.isdir(path):
            results = scan_directory(path, max_files=max_files)
            all_results.extend(results)
            if len(all_results) >= max_files:
                break

    # Deduplicate by file path
    seen = set()
    unique = []
    for r in all_results:
        if r["path"] not in seen:
            seen.add(r["path"])
            unique.append(r)
    return unique[:max_files]

def main():
    parser = argparse.ArgumentParser(description="Find course-related files from WeChat/QQ/common locations")
    parser.add_argument("--platform", choices=["wechat", "qq"], help="Platform to search")
    parser.add_argument("--scan", type=str, help="Scan a specific directory")
    parser.add_argument("--scan-all", action="store_true", help="Scan all common download locations")
    parser.add_argument("--list-platforms", action="store_true", help="List supported platforms and paths")
    parser.add_argument("--max-files", type=int, default=50, help="Max files to return")
    parser.add_argument("--output", type=str, help="Output JSON file path (default: stdout)")
    args = parser.parse_args()

    config = load_config()

    if args.list_platforms:
        print(json.dumps(config, indent=2, ensure_ascii=False))
        return

    results = []

    if args.platform == "wechat":
        results = find_wechat_dirs(config)
        if not results:
            # Fallback to scanning Downloads
            plat_key = get_platform_key()
            fallback = config.get("generic_fallback", {}).get(plat_key, [])[:1]
            for fb in fallback:
                fb_path = expand_path(fb)
                if os.path.isdir(fb_path):
                    results.append({
                        "path": fb_path,
                        "type": "fallback_no_wechat_found",
                        "file_count": count_files(fb_path),
                        "platform": "wechat",
                        "source_dir": fb_path,
                        "note": "WeChat directories not found. Showing generic Downloads instead.",
                    })
                    break

    elif args.platform == "qq":
        results = find_qq_dirs(config)
        if not results:
            plat_key = get_platform_key()
            fallback = config.get("generic_fallback", {}).get(plat_key, [])[:1]
            for fb in fallback:
                fb_path = expand_path(fb)
                if os.path.isdir(fb_path):
                    results.append({
                        "path": fb_path,
                        "type": "fallback_no_qq_found",
                        "file_count": count_files(fb_path),
                        "platform": "qq",
                        "source_dir": fb_path,
                        "note": "QQ directories not found. Showing generic Downloads instead.",
                    })
                    break

    elif args.scan:
        file_results = scan_directory(args.scan, max_files=args.max_files)
        # Group by source directory
        from collections import defaultdict
        grouped = defaultdict(list)
        for fr in file_results:
            grouped[fr["source_dir"]].append(fr)
        for src_dir, files in grouped.items():
            results.append({
                "path": src_dir,
                "type": "custom_scan",
                "file_count": len(files),
                "files": files,
                "platform": "custom",
                "source_dir": src_dir,
            })

    elif args.scan_all:
        file_results = scan_generic(config, max_files=args.max_files)
        from collections import defaultdict
        grouped = defaultdict(list)
        for fr in file_results:
            grouped[fr["source_dir"]].append(fr)
        for src_dir, files in grouped.items():
            results.append({
                "path": src_dir,
                "type": "generic_scan",
                "file_count": len(files),
                "files": files,
                "platform": "generic",
                "source_dir": src_dir,
            })

    else:
        parser.print_help()
        sys.exit(1)

    output = json.dumps(results, indent=2, ensure_ascii=False, default=str)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output)

if __name__ == "__main__":
    main()
