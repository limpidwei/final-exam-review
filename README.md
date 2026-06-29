# law-import

**法学资料一站式工作流** — 从微信/QQ自动发现 → 分类整理 → 复习资料生成，一条管线走到底。

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)

## 一句话说明

把微信/QQ里乱七八糟下载的法学资料（课件、笔记、往年题、案例、法条...），自动整理成按课程分类的项目目录，**并直接生成逐章复习稿**。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 可选：安装 OCR 引擎（用于扫描件/图片）
pip install easyocr          # 推荐：GPU加速，中英混合识别

# 3. 一键安装到所有已安装的 AI Coding Agent
python install.py             # 自动检测 → 安装到对应位置
python install.py --list      # 查看支持哪些 agent

# 4. 在任意支持的 Agent 中使用
# Claude Code:     /law-import
# Codex:           /law-import
# Cursor:          说 "法学导入" 或 /law-import
# 其他:            说 "帮我整理法学资料"
python tools/output_writer.py -i ./法学/ -f all         # 生成输出
```

## 它能做什么

```
微信/QQ下载 → 自动发现 → 多模态提取 → 资料类型分类 → 课程命名 → 去重 → 项目结构 → 复习生成 → 多格式输出
    │            │           │              │            │        │        │         │           │
  手动下载    file_finder  OCR/PDF提取   教材?笔记?    "民法总论"  相似度   目录结构  考纲→考点  MD/HTML
  指定路径    .py          格式转换      重点?案例?    用户说了算  检测     MOC      逐章复习  /PDF/DOCX
  不知道在哪                图片OCR       往年题?                                      密度控制  ✅
                           扫描PDF       考纲?                                        质量检查  上下文分段
                           .docx/.pptx   法条?                                        合并输出

   └── Phase 0-4: 导入管线 ──────────────┘     └── Phase 7: 复习生成 ──────────────┘
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
├── SKILL.md                    # 唯一源文件 — 7-Phase 完整工作流
├── README.md
├── LICENSE                     # MIT
├── requirements.txt
├── install.py                  # 多 agent 一键安装脚本
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
| Hermes (Obsidian) | vault note | `法学知识库/` | Obsidian vault skill note |
| Augment Code | rule | `~/.augment/` | `.augment/rules/law-import.md` |
| Continue.dev | rule | `~/.continue/` | `.continue/rules/law-import.md` |

**只有一个源文件** — `SKILL.md`。所有 agent 指向同一份内容，`install.py` 负责拷贝/链接。

## 支持的操作系统

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

## 已融合 law-review-generator

原 `law-review-generator` skill 已内化为 **Phase 7: 复习资料生成**。导入管线和复习生成现在是同一条工作流：

- **从零开始**：`/law-import` → 发现文件 → 导入整理 → 自动进入复习生成
- **已有资料**：`/law-import 生成复习 for {课程名}` → 跳过导入，直接 Phase 7
- **旧触发词兼容**：`生成复习资料` `整理复习` `备考材料` `期末复习` 等仍有效，自动路由到 Phase 7

## 开源协议

MIT — 自由使用、修改、分发。

## 贡献

欢迎 PR 到 `config/platform_paths.json`（新增微信/QQ 新版本路径）和 `config/subject_keywords.json`（新增学校/专业关键词）。