# 法学期末复习笔记高效整理

**微信/QQ下载 → 自动整理 → 逐章复习稿PDF，一条管线走到底。**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)

## 一句话说明

把微信/QQ里乱七八糟下载的法学资料（课件、笔记、往年题、案例...），自动整理成按课程分类的项目目录，**并直接生成逐章复习稿 PDF**。

## 快速开始

**没有 Python 也能用。** 约 70% 的功能零依赖直接跑（Claude 原生能力）。只有读取 Word/PDF/PPT/图片时需要 Python。

```bash
# 零依赖起步（Tier 0）——什么也不用装，直接说 "/law-import"
# 文本文件 (.md .txt .html) 全支持，分类/整理/复习生成都能做

# 完整能力（Tier 1+2）——5 分钟装好
python setup.py                  # 检测环境 + 显示能力层级
pip install -r requirements.txt  # 核心依赖（Word/PDF/PPT提取）
pip install easyocr              # OCR 可选（扫描件/图片）
python install.py                # 部署到你的 AI agent
python tools/output_writer.py -i ./法学/ -f all         # 生成输出
```

## 它能做什么

```
微信/QQ下载 → 自动发现 → 视觉/OCR → 类型分类 → 课程命名 → 去重 → 章节整合 → 复习生成 → PDF输出
    │            │           │            │            │        │        │         │
  手动下载    file_finder  模型视觉优先  教材?笔记?    "民法总论"  相似度   教材+笔记  考纲→考点
  指定路径    .py          OCR降级      重点?案例?    用户说了算  检测     阅读材料   逐章四段式
  不知道在哪               零依赖不跳过   往年题?                           案例归属   考点速记
                                         考纲?                                      结构化内容
```

### 核心特色

| 能力 | 说明 |
|------|------|
| **多模态归一化** | 模型视觉优先 → OCR降级。DOCX/PDF/PPTX/EPUB/HTML/图片/扫描件 → 统一 Markdown |
| **8种资料类型** | 教材/笔记/重点/往年题/案例/术语表/阅读材料/论文/考纲 — 按优先级链逐维检视（法条已移除：笔记中自然包含）|
| **章节级整合** | 教材+笔记+阅读材料按章节拆分、比对、整合。结构化输出：概念对比表/步骤图/思维模板 |
| **双语智能标注** | 四种语言模式对标不同学生群体：中文主体+考试关键英文标注 / 英文主体+难词中文标注 / 纯中文 / 纯英文 |
| **课程用户命名** | 不替用户做学科归类。关键词智能建议，用户一句话决定课程名 |
| **默认 PDF 输出** | 复习稿默认 PDF 格式，可直接打印装订。也支持 MD/HTML/DOCX |
| **章节考点速记** | 每章结束生成速记表：考点+一句话理解+答题要点123，方便回顾默记翻找 |
| **安全只读** | 绝不移动/删除/修改原始文件，导入=复制+转换 |

## 架构

```
law-import/
├── SKILL.md                    # 唯一源文件 — 7-Phase 完整工作流
├── README.md
├── LICENSE                     # MIT
├── requirements.txt
├── install.py                  # 多 agent 一键安装脚本
├── setup.py                    # 环境检测 + 依赖安装引导
├── agents.json                 # 16 agent 路径映射配置
├── agents/
│   └── codex-plugin.json       # Codex 插件元数据
├── tools/
│   ├── file_finder.py
│   ├── ocr_tool.py
│   ├── format_converter.py
│   ├── classifier.py
│   ├── chunk_manager.py
│   └── output_writer.py
├── config/
│   ├── material_types.json
│   ├── subject_keywords.json
│   └── platform_paths.json
├── templates/
│   └── html_template.html
└── examples/
    └── demo_usage.md
```

## 支持的 AI Coding Agents

一键安装到 16 个 agent。`python install.py` 自动检测已安装的 agent 并部署。

