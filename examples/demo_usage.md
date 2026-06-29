# law-import 使用演示

## 场景：从微信下载的法学资料一键整理

你刚上完民法总论，老师发了课件PPT，同学在群里传了笔记、往年题、一份考纲。
你都下载到了微信，但散落在不同的聊天文件夹里。下周考试，你急需整理成可用的复习材料。

---

### Step 1: 触发 skill

在 Claude Code 中说：

```
/law-import
```

Claude 回应：

> 你的法学资料在哪里？
> - 💬 微信下载的
> - 🐧 QQ下载的
> - 📁 我指定路径
> - 🤷 我不知道在哪

### Step 2: 选择来源

选择 "微信下载的"。

Claude 自动扫描后回应：

> 找到 1 个微信账号的下载目录：
> `C:\Users\xxx\Documents\WeChat Files\wxid_abc123\FileStorage\File\`
> 共 17 个文件。继续扫描这个目录？[Y/n]

输入 `Y`。

### Step 3: 语言偏好

Claude 抽样文件后回应：

> 这批文件中，中文为主 11 个，中英混合 5 个，英文为主 1 个。
> 
> 输出语言偏好：
> - [1] 中文为主 + 英文关键术语标注（如"对价 (consideration)"）
> - [2] 英文为主 + 中文关键表述标注（如"consideration (对价)"）
> - [3] 纯中文
> - [4] 纯英文
> 
> 默认 [1]。选哪个？

选择 `[1]`（中文为主，英文术语标注）。这个选择会贯穿后续所有处理。

### Step 4: 确认文件清单

Claude 输出初筛表格：

```
| # | 文件名 | 类型 | 大小 | 修改时间 | 操作 |
|---|--------|------|------|---------|------|
| 1 | 民法总论课件-第1-8章.pptx | .pptx | 8.2MB | 2026-06-28 | ✅ |
| 2 | 民法总论笔记-完整版.docx | .docx | 1.3MB | 2026-06-29 | ✅ |
| 3 | 民法往年题2019-2025.pdf | .pdf | 2.1MB | 2026-06-25 | ✅ |
| 4 | 2026民法总论考纲.docx | .docx | 156KB | 2026-06-20 | ✅ |
| 5 | 法律行为案例汇编.docx | .docx | 890KB | 2026-06-27 | ✅ |
| 6 | 物权法笔记(好像不是民总的).docx | .docx | 450KB | 2026-06-26 | ⚠️ |
| 7 | setup_wechat.exe | .exe | 2.3MB | 2026-05-01 | ❌ 排除 |
| ... | ... | ... | ... | ... | |
```

你对 #6 不确定 —— 取消勾选，#7 系统已自动排除（安装程序）。确认其余。

### Step 5: 多模态提取

Claude 开始逐文件处理：

```
[1/5] 民法总论课件-第1-8章.pptx → 提取文本... ✅ (48 页幻灯片, 约 12,000 字)
[2/5] 民法总论笔记-完整版.docx → 提取文本... ✅ (约 18,000 字)
[3/5] 民法往年题2019-2025.pdf → 检测：文本PDF → 提取... ✅ (约 25,000 字)
[4/5] 2026民法总论考纲.docx → 提取文本... ✅ (约 2,000 字)
[5/5] 法律行为案例汇编.docx → 提取文本... ✅ (约 15,000 字)
```

### Step 6: 资料类型分类

逐维检视结果：

```
| # | 文件 | 考纲? | 重点? | 往年题? | 法条? | 案例? | 教材/笔记? | 最终类型 | 置信度 |
|---|------|-------|-------|--------|------|------|-----------|---------|--------|
| 1 | 民法总论课件.pptx | ✗ | ✗ | ✗ | ✗ | ✗ | 教材 | 教材 | 高 |
| 2 | 民法总论笔记.docx | ✗ | 含"【★重点】"3处 | ✗ | ✗ | ✗ | 笔记+重点 | 笔记(含重点) | 高 |
| 3 | 民法往年题.pdf | ✗ | ✗ | Q&A结构+分值 | ✗ | 含1道案例题 | — | 往年题 | 高 |
| 4 | 民法总论考纲.docx | 课程目标+学时 | 含考点权重 | ✗ | ✗ | ✗ | — | 考纲 | 高 |
| 5 | 法律行为案例.docx | ✗ | ✗ | ✗ | ✗ | 原告/被告/法院认为 | — | 案例材料 | 高 |
```

### Step 7: 课程命名

Claude 的关键词建议：

> 💡 看起来这些内容跟 **民法学** 比较相关。这些资料是关于哪个考试/课程的？

你回答：**"民法总论 期末"**

Claude：好的，全部 5 个文件归入 **"民法总论"**。确认？[Y/n]

`Y`

### Step 8: 最终确认

分类+课程确认后的最终清单：

```
民法总论  × 5 文件
├── 笔记/          ← 民法总论笔记-完整版.md
├── 重点与考纲/    ← 2026民法总论考纲.md
├── 试题/          ← 民法往年题2019-2025.md
├── 案例/          ← 法律行为案例汇编.md
└── (教材转笔记)   ← 民法总论课件-第1-8章.md
```

确认，开始导入。

### Step 9: 导入执行 + 输出

```
民法总论/
├── 笔记/
│   ├── 民法总论课件-第1-8章.md     (教材, 48页转换)
│   └── 民法总论笔记-完整版.md      (笔记, 含【★重点】标记)
├── 重点与考纲/
│   └── 2026民法总论考纲.md         (考纲, 考点权重)
├── 试题/
│   └── 民法往年题2019-2025.md     (往年题, 6年)
├── 案例/
│   └── 法律行为案例汇编.md         (案例, 15则)
├── _原始文件/                      (原始文件保留)
└── 民法总论概述.md                 (MOC索引)
```

### Step 10: 导入报告

```
## 📥 法学资料导入报告 — 2026-06-30

