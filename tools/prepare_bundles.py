#!/usr/bin/env python3
"""Prepare comprehensive chapter source bundles for Phase 7.3."""
import re, json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'D:\环资法\环境资源法复习')
OUT_DIR = BASE / '源材料_分章' / 'chapter_bundles'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Read all source files
note1 = (BASE / '笔记' / '笔记_环境资源法.md').read_text('utf-8')
note2 = (BASE / '笔记' / '笔记0620.md').read_text('utf-8')
syllabus = (BASE / '重点与考纲' / '教学周历.md').read_text('utf-8')
past_exam = (BASE / '试题' / '往年题_环资2024春试题_docx.md').read_text('utf-8')
past_exam2 = (BASE / '试题' / '往年题_第21_23题参考答案和说明_docx.md').read_text('utf-8')

# Readings text dir
readings_dir = BASE / '文献'

# Syllabus mapping (from chapter_reading_map.json)
with open(str(BASE / 'chapter_reading_map.json'), 'r', encoding='utf-8') as f:
    reading_map = json.load(f)

# Pre-read all readings
all_readings = {}
for rf in readings_dir.glob('*.txt'):
    all_readings[rf.name] = rf.read_text('utf-8')

# Chapter definitions
chapters = [
    {'key': 'ch01', 'title': '第一章 环境法的形成', 'h2': '第一章  环境法的形成', 'weight': '重点', 'min_lines': 1500},
    {'key': 'ch02', 'title': '第二章 中国环境法的体系', 'h2': '第二章  中国环境法的体系', 'weight': '重点', 'min_lines': 1500},
    {'key': 'ch03', 'title': '第三章 (风险)预防原则', 'h2': '第三章 （风险）预防原则', 'weight': '重点', 'min_lines': 1500},
    {'key': 'ch04', 'title': '第四章 生物技术研究、开发与应用安全', 'h2': '第四章 生物技术研究', 'weight': '了解', 'min_lines': 500},
    {'key': 'ch05', 'title': '第五章 污染者负担原则', 'h2': '第五章 污染者负担原则', 'weight': '重点', 'min_lines': 1500},
    {'key': 'ch06', 'title': '第六章 环境合作原则', 'h2': '第六章 环境合作原则', 'weight': '重点', 'min_lines': 500},
    {'key': 'ch07', 'title': '第七章 环境规制的手段：命令与控制', 'h2': '第七章 环境规制的手段', 'weight': '必考', 'min_lines': 3000},
    {'key': 'ch08', 'title': '第八章 环境权的法理与实证', 'h2': '第八章  环境权的法理与实证', 'weight': '必考', 'min_lines': 3000},
    {'key': 'ch09', 'title': '第九章 生态环境损害赔偿制度', 'h2': '第九章  生态环境损害赔偿制度', 'weight': '必考', 'min_lines': 3000},
    {'key': 'ch10', 'title': '第十章 社会组织环境公益诉讼制度', 'h2': '第十章  社会组织环境公益诉讼制度', 'weight': '重点', 'min_lines': 1500},
    {'key': 'ch11', 'title': '第十一章 检察环境公益诉讼制度', 'h2': '第十一章 检察环境公益诉讼制度', 'weight': '重点', 'min_lines': 1500},
]

def extract_section_note(text, heading):
    """Extract a chapter section from a note file."""
    lines = text.split('\n')
    result = []
    in_section = False
    heading_pattern = None

    # Find the heading
    for i, line in enumerate(lines):
        if re.search(re.escape(heading), line) and re.match(r'^#{1,3}\s', line):
            heading_pattern = re.escape(heading)
            in_section = True
            result.append(line)
            break

    if not in_section:
        # Try more flexible matching
        for i, line in enumerate(lines):
            words = heading.split()[:2]
            if all(w in line for w in words) and re.match(r'^#{1,3}\s', line):
                in_section = True
                result.append(line)
                break

    if not in_section:
        return "[未在笔记中找到此章节]\n"

    # Continue until next chapter heading at same or higher level
    for j in range(i+1, len(lines)):
        line = lines[j]
        if re.match(r'^#{1,2}\s', line) and not re.search(heading_pattern, line):
            # Check if this is a new chapter (not a subsection of current)
            h_level = len(line) - len(line.lstrip('#'))
            if h_level <= 2:
                break
        result.append(line)

    return '\n'.join(result)

# Also extract from new_note_analysis
new_note_dir = BASE / '_原始文件' / 'new_note_analysis' / 'chapters'

for ch in chapters:
    bundle = []
    bundle.append(f'# {ch["title"]}')
    bundle.append(f'考点权重：{ch["weight"]}  |  密度目标：≥{ch["min_lines"]}行\n')

    # 1. From note1 (main)
    section = extract_section_note(note1, ch['h2'])
    bundle.append(f'## === 源材料A：笔记（主）===\n{section}\n')

    # 2. From note2
    section2 = extract_section_note(note2, ch['h2'])
    bundle.append(f'## === 源材料B：笔记0620 ===\n{section2}\n')

    # 3. Existing chapter file
    ch_files = sorted((BASE / '源材料_分章').glob(f'{ch["key"].replace("ch","ch")}*.md'))
    if ch_files:
        cf = ch_files[0].read_text('utf-8')
        bundle.append(f'## === 源材料C：已有章节提取（{ch_files[0].name}）===\n{cf}\n')

    # 4. New note analysis
    for nf in sorted(new_note_dir.glob(f'*{ch["key"]}*')):
        bundle.append(f'## === 源材料D：新笔记分析（{nf.name}）===\n{nf.read_text("utf-8")}\n')

    # 5. Readings per map
    for map_key, map_val in reading_map.items():
        if ch['key'] in map_key or ch['title'][:4] in map_val.get('chapter_title', ''):
            for reading_path in map_val.get('readings', []):
                reading_name = Path(reading_path).name
                if reading_name in all_readings:
                    bundle.append(f'## === 阅读文献：{reading_name.replace(".txt","")} ===\n{all_readings[reading_name]}\n')
            break

    out_file = OUT_DIR / f'{ch["key"]}_source_bundle.md'
    out_file.write_text('\n'.join(bundle), 'utf-8')
    lines = len('\n'.join(bundle).splitlines())
    print(f'{ch["key"]} {ch["title"]}: {lines}行')

# Also save a common reference file with syllabus and past exams
common = []
common.append('# 公共参考材料\n')
common.append(f'## 教学周历\n{syllabus}\n')
common.append(f'## 往年试题（2024春）\n{past_exam}\n')
common.append(f'## 往年试题参考答案\n{past_exam2}\n')
(OUT_DIR / '_common_reference.md').write_text('\n'.join(common), 'utf-8')
print(f'\n公共参考材料: {len("\n".join(common).splitlines())}行')
print('Done!')
