#!/usr/bin/env python3
"""
Material type classifier + subject keyword suggester for 期末一键复习（Final Review）.

Usage:
    python classifier.py --input text.md --mode material_type
    python classifier.py --input text.md --mode subject_suggest
    python classifier.py --input text.md --mode full
    python classifier.py --input text.md --mode quality

Output: JSON with classification results, confidence scores, and quality flags.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from collections import Counter

# Load configs
CONFIG_DIR = Path(__file__).parent.parent / "config"

def load_json(filename: str) -> dict:
    with open(CONFIG_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)

def classify_material_type(text: str, filename: str = "") -> dict:
    """
    Classify a document into one of 10 material types.
    Returns {type, confidence, evidence, special_markers}.
    Uses the step-by-step priority chain from SKILL.md Phase 2.
    """
    config = load_json("material_types.json")
    types = config["types"]
    thresholds = config["type_detection_thresholds"]
    special_markers = config["special_markers"]

    scores = {}
    evidence = {}
    filename_lower = filename.lower()
    text_lower = text.lower()

    for type_key, type_def in types.items():
        score = 0
        hits = []

        # Check filename patterns
        for pat in type_def["detection"]["filename_patterns"]:
            if re.search(pat, filename_lower):
                score += 2  # filename matches are strong signals
                hits.append(f"filename:{pat}")

        # Check content patterns
        for pat in type_def["detection"]["content_patterns"]:
            matches = re.findall(pat, text)
            if matches:
                score += min(len(matches), 5)  # cap at 5 per pattern
                hits.append(f"content:{pat}")

        # Apply weight
        weight = type_def["detection"]["weight"]
        weighted_score = score * weight / 10.0

        scores[type_key] = {
            "raw_score": score,
            "weighted_score": round(weighted_score, 2),
            "type_name": type_def["name_zh"],
            "hits": hits[:10],  # top 10 hits
        }

    # Sort by weighted score
    ranked = sorted(scores.items(), key=lambda x: -x[1]["weighted_score"])
    top = ranked[0]
    second = ranked[1] if len(ranked) > 1 else (None, None)

    # Determine confidence
    top_score = top[1]["weighted_score"]
    second_score = second[1]["weighted_score"] if second else 0
    gap = top_score - second_score

    if top_score >= thresholds["high_confidence"] and gap >= 2:
        confidence = "high"
    elif top_score >= thresholds["medium_confidence"]:
        confidence = "medium"
    elif top_score >= thresholds["low_confidence"]:
        confidence = "low"
    else:
        confidence = "none"

    # Extract special markers (★重点, 必考, etc.)
    found_markers = {
        "exam_critical": [],
        "exam_excluded": [],
        "quality_flags": [],
    }
    for marker in special_markers["exam_critical"]:
        if marker in text:
            found_markers["exam_critical"].append(marker)
    for marker in special_markers["exam_excluded"]:
        if marker in text:
            found_markers["exam_excluded"].append(marker)
    for marker in special_markers["quality_flags"]:
        if marker in text:
            found_markers["quality_flags"].append(marker)

    result = {
        "primary_type": top[0],
        "primary_name": top[1]["type_name"],
        "confidence": confidence,
        "top_candidates": [
            {"type": k, "name": v["type_name"], "score": v["weighted_score"]}
            for k, v in ranked[:3]
        ],
        "evidence": top[1]["hits"],
        "special_markers": found_markers,
        "suggested_pipeline": types[top[0]]["output_pipeline"],
        "review_relevance": types[top[0]]["review_relevance"],
        "all_scores": {k: v["weighted_score"] for k, v in ranked},
    }

    return result

def suggest_subjects(text: str, filename: str = "") -> dict:
    """
    Suggest subjects based on keyword matching.
    This is SUGGESTION ONLY — the user decides the actual course name.
    """
    config = load_json("subject_keywords.json")
    subjects = config["subjects"]
    thresholds = config["confidence_thresholds"]

    scores = {}
    evidence = {}

    text_lower = text.lower()
    filename_lower = filename.lower()

    for subj_key, subj_def in subjects.items():
        zh_score = 0
        en_score = 0
        zh_hits = []
        en_hits = []

        for kw in subj_def["keywords_zh"]:
            count = len(re.findall(re.escape(kw), text))
            if count > 0:
                zh_score += min(count, 3) * 1.0  # Chinese keyword weight = 1.0
                zh_hits.append(kw)
            # Also check filename
            if kw in filename_lower:
                zh_score += 2.0
                zh_hits.append(f"filename:{kw}")

        for kw in subj_def["keywords_en"]:
            count = len(re.findall(re.escape(kw), text_lower))
            if count > 0:
                en_score += min(count, 3) * 0.8  # English keyword weight = 0.8
                en_hits.append(kw)
            if kw in filename_lower:
                en_score += 1.6
                en_hits.append(f"filename:{kw}")

        total_score = zh_score + en_score
        scores[subj_key] = {
            "total_score": round(total_score, 2),
            "zh_score": zh_score,
            "en_score": en_score,
            "subject_name": subj_def["name_zh"],
            "zh_hits": zh_hits[:10],
            "en_hits": en_hits[:10],
        }

    ranked = sorted(scores.items(), key=lambda x: -x[1]["total_score"])
    top = ranked[0]
    second = ranked[1] if len(ranked) > 1 else (None, None)
    top_score = top[1]["total_score"]
    second_score = second[1]["total_score"] if second else 0
    gap = top_score - second_score

    # Determine suggestion strength
    if top_score >= thresholds["high"]["min_hits"] and gap >= thresholds["high"]["min_gap"]:
        strength = "strong"
        suggestion_text = f"💡 看起来这些内容跟 **{top[1]['subject_name']}** 比较相关"
    elif top_score >= thresholds["medium"]["min_hits"] and gap >= thresholds["medium"]["min_gap"]:
        strength = "moderate"
        suggestion_text = f"💡 可能跟 **{top[1]['subject_name']}** 有关（但不确定）"
    elif top_score >= thresholds["low"]["min_hits"]:
        strength = "weak"
        candidates = [f"**{v['subject_name']}**" for k, v in ranked[:3] if v["total_score"] >= 2]
        suggestion_text = f"💡 可能的方向：{' / '.join(candidates)}" if candidates else ""
    else:
        strength = "none"
        suggestion_text = ""

    # Check for cross-discipline conflicts
    conflicts = []
    conflict_pairs = config.get("cross_discipline_conflicts", {}).get("pairs", [])
    for pair in conflict_pairs:
        if pair[0] in scores and pair[1] in scores:
            s1 = scores[pair[0]]["total_score"]
            s2 = scores[pair[1]]["total_score"]
            if abs(s1 - s2) <= 3 and s1 >= 2:
                conflicts.append({
                    "pair": [pair[0], pair[1]],
                    "names": [subjects[pair[0]]["name_zh"], subjects[pair[1]]["name_zh"]],
                    "score_diff": round(abs(s1 - s2), 1),
                })

    return {
        "top_suggestion": top[0],
        "suggestion_name": top[1]["subject_name"],
        "suggestion_text": suggestion_text,
        "strength": strength,
        "candidates": [
            {"subject": k, "name": v["subject_name"], "score": v["total_score"], "hits": v["zh_hits"] + v["en_hits"]}
            for k, v in ranked[:5] if v["total_score"] >= 1
        ],
        "conflicts": conflicts,
        "_note": "This is a SUGGESTION only. The user should name their own course. See SKILL.md Phase 3.1.",
    }

def assess_quality(text: str) -> dict:
    """Assess content quality and flag issues."""
    flags = []

    # Check for missing chapters (table of contents mentions chapters not in body)
    toc_chapters = re.findall(r'第[一二三四五六七八九十\d]+章', text[:3000])
    body_chapters = re.findall(r'第[一二三四五六七八九十\d]+章', text[3000:])
    if toc_chapters and body_chapters:
        missing = set(toc_chapters) - set(body_chapters)
        if missing:
            flags.append({"type": "missing_chapters", "detail": f"目录提及但正文缺失: {', '.join(sorted(missing))}"})

    # Check for dangling references
    if re.search(r'同上|见前|前述|如前所述', text) and len(text) < 500:
        flags.append({"type": "dangling_reference", "detail": "含'同上/见前'引用但文本较短，可能缺上下文"})

    if re.search(r'见附件|详见附件|附件\d|见附图', text):
        if "附件" not in text[100:]:
            flags.append({"type": "missing_attachment", "detail": "引用了附件但正文中未找到附件内容"})

    # Check heading number continuity
    heading_nums = re.findall(r'^#{1,3}\s*(\d+)', text, re.MULTILINE)
    if len(heading_nums) >= 3:
        nums = [int(n) for n in heading_nums]
        if max(nums) - min(nums) > len(nums) * 2:
            flags.append({"type": "numbering_gap", "detail": "标题编号可能存在跳跃"})

    # Source reliability
    reliability = "unknown"
    if re.search(r'教材|课本|textbook|官方|正式', text[:500]):
        reliability = "high"
    elif re.search(r'笔记|整理|随堂|上课|回忆', text[:500]):
        reliability = "medium"

    return {
        "quality_flags": flags,
        "reliability": reliability,
        "has_toc": bool(re.search(r'目\s*录|Table of Contents|CONTENTS', text[:1000])),
        "estimated_completeness": "完整" if len(flags) == 0 else "有缺失",
    }

def main():
    parser = argparse.ArgumentParser(description="Law material classifier")
    parser.add_argument("--input", "-i", required=True, help="Input text/Markdown file")
    parser.add_argument("--mode", "-m", choices=["material_type", "subject_suggest", "full", "quality"],
                        default="full", help="Classification mode")
    parser.add_argument("--filename", help="Original filename (for file-name-based matching)")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    args = parser.parse_args()

    filepath = args.input
    if not os.path.isfile(filepath):
        print(f"ERROR: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    filename = args.filename or Path(filepath).name

    result = {}
    if args.mode in ("material_type", "full"):
        result["material_type"] = classify_material_type(text, filename)
    if args.mode in ("subject_suggest", "full"):
        result["subject_suggestion"] = suggest_subjects(text, filename)
    if args.mode in ("quality", "full"):
        result["quality"] = assess_quality(text)

    output = json.dumps(result, indent=2, ensure_ascii=False, default=str)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Classification results written to {args.output}", file=sys.stderr)
    else:
        print(output)

if __name__ == "__main__":
    main()