### 概览
| 指标 | 数值 |
|------|------|
| 来源 | 微信 (wxid_abc123) |
| 发现 | 17 个文件 |
| 确认 | 5 个文件 |
| 语言模式 | 中文为主 + 英文术语标注 |
| 格式分布 | .pptx×1, .docx×3, .pdf×1 |
| 成功 | 5 ✅ |
| 失败 | 0 |

### 课程分布
| 课程 | 文件 | 类型分布 |
|------|------|---------|
| 民法总论 | 5 | 教材×1, 笔记(含重点)×1, 往年题×1, 考纲×1, 案例×1 |

### 下一步建议
🔍 发现考纲1份 + 重点标记3处 + 往年题6年 → 建议立即触发生成复习
📋 回复 "生成复习" 或 /law-review-generator
```

### Step 11: 触发复习生成（可选）

回复 "生成复习" → law-review-generator 自动以考纲为骨架、以笔记为素材、以往年题为权重，生成逐章复习稿。

---

## 命令行等效操作（不用 Claude Code）

```bash
# Step 2: 发现文件
python tools/file_finder.py --platform wechat

# Step 5: 格式转换
python tools/format_converter.py -i 民法总论课件.pptx -m pptx2md -o 课件.md
python tools/format_converter.py -i 民法总论笔记.docx -m docx2md -o 笔记.md
python tools/format_converter.py -i 民法往年题.pdf -m pdf2md -o 往年题.md

# Step 6: 分类
python tools/classifier.py -i 笔记.md -m full
# → {"material_type": {"primary_type": "lecture_notes", ...}, "subject_suggestion": {...}}

# Step 9: 生成输出
python tools/output_writer.py -i ./民法总论/ -f all -o ./output/
# → 生成 output/民法总论.md + .html + .pdf + .docx
```

---

## 语言模式效果示例

同一段内容在不同语言模式下的输出：

**原文（中英混合笔记）：**
> 侵权责任的构成要件包括 duty of care, breach, causation, and damages。
> 其中 causation 又分为事实因果关系 (factual causation) 和法律因果关系 (legal causation)。

**模式 [1] 中文为主 + 英文关键术语标注：**
> 侵权责任的构成要件包括注意义务 (duty of care)、违反义务 (breach)、因果关系 (causation) 和损害 (damages)。其中因果关系 (causation) 又分为事实因果关系 (factual causation) 和法律因果关系 (legal causation)。

**模式 [2] 英文为主 + 中文关键表述标注：**
> The elements of tort liability include duty of care, breach, causation (因果关系), and damages (损害). Causation is further divided into factual causation (事实因果关系) and legal causation (法律因果关系).

**模式 [3] 纯中文：**
> 侵权责任的构成要件包括注意义务、违反义务、因果关系和损害。其中因果关系又分为事实因果关系和法律因果关系。

**模式 [4] 纯英文：**
> The elements of tort liability include duty of care, breach, causation, and damages. Causation is further divided into factual causation and legal causation.
