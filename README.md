# law-import

**法学资料导入器** — 从微信/QQ/任意目录自动发现法学资料，智能分类，一键生成结构化复习项目。

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)

## 一句话说明

把微信/QQ里乱七八糟下载的法学资料（课件、笔记、往年题、案例、法条...），自动整理成按课程分类、可直接生成复习材料的项目目录。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 可选：安装 OCR 引擎（用于扫描件/图片）
pip install easyocr          # 推荐：GPU加速，中英混合识别
# 或
pip install pytesseract      # 轻量，需额外安装 Tesseract 引擎

# 3. 在 Claude Code 中使用
# 将 law-import/ 文件夹复制到 ~/.claude/skills/
# 然后说："/law-import"

# 4. 纯命令行模式（不需要 Claude Code）
python tools/file_finder.py --platform wechat          # 发现微信下载的法学文件
python tools/format_converter.py -i 笔记.docx -m docx2md  # 转换格式
python tools/classifier.py -i 笔记.md -m full          # 分类文件
python tools/output_writer.py -i ./法学/ -f all         # 生成输出
```

## 它能做什么

```
微信/QQ下载区 → 自动发现 → 多模态提取 → 资料类型分类 → 用户命名课程 → 去重 → 生成项目 → 多格式输出
    │               │           │              │              │        │        │         │
  手动下载       file_finder  OCR/PDF提取   教材?笔记?     "民法总论"   相似度   目录结构   MD/HTML
  指定路径       .py          格式转换      重点?案例?     用户说了算   检测     MOC      /PDF/DOCX
  不知道在哪                   图片OCR       往年题?                                      ✅
                              扫描PDF       考纲?                                        上下文分段
                              .docx/.pptx   法条?
```

### 核心特色

| 能力 | 说明 |
|------|------|
| **多模态归一化** | DOCX/PDF/PPTX/EPUB/HTML/图片/扫描件 → 统一 Markdown |
| **10种资料类型** | 教材/笔记/重点/往年题/案例/术语表/阅读材料/论文/考纲/法条 — 按优先级链逐维检视 |
| **课程用户命名** | 不替用户做学科归类。关键词智能建议，用户一句话决定课程名（适配任意学校课程表）|
| **上下文分段** | 大文件自动按章节边界分段处理，200字符重叠防断裂 |
| **多格式输出** | MD（Obsidian兼容）/ HTML / PDF / DOCX 一键生成 |
| **安全只读** | 绝不移动/删除/修改原始文件，导入=复制+转换 |
| **确认门禁** | 文件选择 + 分类结果 两次用户确认，写入前充分把关 |

## 架构

```
law-import/
├── SKILL.md                    # Claude Code Skill 完整工作流定义
├── README.md                   # 本文件
├── requirements.txt            # Python 依赖
├── tools/
│   ├── file_finder.py          # 跨平台微信/QQ文件发现
│   ├── ocr_tool.py             # OCR引擎（EasyOCR/Tesseract自动降级）
│   ├── format_converter.py     # 多格式→统一Markdown
│   ├── classifier.py           # 资料类型分类+关键词建议
│   ├── chunk_manager.py        # 大文件上下文窗口分段+合并
│   └── output_writer.py        # MD/HTML/PDF/DOCX多格式输出
├── config/
│   ├── material_types.json     # 10种资料类型检测规则+权重
│   ├── subject_keywords.json   # 关键词建议词典（仅供参考，用户命名优先）
│   └── platform_paths.json     # 微信/QQ跨平台路径定义
├── templates/
│   └── html_template.html      # HTML输出模板
└── examples/
    └── demo_usage.md           # 使用演示
```

## 支持的平台

| 平台 | 微信 | QQ | 通用扫描 |
|------|------|-----|---------|
| Windows 10/11 | ✅ | ✅ | ✅ |
| macOS | ✅ | ✅ | ✅ |
| Linux | ✅ | ✅ | ✅ |

## 支持的文件格式

| 格式 | 提取方式 | OCR |
|------|---------|-----|
| `.docx` | python-docx | — |
| `.pptx` | python-pptx | — |
| `.pdf` (文本) | PyPDF2 | — |
| `.pdf` (扫描) | pdf2image + OCR | ✅ |
| `.epub` | ebooklib + BeautifulSoup | — |
| `.html` | markdownify | — |
| `.txt` | 自动编码检测 | — |
| `.json` (幕布) | 递归节点树解析 | — |
| `.png/.jpg` | EasyOCR / Tesseract | ✅ |

## 资料类型检测链

按优先级逐维检视，每个维度独立给分：

1. **考纲/大纲** — 课程目标+学时+考核方式 → 最高优先级
2. **重点/考点** — 【★重点】【必考】【历年真题】标记
3. **往年试题** — Q&A结构+题型+分值标注
4. **法条/法规** — 条-款-项编号+施行日期
5. **案例材料** — 原告/被告/法院认为+案号
6. **教材 vs 笔记** — 标题规整度+学术用语 vs 非正式编号+口语化
7. **术语表** — 术语-定义对结构
8. **学术论文** — 摘要+关键词+IMRaD
9. **阅读材料** — 参考文献列表
10. **默认回退** — 通用参考资料

## 目录结构

导入后自动生成：

```
法学/
├── 民法总论/              ← 用户命名的课程
│   ├── 笔记/
│   ├── 重点与考纲/
│   ├── 试题/
│   ├── 案例/
│   ├── 法条/
│   ├── 术语/
│   ├── 文献/
│   ├── _原始文件/
│   └── 民法总论概述.md
├── 刑法分论/
│   └── ... (同上)
├── _跨课程/               ← 多课程共享资源
├── _原始文件/
└── 法学总览.md
```

## 与 law-review-generator 衔接

导入完成后可以直接触发复习材料生成：

```
law-import 完成 → "触发复习生成"
  ├─ 考纲文件 → topic_map.json 骨架
  ├─ 重点文件 → 【★重点】考点补充
  ├─ 往年题 → 高频考点统计
  └─ law-review-generator 输出逐章复习稿
```

## 开源协议

MIT — 自由使用、修改、分发。

## 贡献

欢迎 PR 到 `config/platform_paths.json`（新增微信/QQ 新版本路径）和 `config/subject_keywords.json`（新增学校/专业关键词）。