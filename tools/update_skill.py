#!/usr/bin/env python3
"""Update SKILL.md with new density targets and formatting requirements."""
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

SKILL = str(Path.home() / '.claude' / 'skills' / 'final-review' / 'SKILL.md')

with open(SKILL, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update density section
old_density = '## 密度标准（不可协商）\n\t│  │  │  │  │  - 【必考】章节总输出 ≥ 3000 行（约 60 页 A4，底线非目标）\n\t│  │  │  │  │  - 【★重点】章节总输出 ≥ 1500 行（约 30 页 A4，底线非目标）\n\t│  │  │  │  │  - 【了解】章节总输出 ≥ 500 行（约 10 页 A4，底线非目标）\n\t│  │  │  │  │  这些是**底线**，不是目标。源材料充足时应该远超。'

new_density = (
    '## 总量约束（硬性上限）\n'
    '\t│  │  │  │  │  **整份材料目标：6-8万字（中文字数）**。\n'
    '\t│  │  │  │  │  你这一章的定额如下：\n'
    '\t│  │  │  │  │  | 权重 | 中文字目标 | 约合行数 |\n'
    '\t│  │  │  │  │  |------|:----------:|:--------:|\n'
    '\t│  │  │  │  │  | 必考 | 8000-10000 | 250-350 |\n'
    '\t│  │  │  │  │  | 重点 | 5000-7000  | 150-200 |\n'
    '\t│  │  │  │  │  | 了解 | 2000-3000  | 60-100  |\n'
    '\t│  │  │  │  │  超出上限意味其他章被压缩。'
)

if old_density in content:
    content = content.replace(old_density, new_density)
    print('1. Density section updated')
else:
    print('1. FAILED: density section not found')

# 2. Update output spec
old_output = '① 四段式结构（每个考点）\n\t│  │  │  │  │  2. 结构化图表 ≥ 2 个（概念对比表/步骤图/层级图）\n\t│  │  │  │  │  3. 完整法学标准——逐要素展开，不缩写\n\t│  │  │  │  │  4. 案例六段式完整嵌入\n\t│  │  │  │  │  5. 语言模式：[1] 中文主体 + 考试关键英文标注\n\t│  │  │  │  │  6. 末尾必须包含 ## 📋 本章考点速记 表格'

new_output = (
    '1. 整理结构：定义->构成要件->法律后果->评价 四段式\n'
    '\t│  │  │  │  │  2. 表格格式——使用干净管道表格，:---:对齐：\n'
    '\t│  │  │  │  │     | 概念 | 构成要件 | 法律效果 |\n'
    '\t│  │  │  │  │     |:----|:--------|:--------|\n'
    '\t│  │  │  │  │     | XX  | A+B+C   | YY      |\n'
    '\t│  │  │  │  │  3. 对比/分类表>=1个，替代流程图/层级图\n'
    '\t│  │  │  │  │  4. 案例1段话：案名->要点->结论（极重要用2段）\n'
    '\t│  │  │  │  │  5. 语言模式：纯中文，重要概念首次标注英文\n'
    '\t│  │  │  │  │  6. 末尾 ## 考点速记，2列（考点|考查方式），<=15行\n'
    '\t│  │  │  │  │  7. 禁止废话（综上所述/由此可见等）\n'
    '\t│  │  │  │  │  8. 禁止每个考点前加序号（一、二、三）'
)

if old_output in content:
    content = content.replace(old_output, new_output)
    print('2. Output spec updated')
else:
    print('2. FAILED: output spec not found')

# 3. Update Review Agent
old_review = '全稿总行数 ≥ 14000（约 280 页 A4，硬性底线）\n\t│  │  │  网每章密度达标（必考 ≥3000 / ★重点 ≥1500 / 了解 ≥500）'
new_review = '全稿总字数 6-8万字（中文字数，硬性上限与下限）\n\t│  │  │  网每章字数达标（必考 8000-10000 / 重点 5000-7000 / 了解 2000-3000）'
if old_review in content:
    content = content.replace(old_review, new_review)
    print('3. Review agent updated')
else:
    print('3. FAILED: review agent not found')

# 4. Update exit gate
old_exit = '全稿 ≥ 14000 行? 必考章均 ≥ 3000? ★重点章均 ≥ 1500?'
new_exit = '全稿 6-8万字? 必考章均 8000-10000字? 重点章均 5000-7000字?'
if old_exit in content:
    content = content.replace(old_exit, new_exit)
    print('4. Exit gate updated')
else:
    print('4. FAILED: exit gate not found')

# 5. Update must retain section
old_retain = '### 必须保留\n\t│  │  │  │  │  - 概念的定义、构成要件、法律后果（规范结构）\n\t│  │  │  │  │  - 论证逻辑——为什么这个规则是这样（不只是结论）\n\t│  │  │  │  │  - 原文精华——笔记中论证衔接度高的段落直接保留原文\n\t│  │  │  │  │  - 比较法的差异及其原因\n\t│  │  │  │  │  - 学术争议——不同观点 + 各方理由\n\t│  │  │  │  │  - 老师强调的观点/立场\n\t│  │  │  │  │  - 法学标准/测试的每一个要素展开说明（不是列名字）\n\t│  │  │  │  │  - 案例完整六段式\n\t│  │  │  │  │  - 课程管理信息（考试时间/形式/成绩构成）'

new_retain = (
    '### 必须保留（精简版）\n'
    '\t│  │  │  │  │  - 概念的定义、构成要件、法律后果——每考点1-3段\n'
    '\t│  │  │  │  │  - 核心论证逻辑（一句话点明，不堆砌背景）\n'
    '\t│  │  │  │  │  - 比较法差异——用对比表格呈现，不逐国叙述\n'
    '\t│  │  │  │  │  - 学术争议——双方各1句核心论点，不铺陈论据链\n'
    '\t│  │  │  │  │  - 老师明确强调的观点/立场\n'
    '\t│  │  │  │  │  - 法学标准要素——用表格/清单列出+简短说明\n'
    '\t│  │  │  │  │  - 案例——每个1-2段（不必六段式，除非极重要）\n'
    '\t│  │  │  │  │  - 往年真题关联——标注哪些考点考过'
)
if old_retain in content:
    content = content.replace(old_retain, new_retain)
    print('5. Retain section updated')
else:
    print('5. FAILED: retain section not found')

# 6. Update filter section
old_filter = '### 必须过滤（噪音）\n\t│  │  │  │  │  - 长法条 → 仅保留“构成要件+法律后果”规范结构\n\t│  │  │  │  │  - 同一观点反复表述 → 保留最清晰版本，删重复\n\t│  │  │  │  │  - 与复习无关的冗长描述 → 删除'

new_filter = (
    '### 必须删除\n'
    '\t│  │  │  │  │  - 长法条原文 → 仅保留“构成要件+法律效果”\n'
    '\t│  │  │  │  │  - 同一观点反复表述 → 保留最精炼版本\n'
    '\t│  │  │  │  │  - 冗余过渡句（“首先”“如上所述”等）\n'
    '\t│  │  │  │  │  - 背景知识拓展、课堂逸事、个人经历\n'
    '\t│  │  │  │  │  - 每个考点前面的长篇引言\n'
    '\t│  │  │  │  │  - 大段论文原文引用 → 改为1-2句概括核心结论'
)
if old_filter in content:
    content = content.replace(old_filter, new_filter)
    print('6. Filter section updated')
else:
    print('6. FAILED: filter section not found')

with open(SKILL, 'w', encoding='utf-8') as f:
    f.write(content)
print('\nDone!')