| Agent | 类型 | 检测方式 | 安装位置 |
|-------|------|---------|---------|
| Claude Code (CLI) | skill_md | `~/.claude/` | `.claude/skills/law-import/` |
| Claude Code (IDE) | skill_md | `.claude/skills/` | `.claude/skills/law-import/` |
| Cursor | skill + rule | `~/.cursor/` | `.cursor/skills/` + `.cursor/rules/` |
| Windsurf | skill + rule | `~/.windsurf/` | `.windsurf/skills/` + `.windsurf/rules/` |
| Codex (OpenAI) | skill + plugin | `~/.codex/` | `.codex/skills/` + `.codex/plugins/` |
| Cline (VS Code) | clinerules | `~/.clinerules/` | `.clinerules/law-import.md` |
| GitHub Copilot | instructions | `~/.github/` | `.github/copilot-instructions.md` |
| Gemini CLI | skill_md | `~/.gemini/` | `.gemini/skills/law-import/` |
| OpenCode CLI | skill_md | `~/.opencode/` | `.opencode/skills/law-import/` |
| Kimi Code | skill_md | `~/.kimi/` | `.kimi/skills/law-import/` |
| OpenCalw | skill_md | `~/.opencalw/` | `.opencalw/skills/law-import/` |
| Augment Code | rule | `~/.augment/` | `.augment/rules/law-import.md` |
| Continue.dev | rule | `~/.continue/` | `.continue/rules/law-import.md` |

**只有一个源文件** — `SKILL.md`。所有 agent 指向同一份内容，`install.py` 负责拷贝/链接。

## 支持的操作系统

| 平台 | 微信 | QQ | 通用扫描 |
|------|------|-----|---------|
| Windows 10/11 | ✅ | ✅ | ✅ |
| macOS | ✅ | ✅ | ✅ |
| Linux | ✅ | ✅ | ✅ |

## 没装 Python 怎么办？

| 你有的文件 | 没 Python 能处理吗？ | 需要什么？ |
|-----------|---------------------|-----------|
| `.md` `.txt` `.html` | ✅ 直接处理 | 零依赖 |
| 资料分类 / 课程命名 / 目录创建 | ✅ 直接处理 | Claude 原生 |
| 复习资料生成 (Phase 7) | ✅ 直接处理 | Claude 原生 |
| `.docx` Word 文档 | ❌ 需要 Python | `pip install python-docx` |
| `.pptx` PPT 课件 | ❌ 需要 Python | `pip install python-pptx` |
| `.pdf` (文本) | ❌ 需要 Python | `pip install PyPDF2` |
| `.pdf` (扫描) / `.png` `.jpg` | 🟡 模型有视觉能力→直接用；无→需要 Python + OCR | `pip install easyocr`（仅当模型不支持视觉时） |

**降级行为**：遇到需要 Python 的文件时，skill 不会报错崩溃——标记为 `[待转换: 需 Python]`，跳过，继续处理其他文件。最后汇总"X 个成功，Y 个待转换"。

**安装 Python**：
- Windows: `winget install Python.Python.3.12`
- macOS: `brew install python@3.12`
- Linux: `sudo apt install python3 python3-pip`

然后 `pip install -r requirements.txt`，重新跑一遍导入即可转换之前跳过的文件。

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
4. **案例材料** — 六段式结构化提取+按章节知识点归属判断
5. **教材 vs 笔记** — 标题规整度+学术用语 vs 非正式编号+口语化（用户确认优先级）
6. **术语表** — 术语-定义对结构
7. **学术论文/阅读材料** — 摘要+参考文献列表（统一归入文献）
8. **默认回退** — 通用参考资料

## 目录结构

导入后自动生成：

```
法学/
└── {课程名}/
    ├── 笔记/                   ← 各章节整合后的笔记
    ├── 重点与考纲/
    ├── 试题/
    ├── 案例/                   ← 仅综合性独立案例时创建
    ├── 术语/                   ← 如果有
    ├── 文献/
    ├── review/                 ← 生成的复习稿
    │   ├── section_01.md
    │   └── 复习材料_终稿.pdf
    ├── _原始文件/
    └── {课程}概述.md
```

## 已融合 law-review-generator

原 `law-review-generator` skill 已内化为 **Phase 7: 复习资料生成**。导入管线和复习生成现在是同一条工作流：

- **从零开始**：`/law-import` → 发现文件 → 导入整理 → 自动进入复习生成
- **已有资料**：`/law-import 生成复习 for {课程名}` → 跳过导入，直接 Phase 7
- **旧触发词兼容**：`生成复习资料` `整理复习` `备考材料` `期末复习` 等仍有效，自动路由到 Phase 7

## 开源协议

MIT — 自由使用、修改、分发。

## 贡献

欢迎 PR 到 `config/platform_paths.json`（新增微信/QQ 新版本路径）和 `config/subject_keywords.json`（新增学校/专业关键词）。