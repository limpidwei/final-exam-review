---
name: law-import
description: 法学资料一站式工作流。自动发现微信/QQ下载的法学资料（或用户指定路径），多模态格式归一化（OCR/扫描PDF/图片/文档），逐文件资料类型分类（教材/笔记/重点/往年题/案例/术语表/阅读材料/论文/考纲/法条），由用户命名课程归属，去重，按课程创建项目目录结构，内置复习资料生成器（考纲→考点映射→逐章复习稿→多格式输出），大文件上下文窗口分段处理。已融合 law-review-generator。Use when user mentions "法学导入", "导入资料", "整理下载", "从微信整理", "从QQ整理", "法学资料整理", "复习资料", "整理复习", "备考材料", "期末复习", "法学期末", "生成复习" or wants to import law study materials or generate exam review materials.
---

# 法学资料导入器

## 设计理念

面向**开源分发**的完整法学资料导入管线。零配置启动：用户只需告知文件来源（微信/QQ/指定路径/不知道），skill 自动完成从多模态文件发现到结构化知识库输出的全过程。

### 核心能力

```
                    ┌────────── law-import 一站式工作流 ──────────┐
                    │                                              │
多模态文件 → OCR/提取 → 统一文本 → 类型分类 → 课程命名 → 去重 → 项目结构 → 复习生成 → 多格式输出
   │            │                    │           │         │        │         │           │
  图片      Tesseract           教材?      "民法总论"   相似度   目录结构  考纲→考点  MD/HTML
  扫描PDF   EasyOCR             笔记?      用户说了算   字节     MOC      逐章复习  PDF/DOCX
  DOCX      python-docx         往年题?               内容     索引     密度控制  上下文分段
  PPTX      python-pptx         重点?                                    质量检查  大文件
  EPUB      ebooklib            案例?                                    合并输出  分块处理
  幕布JSON  递归解析            术语表?
  HTML      文本提取            论文?
  ...                           考纲?
                                法条?
                    │                                              │
                    └── Phase 0-4: 导入管线 ── Phase 7: 复习生成 ──┘
```

---

## 触发

用户说"法学导入"、"导入法学资料"、"整理下载的法学材料"、"从微信/QQ导入法学资料"等。

---

## 6 阶段完整决策树

```
用户触发 law-import
│
├─ PHASE 0: 路径发现与文件枚举
│  │
│  ├─ [0.1] 用户提供了具体路径？
│  │  ├─ YES → 验证路径存在 → 跳到 [0.5]
│  │  └─ NO → [0.2]
│  │
│  ├─ [0.2] 用户提示了来源平台？
│  │  ├─ "微信" → 执行 `python tools/file_finder.py --platform wechat`
│  │  │  ├─ 找到 ≥1 个 wxid 目录 → 列出路径+文件数 → 用户选择 → [0.5]
│  │  │  └─ 未找到 → 告知原因 → 回退到 [0.3]
│  │  ├─ "QQ" → 执行 `python tools/file_finder.py --platform qq`
│  │  │  ├─ 找到 ≥1 个 QQ号目录 → 列出路径+文件数 → 用户选择 → [0.5]
│  │  │  └─ 未找到 → 告知原因 → 回退到 [0.3]
│  │  └─ 用户不知来源 → [0.3]
│  │
│  ├─ [0.3] 通用扫描
│  │  ├─ 扫描 Downloads / Desktop / Documents / D:\大学\ / D:\法学\
│  │  ├─ 文件类型过滤：.docx .pdf .txt .md .pptx .json .doc .xmind .html .epub .png .jpg .jpeg
│  │  ├─ 法学关键词初筛
│  │  ├─ 找到疑似法学文件？
│  │  │  ├─ YES → 按来源路径分组展示 → 用户确认 → [0.5]
│  │  │  └─ NO → 告知 → 请用户手动指定路径或扩大扫描
│  │  └─ 上限：展示 50 个候选文件
│  │
│  ├─ [0.4] 路径确认后的扩展扫描（可选）
│  │  └─ 用户可追加多个路径 → 合并文件列表 → [0.5]
│  │
│  └─ [0.5] 文件初筛清单
│     ├─ 排除：系统文件(~$) 临时文件(.tmp .crdownload) 空文件(<1KB) 安装程序
│     ├─ 排除：文件名纯数字/乱码、明显非资料（.exe .dll .msi .zip .rar .7z）
│     ├─ 按修改时间倒序排列
│     └─ 输出初步表格 → 用户逐文件勾选确认 → [0.6]
│
│  └─ [0.6] 语言偏好设置（文件确认后立即询问）
│     │
│     │  为什么这时问：语言选择影响 OCR 引擎配置、格式转换时的术语标注策略、
│     │  以及最终输出的双语对照格式。在文件处理开始前确定，避免后续返工。
│     │
│     ├─ [0.6a] 先扫描文件语言分布（轻量估算，不读取全部内容）：
│     │  ├─ 统计文件名中的中文字符 vs 英文字符比例
│     │  ├─ 抽样前 500 字节估算正文语言比例
│     │  └─ 报告："这批文件中，中文为主 X 个，英文为主 Y 个，中英混合 Z 个"
│     │
│     ├─ [0.6b] 展示四个选项，用户选择：
│     │  │
│     │  │  ┌─────────────────────────────────────────────────────────┐
│     │  │  │  输出语言偏好：                                          │
│     │  │  │                                                         │
│     │  │  │  [1] 中文为主 + 英文关键术语标注                         │
│     │  │  │      → 正文中文，"对价 (consideration)"、"过失 (negligence)"│
│     │  │  │      → 适合：中文授课、中文教材、国内考试复习            │
│     │  │  │                                                         │
│     │  │  │  [2] 英文为主 + 中文关键表述标注                         │
│     │  │  │      → 正文英文，"consideration (对价)"、"negligence (过失)"│
│     │  │  │      → 适合：英文授课/LLM/留学考试/英文教材              │
│     │  │  │                                                         │
│     │  │  │  [3] 纯中文                                              │
│     │  │  │      → 仅保留中文，英文术语不标注（除非原文仅有英文）     │
│     │  │  │      → 适合：纯中文资料整理、国内法考复习                │
│     │  │  │                                                         │
│     │  │  │  [4] 纯英文                                              │
│     │  │  │      → 仅保留英文，中文术语不标注（除非原文仅有中文）     │
│     │  │  │      → 适合：英文论文/国际期刊/海外考试                  │
│     │  │  └─────────────────────────────────────────────────────────┘
│     │  │
│     │  ├─ 用户选择 [1] 或 [2] → 后续所有提取步骤启用双语对照模式
│     │  │  ├─ 术语表：自动生成中←→英对照
│     │  │  ├─ 概念卡片：主语言阐述 + 括号标注对译
│     │  │  ├─ OCR：chi_sim+eng 双语言模型
│     │  │  └─ 输出：frontmatter 标注 `language_mode: bilingual_zh` 或 `bilingual_en`
│     │  ├─ 用户选择 [3] 或 [4] → 单语模式
│     │  │  ├─ 术语表：仅保留主语言
│     │  │  ├─ OCR：仅加载主语言模型（更快）
│     │  │  └─ 输出：frontmatter 标注 `language_mode: zh_only` 或 `en_only`
│     │  └─ 用户未选择（跳过）→ 默认 [1] 中文为主 + 英文关键术语标注
│     │
│     └─ [0.6c] 语言偏好写入 session context，贯穿所有后续 Phase
│
├─ PHASE 1: 多模态格式归一化
│  │
│  └─ 对每个用户确认的文件，按格式类型分发到对应提取器：
│     │
│     ├─ [1.1] 判断文件模态类型
│     │  │
│     │  ├─ 文本模态（直接可读文本）：
│     │  │  ├─ .md / .txt → 直接读取，UTF-8/GBK 自动检测编码
│     │  │  ├─ .html → 提取 body 文本，去除标签，保留标题层级
│     │  │  └─ .json（幕布导出）→ 递归解析节点树 → 生成层级 MD
│     │  │
│     │  ├─ 文档模态（需解析的富文本）：
│     │  │  ├─ .docx → `python tools/format_converter.py --input file.docx --mode docx2md`
│     │  │  ├─ .pptx → `python tools/format_converter.py --input file.pptx --mode pptx2md`
│     │  │  └─ .epub → `python tools/format_converter.py --input file.epub --mode epub2md`
│     │  │
│     │  ├─ PDF 模态（需判断文本/扫描）：
│     │  │  ├─ [1.1a] 检测 PDF 是否为扫描件
│     │  │  │  ├─ 使用 PyPDF2 尝试提取文本
│     │  │  │  ├─ 提取文本 < 100 字符 且页数 > 1 → 判定为扫描件
│     │  │  │  └─ 提取文本 ≥ 100 字符 → 判定为文本 PDF
│     │  │  ├─ 文本 PDF → `python tools/format_converter.py --mode pdf2md`
│     │  │  └─ 扫描 PDF → 进入 OCR 管线 [1.3]
│     │  │
│     │  └─ 图像模态（需 OCR）：
│     │     ├─ .png / .jpg / .jpeg / .bmp / .tiff
│     │     ├─ 包含文字的截图（微信聊天记录截图等）
│     │     └─ 进入 OCR 管线 [1.3]
│     │
│     ├─ [1.2] 文本提取上下文窗口估算
│     │  ├─ 计算提取后文本的 token 估算值（中文 ≈ 字数 × 1.5, 英文 ≈ 词数 × 1.3）
│     │  ├─ token < 80% 模型上下文窗口 → 直接全量处理
│     │  ├─ token ≥ 80% 上下文窗口 → 标记为"大文件"，进入分段策略
│     │  └─ 分段策略：
│     │     ├─ 按自然章节边界切分（H1/H2 标题 / 页码标记 / 明显分隔线）
│     │     ├─ 每个分段 ≤ 60% 上下文窗口
│     │     ├─ 分段间保留 200 字符重叠（避免边界断裂）
│     │     ├─ 每段独立处理 → 最后合并（通过 section_merger）
│     │     └─ 合并时验证衔接完整性（检查段间是否有孤儿标题/句子）
│     │
│     └─ [1.3] OCR 管线（语言模式影响引擎语言配置）
│        ├─ 语言参数由 [0.6] 语言偏好决定：
│        │  ├─ 模式 [1] 中文为主+英文标注 → `--lang chi_sim+eng`
│        │  ├─ 模式 [2] 英文为主+中文标注 → `--lang eng+chi_sim`
│        │  ├─ 模式 [3] 纯中文 → `--lang chi_sim`
│        │  └─ 模式 [4] 纯英文 → `--lang eng`
│        ├─ 预处理：
│        │  ├─ 图像增强（对比度/锐化/去噪）→ 提高识别率
│        │  ├─ 倾斜校正（自动检测+旋转）
│        │  └─ 区域检测（区分文字区/图片区/表格区）
│        ├─ OCR 引擎选择（自动降级）：
│        │  ├─ 首选：EasyOCR（GPU 加速，语言列表按模式配置）
│        │  ├─ EasyOCR 不可用 → Tesseract 5（语言参数同上）
│        │  └─ Tesseract 不可用 → 告知用户安装: `pip install easyocr`
│        ├─ 执行：`python tools/ocr_tool.py --input image.png --lang {按模式}`
│        ├─ 后处理：
│        │  ├─ 拼写纠错（法学专业术语词典增强，语言模式决定词典语言）
│        │  ├─ 段落合并（OCR 断行修复）
│        │  ├─ 双语模式 [1][2]：识别中英混排段落，标记语言切换点
│        │  └─ 置信度标注（< 70% 的字符用 [低置信: ...] 标记）
│        └─ 输出：纯文本 → 进入统一文本池
│
├─ PHASE 2: 资料类型分类（Step-by-step 逐维检视）
│  │
│  └─ 对归一化后的每个文本块，按以下维度逐层分类。每层独立给分，
│     最后按 `config/material_types.json` 的优先级仲裁。
│     │
│     ├─ [2.1] 维度一：是否为考纲/大纲？
│     │  ├─ 检测特征：含"课程目标"+"学时"+"考核方式"？含学时分配表？
│     │  ├─ YES → 标记为 syllabus（最高优先级），置信度=高
│     │  │  └─ 提取：考点列表、权重分配、教材信息 → 写入 topic_map 候选
│     │  └─ NO → 进入 [2.2]
│     │
│     ├─ [2.2] 维度二：是否含重点/考点标记？
│     │  ├─ 检测特征：含【★重点】【必考】【历年真题】【高频】等标记？
│     │  ├─ 检测特征：含"不考""了解即可"排除标记？
│     │  ├─ YES → 标记为 key_points + 相关学科
│     │  │  ├─ 提取所有标记项 → 生成重点清单
│     │  │  └─ 与已有 topic_map 交叉验证
│     │  └─ NO → 进入 [2.3]
│     │
│     ├─ [2.3] 维度三：是否为往年试题？
│     │  ├─ 检测特征：Q&A交替结构？题号+分值标注？含"简答题""论述题""名词解释"？
│     │  ├─ 检测特征：含"参考答案""评分标准"？
│     │  ├─ YES → 标记为 past_exams
│     │  │  └─ 提取：题型分类、年份标注、分值权重 → 考点频次统计
│     │  └─ NO → 进入 [2.4]
│     │
│     ├─ [2.4] 维度四：是否为法条/法规文本？
│     │  ├─ 检测特征："第X条"编号体系？含"施行""修订"日期？含"款""项""目"层级？
│     │  ├─ 检测特征：含"主席令""国务院令""司法解释"？
│     │  ├─ YES → 标记为 statutes → 按条拆分为独立卡片
│     │  └─ NO → 进入 [2.5]
│     │
│     ├─ [2.5] 维度五：是否为案例材料？
│     │  ├─ 检测特征：含"原告""被告""法院认为""判决如下"？含案号？
│     │  ├─ 检测特征：事实-争议焦点-法院观点三段结构？
│     │  ├─ YES → 标记为 case_materials
│     │  │  └─ 提取：案情摘要 + 争议焦点 + 法院观点 + 法理分析
│     │  └─ NO → 进入 [2.6]
│     │
│     ├─ [2.6] 维度六：是教材还是笔记？
│     │  ├─ 教材特征：层级标题规整（章-节-目）、含"学习目标""课后习题""本章小结"
│     │  ├─ 笔记特征：非正式编号、含"老师""上课""PPT""→""ps:"
│     │  ├─ 教材 → 标记为 textbook, 置信度 ± 笔记特征干扰
│     │  ├─ 笔记 → 标记为 lecture_notes
│     │  ├─ 两者特征混杂 → 标记为 lecture_notes（保守），置信度=中
│     │  └─ 两者都不明显 → 标记为 reference（通用参考资料），进入 [2.7]
│     │
│     ├─ [2.7] 维度七：是否为术语表/名词解释？
│     │  ├─ YES → 标记为 glossary → 按术语-定义对拆分
│     │  └─ NO → 进入 [2.8]
│     │
│     ├─ [2.8] 维度八：是否为学术论文？
│     │  ├─ YES → 标记为 academic_paper → 提取摘要+论点
│     │  └─ NO → 进入 [2.9]
│     │
│     └─ [2.9] 维度九：是否为阅读材料列表？
│        ├─ YES → 标记为 reading_materials → 提取文献条目
│        └─ NO → 最终回退类型 = lecture_notes（默认）或 reference
│
├─ PHASE 3: 课程归属 + 质量评估 + 去重
│  │
│  │  设计原则：学生最清楚自己要考什么。不替用户做学科归类——
│  │  关键词匹配仅用于"智能建议"，最终由用户一句话决定。
│  │
│  ├─ [3.1] 课程/考试归属（用户主导，关键词辅助）
│  │  │
│  │  ├─ [3.1a] 先问用户，不等分类器跑完：
│  │  │  └─ "这些资料是关于哪门课/哪个考试的？（比如'民法总论期末''刑法分论''法考民法'）"
│  │  │
│  │  ├─ [3.1b] 同时做关键词轻量扫描作为智能建议（不阻塞用户输入）：
│  │  │  ├─ 用 `config/subject_keywords.json` 跑一轮命中统计（中文 ×1.0, 英文 ×0.8）
│  │  │  ├─ 命中 ≥ 3 个关键词 + 领先 ≥ 2 → 生成一条建议：
│  │  │  │  └─ "💡 看起来这些内容跟 **{学科名}** 比较相关。是这个课吗？还是别的？"
│  │  │  ├─ 多条建议（最多 3 条）→ 列出来让用户点选或忽略
│  │  │  └─ 什么都没有命中 → 不猜测，静默等待用户输入
│  │  │
│  │  ├─ [3.1c] 用户回答后的处理：
│  │  │  ├─ 用户说了一个课程名（如"民法总论"）→ 这就是 folder name，直接使用
│  │  │  ├─ 用户说了多个课程（如"民法 + 刑法"）→ 请用户把文件分配到各课程
│  │  │  │  └─ 输出分组表格，用户拖拽式确认 → 每个文件绑定到一个课程
│  │  │  ├─ 用户说"就是法考内容" → folder name = "法考"，所有文件归入
│  │  │  └─ 用户也不确定 → 展示关键词建议的 TOP 3 + "自定义输入"
│  │  │
│  │  └─ [3.1d] 一个文件可能属于多个课程？
│  │     └─ 问用户："这个文件要复制到多个课程目录，还是只放一个？"
│  │        ├─ 复制 → 两份独立副本，frontmatter 标注 cross-listed
│  │        └─ 只放一个 → 用户指定主课程，另一课程目录放 wikilink 快捷方式
│  │
│  │  为什么不用固定16学科硬分类：
│  │  - 每个学校课程设置不同（侵权法可能独立开课，也可能在民法下）
│  │  - 学生命名方式不同（"民法总论"vs"民法上"vs"民总"）
│  │  - 开源工具不能假定用户课程表
│  │  - `subject_keywords.json` 保留为可选建议词典，用户可替换为自己的学校课程关键词
│  │
│  ├─ [3.2] 内容质量评估
│  │  ├─ 完整性检查：
│  │  │  ├─ 含目录但正文缺失章节 → 标记 [缺: 第X章]
│  │  │  ├─ 文中引用"同上""见前"但无上文 → 标记 [缺上下文]
│  │  │  └─ 引用外部材料但未附加 → 标记 [缺: 附件]
│  │  ├─ 格式一致性：
│  │  │  ├─ 标题编号跳跃（如 1. → 3. 缺 2.）→ 标记 [格式: 编号不连续]
│  │  │  └─ 表格残缺（表头无表体/表体无表头）→ 标记 [格式: 表格残缺]
│  │  └─ 可信度标注：
│  │     ├─ 来源 = 课件/教材 → 高可信度
│  │     ├─ 来源 = 个人笔记/回忆 → 中可信度，标记 [待核实]
│  │     └─ 来源不明 → 低可信度，标记 [存疑: 来源不明]
│  │
│  └─ [3.3] 去重检测
│     ├─ 维度1：文件名相似度 > 85%（Levenshtein / LCS）
│     ├─ 维度2：文件大小完全相同（字节级 MD5）
│     ├─ 维度3：前 800 字符内容相似度 > 90%（Jaccard / cosine）
│     ├─ ≥2 项命中 → 高度疑似重复，建议跳过
│     ├─ 1 项命中 → 可能重复，列出差异让用户判断
│     └─ 0 项命中 → 新文件，正常导入
│
├─ PHASE 4: 项目目录结构创建
│  │
│  │  设计原则：目录结构按用户命名的课程动态生成，不预置16学科。
│  │  用户可能只有一个课（"民法总论期末"），也可能有多个（"民法+刑法+法理"）。
│  │
│  ├─ [4.1] 确定输出根目录
│  │  ├─ Obsidian vault 可用？→ `{vault}/法学/`
│  │  ├─ 用户指定输出路径？→ `{user_path}/法学/`
│  │  └─ 都无 → 默认 `./法学/`（当前目录，开源用户默认路径）
│  │
│  ├─ [4.2] 按用户命名的课程动态创建目录
│  │  │
│  │  ├─ 单课程（如用户说"民法总论"）：
│  │  │  ```
│  │  │  法学/
│  │  │  └── 民法总论/
│  │  │      ├── 笔记/           # lecture_notes + textbook
│  │  │      ├── 重点与考纲/     # key_points + syllabus
│  │  │      ├── 试题/           # past_exams
│  │  │      ├── 案例/           # case_materials
│  │  │      ├── 法条/           # statutes
│  │  │      ├── 术语/           # glossary
│  │  │      ├── 文献/           # academic_paper + reading_materials
│  │  │      ├── _原始文件/      # 原始文件保留（只读）
│  │  │      └── 民法总论概述.md  # MOC/索引文件
│  │  │  ```
│  │  │
│  │  └─ 多课程（如用户说"民法总论 + 刑法分论 + 法理"）：
│  │     ```
│  │     法学/
│  │     ├── 民法总论/
│  │     │   ├── 笔记/
│  │     │   ├── 重点与考纲/
│  │     │   ├── 试题/
│  │     │   ├── ... (同上)
│  │     │   └── 民法总论概述.md
│  │     ├── 刑法分论/
│  │     │   └── ... (同上)
│  │     ├── 法理/
│  │     │   └── ... (同上)
│  │     ├── _跨课程/            # 跨课程共享：法条/术语/文献
│  │     │   ├── 法条/
│  │     │   ├── 术语/
│  │     │   └── 文献/
│  │     ├── _原始文件/          # 全局原始文件保留
│  │     └── 法学总览.md         # 全局 MOC
│  │     ```
│  │
│  ├─ [4.3] 按 Phase 2 资料类型分发到子目录
│  │  ├─ lecture_notes / textbook → `{课程}/笔记/`
│  │  ├─ key_points / syllabus → `{课程}/重点与考纲/`
│  │  ├─ past_exams → `{课程}/试题/`
│  │  ├─ case_materials → `{课程}/案例/`
│  │  ├─ statutes → `{课程}/法条/`（如多课程共享 → `_跨课程/法条/`）
│  │  ├─ glossary → `{课程}/术语/`（如通用 → `_跨课程/术语/`）
│  │  ├─ academic_paper / reading_materials → `{课程}/文献/`
│  │  └─ 无法归类 → `{课程}/笔记/`（默认）
│  │
│  └─ [4.4] 创建/更新索引文件
│     ├─ 生成/更新 课程 MOC（`{课程}概述.md`，含该课程所有子目录的 wikilink）
│     ├─ 多课程时生成 `法学总览.md`（全局 MOC，含所有课程入口）
│     ├─ 生成/更新 `_原始文件/原始文件索引.md` — 记录 source→note 映射
│     └─ 追加 `_原始文件/项目进度.md` — 本次导入记录
│
├─ PHASE 5: 输出生成
│  │
│  ├─ [5.1] 用户选择输出格式
│  │  ├─ MD（默认）→ 适合 Obsidian / 通用 Markdown 阅读器
│  │  ├─ HTML → 适合浏览器查看 / 打印 / 分享链接
│  │  ├─ PDF → 适合打印装订 / 提交作业
│  │  ├─ DOCX → 适合 Word 进一步编辑
│  │  └─ ALL → 一次生成全部格式
│  │
│  ├─ [5.2] 上下文窗口分段处理
│  │  ├─ 单文件 token < 80% 上下文窗口 → 直接处理
│  │  ├─ 单文件 token ≥ 80% 上下文窗口：
│  │  │  ├─ 拆分为 N 个分段（按章节边界），每段 ≤ 60% 上下文
│  │  │  ├─ 对每段独立执行分类+结构提取
│  │  │  ├─ 生成 N 个临时结果
│  │  │  └─ 合并器（section_merger）：
│  │  │     ├─ 按章节编号聚合
│  │  │     ├─ 处理跨段句子（通过 200 字符重叠区检测）
│  │  │     └─ 输出统一文件
│  │  │
│  │  └─ 多文件总 token 超过上下文窗口：
│  │     ├─ 分批处理（每批 N 个文件，确保 batch token < 60% 上下文）
│  │     ├─ 批次间用户可暂停/跳过/调整顺序
│  │     └─ 最终汇总报告合并所有批次结果
│  │
│  ├─ [5.3] 格式生成器
│  │  ├─ MD 输出：
│  │  │  ├─ 标准 Obsidian 兼容 Markdown（wikilink, frontmatter, 标签）
│  │  │  ├─ 层级标题保留原结构
│  │  │  └─ 每个文件含完整 frontmatter（见下方模板）
│  │  ├─ HTML 输出：`python tools/output_writer.py --format html --template law_note`
│  │  │  ├─ 使用 `templates/html_template.html` 渲染
│  │  │  ├─ 含目录侧边栏、搜索、打印样式
│  │  │  └─ 所有学科合集页（index.html）
│  │  ├─ PDF 输出：`python tools/output_writer.py --format pdf`
│  │  │  ├─ MD → HTML → WeasyPrint/Playwright → PDF
│  │  │  ├─ 含页眉（学科名）、页脚（页码）
│  │  │  └─ 自动生成目录页
│  │  └─ DOCX 输出：`python tools/output_writer.py --format docx`
│  │     ├─ 使用 python-docx 模板渲染
│  │     ├─ 保留标题层级（Heading 1-4 对应 Word 样式）
│  │     └─ 表格/列表完整转换
│  │
│  └─ [5.4] Frontmatter 模板
│     ```yaml
│     ---
│     title: "{从文件名+内容推断的规范标题}"
│     language_mode: {bilingual_zh|bilingual_en|zh_only|en_only}
│     course: "{用户命名的课程名，如'民法总论''刑法分论''法考民法'}"
│     subject_hint: "{关键词建议的学科标签，如'民法学'。仅供参考，以course为准}"
│     type: {textbook|lecture-notes|key-points|past-exam|case-material|glossary|reading-material|academic-paper|statute|syllabus}
│     source: "{原始文件绝对路径}"
│     source_format: {docx|pdf|pptx|png|txt|md|json|epub|html}
│     source_content_type: {text|scanned|image|mixed}
│     ocr_applied: {true|false}
│     ocr_engine: {easyocr|tesseract|none}
│     ocr_confidence: {0.0-1.0|N/A}
│     token_count: {估算token数}
│     chunked: {true|false}
│     chunk_index: {分段序号|N/A}
│     quality_flags: [{缺:XX}|{存疑:XX}|{格式:XX}|]
│     exam_relevance: {highest|high|medium|low|none}
│     exam_markers: [{★重点}|{必考}|{历年真题}|]
│     has_cases: {true|false}
│     has_statutes: {true|false}
│     has_glossary: {true|false}
│     cross_listed: [{其他课程名}|]      # 如果一个文件属于多课程
│     status: raw-import
│     imported: {YYYY-MM-DD}
│     imported_by: law-import-skill
│     tags:
│       - {type_tag}
│       - {exam_tag_if_applicable}
│     ---
│
│     注：language_mode 贯穿全部 Phase：
│     - bilingual_zh：中文正文 + 英文术语括号标注 → "对价 (consideration)"
│     - bilingual_en：英文正文 + 中文术语括号标注 → "consideration (对价)"
│     - zh_only：仅保留中文（英文术语如原文仅有英文则保留原文）
│     - en_only：仅保留英文（中文术语如原文仅有中文则保留原文）
│     ```
│
├─ PHASE 6: 导入报告
│  │
│  ├─ [6.1] 生成导入报告（见报告模板）
│  ├─ [6.2] 判断是否自动进入 Phase 7：
│  │  ├─ 含 syllabus / key_points / past_exams 任一 → "检测到备考材料，建议立即生成复习资料"
│  │  │  └─ 默认进入 Phase 7，用户可选跳过
│  │  └─ 仅有 notes / textbook / cases → "导入完成。是否需要生成复习资料？"
│  │     ├─ YES → Phase 7
│  │     └─ NO → 完成
│  └─ [6.3] 更新项目进度文件
│
├─ PHASE 7: 复习资料生成（融合 law-review-generator）
│  │
│  │  设计原则：这是 law-import 的自然延续，不是单独的 skill。
│  │  导入完成 → 复习生成，一气呵成。所有导入阶段的信息（资料类型、课程名、
│  │  语言模式、特殊标记）直接复用，无需重复配置。
│  │
│  ├─ [7.1] 源材料盘点与覆盖评估
│  │  ├─ 展示该课程的可用源材料，按资料类型分组：
│  │  │  | 类型 | 文件 | 用途 | 覆盖章节 |
│  │  │  |------|------|------|---------|
│  │  │  | 考纲 | 2026民法总论考纲.md | 考点框架+权重 | 全部8章 |
│  │  │  | 笔记 | 民法总论笔记.md | 中文阐述主体 | 第1-7章 |
│  │  │  | 教材 | 民法总论课件.md | 定义+体系 | 第1-8章 |
│  │  │  | 往年题 | 民法往年题2019-2025.md | 高频考点标注 | — |
│  │  │  | 案例 | 法律行为案例汇编.md | 法理嵌入 | 第3-5章 |
│  │  ├─ 覆盖率评估：哪些章节缺源材料？标记 [缺源: 第X章]
│  │  └─ 用户确认考试范围：
│  │     ├─ 哪些章不考？（如"第8章不考"）→ 排除
│  │     └─ 是否有额外考点需要补充？（口头补充，无需文件）
│  │
│  ├─ [7.2] 建立考点映射（topic_map）
│  │  │
│  │  ├─ 自动提取（优先级链）：
│  │  │  ├─ syllabus → 考点列表 + 权重（【必考】【★重点】【了解】）+ 学时分配
│  │  │  ├─ key_points → 补充考点标记 + 【★重点】具体内容
│  │  │  ├─ past_exams → 统计每个考点的出题频次 + 题型分布
│  │  │  │  └─ 输出：`考点 | 出现年份 | 题型 | 平均分值`
│  │  │  └─ textbook/notes 的 H1/H2 标题 → 补充 syllabus 未覆盖的考点
│  │  │
│  │  ├─ 无 syllabus 时的降级策略：
│  │  │  ├─ 有 key_points → 从重点标记反向推导考点列表
│  │  │  ├─ 有 past_exams → 从试题题干提取考点关键词
│  │  │  └─ 仅有笔记 → 按 H1/H2 标题自动生成 topic_map（每个 H2 = 一个考点，权重默认【了解】）
│  │  │
│  │  └─ 输出 topic_map 给用户确认（表格 + JSON）：
│  │     | 章 | 考点 | 权重 | 源材料 | 往年出现 | 有案例？|
│  │     |----|------|------|--------|---------|--------|
│  │     | 1 | 民法概述 | 【了解】 | 笔记§1, 课件§1 | 0次 | ✗ |
│  │     | 3 | 法律行为 | 【必考】 | 笔记§3, 课件§3, 案例3则 | 6次(论述×3+案例×3) | ✓ |
│  │     | ... | ... | ... | ... | ... | ... |
│  │     用户可调整：修改权重、增删考点、调整章节归属
│  │
│  ├─ [7.3] 逐章生成复习 Section
│  │  │
│  │  ├─ 对 topic_map 中每个考点，按权重分配篇幅：
│  │  │  ├─ 【必考】→ 200-400 行（约 4-8 页 A4）
│  │  │  ├─ 【★重点】→ 100-200 行（约 2-4 页 A4）
│  │  │  ├─ 【了解】→ 30-80 行（约 0.5-1.5 页 A4）
│  │  │  └─ 不考 → 跳过
│  │  │
│  │  ├─ 每个考点的标准四段式结构：
│  │  │  ```markdown
│  │  │  ## [考点名]                                         ← H2/H3
│  │  │
│  │  │  ### 1. 核心概念与定义
│  │  │  【★重点】[定义，保留英文术语按语言模式标注]
│  │  │  [中文阐述，来自笔记/教材]
│  │  │
│  │  │  ### 2. 制度原理与体系
│  │  │  | 对比维度 | A | B |                               ← 概念对比表
│  │  │  |---------|---|---|
│  │  │  | ... | ... | ... |
│  │  │
│  │  │  ### 3. 案例与适用
│  │  │  **参考案例：** [案例名]——[一句话法理结论]
│  │  │  [案例嵌入在对应考点下，不单独列案例章]
│  │  │
│  │  │  ### 4. 考试提示
│  │  │  **【历年真题】** [出题规律+题型提示]
│  │  │  **【易错点】** [常见错误+避坑提示]
│  │  │  ```
│  │  │
│  │  ├─ 源材料引用规则：
│  │  │  ├─ 课程笔记 → 中文阐述主体（不要直接复制，重组为复习语言）
│  │  │  ├─ 英文教材 → 关键术语原文引用（按 [0.6] 语言模式决定标注方式）
│  │  │  ├─ 案例原文 → 提炼法理，不照搬全部事实
│  │  │  └─ 往年题 → 出题规律提示，不照搬原题
│  │  │
│  │  ├─ 上下文管理：
│  │  │  ├─ 每个考点独立处理，不跨考点混合
│  │  │  ├─ 如果单考点源材料超过 60% 上下文窗口 → 启动 chunk_manager
│  │  │  └─ 全稿按章拆分，每个 section 独立 .md
│  │  │
│  │  └─ 输出：`{课程}/review/section_01.md ... section_NN.md`
│  │     每章一个文件（即使该章有多个考点也合并在一章内）
│  │
│  ├─ [7.4] 质量检查
│  │  │
│  │  ├─ 逐考点检查清单：
│  │  │  ├─ [ ] 每个【必考】考点篇幅 ≥ 150 行
│  │  │  ├─ [ ] 每个【★重点】考点篇幅 ≥ 80 行
│  │  │  ├─ [ ] 全稿总行数 3000-5000（60-100 页 A4）
│  │  │  ├─ [ ] 英文术语首次出现有标注（按 language_mode）
│  │  │  ├─ [ ] 案例嵌入在对应考点下（非独立案例章）
│  │  │  ├─ [ ] 没有"不考"章节的冗余内容
│  │  │  ├─ [ ] 表格完整（表头+表体齐全）
│  │  │  └─ [ ] 跨章引用正确（wikilink 指向存在）
│  │  │
│  │  ├─ 不通过的处理：
│  │  │  ├─ 篇幅不足 → 回到 [7.3] 对该考点扩充
│  │  │  ├─ 篇幅过大（全稿 > 5000 行）→ 对【了解】考点精简
│  │  │  └─ 格式问题 → 逐项修复
│  │  │
│  │  └─ 全稿密度自查通过 → [7.5]
│  │
│  ├─ [7.5] 合并输出
│  │  │
│  │  ├─ 合并所有 section → `{课程}/复习材料_终稿.md`
│  │  │  ├─ 纯拼接（不重新格式化）
│  │  │  ├─ 添加总目录页（含各章链接）
│  │  │  └─ 添加尾页：考点覆盖统计 + 源材料清单
│  │  │
│  │  ├─ 按 Phase 5 选择的格式输出：
│  │  │  ├─ MD（默认，Obsidian 兼容）
│  │  │  ├─ HTML（含侧边栏目录+打印样式）
│  │  │  ├─ PDF（MD → HTML → WeasyPrint）
│  │  │  └─ DOCX（python-docx 渲染，保留标题层级）
│  │  │
│  │  ├─ 文件管理：
│  │  │  ├─ 保留单章文件（`review/section_*.md`，方便单独复习）
│  │  │  ├─ 保留 topic_map.json（下次更新复习稿时可复用）
│  │  │  └─ 清理旧版本：如果之前生成过复习稿，覆盖前先备份到 `review/_archive/`
│  │  │
│  │  └─ 输出成功 → [7.6]
│  │
│  └─ [7.6] 复习报告
│     │
│     └─ 生成复习报告（追加到导入报告后）：
│        | 指标 | 数值 |
│        |------|------|
│        | 考试范围 | {N} 章，{M} 个考点 |
│        | 【必考】考点 | {N} 个（占 {X}% 篇幅） |
│        | 【★重点】考点 | {N} 个（占 {X}% 篇幅） |
│        | 【了解】考点 | {N} 个（占 {X}% 篇幅） |
│        | 跳过章节 | {list or "无"} |
│        | 引用案例 | {N} 则 |
│        | 往年题覆盖 | {N}/{M} 考点有往年题对应 |
│        | 全稿总行数 | {N} 行（约 {X} 页 A4） |
│        | 语言模式 | {bilingual_zh/bilingual_en/zh_only/en_only} |
│        | 输出格式 | {MD/HTML/PDF/DOCX} |
│        | 复习稿路径 | `{课程}/复习材料_终稿.md` |
│
└─ ERROR PATHS（任何阶段出错时的 safe fallback）
   ├─ Phase 0 路径不存在 → 告知 + 请求重新输入
   ├─ Phase 1 格式不支持 → 保留原文件 + 标记"需手动处理"
   ├─ Phase 1 OCR 失败 → 保留原图 + 标记"OCR失败" + 建议安装 Tesseract/EasyOCR
   ├─ Phase 1 大文件无法分段 → 截取前 60% + 标记"文件过大，仅处理前段"
   ├─ Phase 2 类型无法确定 → 默认 lecture_notes + 标记"类型待确认"
   ├─ Phase 3 归属无法确定 → 标记"待分类" + 用户后续补充
   ├─ Phase 4 目录创建失败 → 检查权限 + 建议更换输出路径
   ├─ Phase 5 格式生成失败 → 降级到 MD（兜底格式）
   ├─ Phase 7 无 syllabus/key_points → 从笔记标题自动生成 topic_map（降级模式）
   ├─ Phase 7 源材料不足 → 标记 [缺源: 第X章]，仅生成已有章节
   ├─ Phase 7 全稿过短 → 不强制灌水，标记"内容偏少，建议补充源材料"
   └─ 全局：任何步骤单个文件失败 → 跳过该文件 + 继续处理其余 + 汇总报告列出全部失败项
```

---

## 工具集参考

### `tools/file_finder.py`
跨平台微信/QQ 文件自动发现：
```
python tools/file_finder.py --platform wechat          # 自动发现微信下载文件
python tools/file_finder.py --platform qq              # 自动发现QQ下载文件
python tools/file_finder.py --scan ~/Downloads         # 扫描指定目录
python tools/file_finder.py --scan-all                  # 通用扫描全部常见下载位置
```
读取 `config/platform_paths.json` 获取路径定义。
输出 JSON：`[{path, size, mtime, platform, source_dir}]`

### `tools/ocr_tool.py`
图像/扫描 PDF 文字识别：
```
python tools/ocr_tool.py --input scan.png --lang chi_sim+eng
python tools/ocr_tool.py --input scanned.pdf --mode pdf --pages 1-10
python tools/ocr_tool.py --input dir/ --batch             # 批量处理
```
自动降级：EasyOCR → Tesseract → 错误提示。
输出 JSON：`{text, confidence, engine, per_page: [{page, text, conf}]}`

### `tools/format_converter.py`
多格式 → 统一 Markdown 转换：
```
python tools/format_converter.py --input file.docx --mode docx2md
python tools/format_converter.py --input file.pptx --mode pptx2md
python tools/format_converter.py --input file.pdf --mode pdf2md
python tools/format_converter.py --input file.epub --mode epub2md
python tools/format_converter.py --input file.html --mode html2md
python tools/format_converter.py --input mubu.json --mode mubu2md
```
自动检测编码（UTF-8/GBK/GB2312）。
输出：纯文本 Markdown 字符串或写入文件。

### `tools/classifier.py`
资料类型 + 学科分类：
```
python tools/classifier.py --input text.md --mode material_type
python tools/classifier.py --input text.md --mode subject
python tools/classifier.py --input text.md --mode full    # 完整分类
```
读取 `config/material_types.json` 和 `config/subject_keywords.json`。
输出 JSON：`{material_type, confidence, subject, subject_confidence, quality_flags, exam_markers}`

### `tools/output_writer.py`
多格式输出生成：
```
python tools/output_writer.py --input notes/ --format md --output output/
python tools/output_writer.py --input notes/ --format html --template law_note
python tools/output_writer.py --input notes/ --format pdf
python tools/output_writer.py --input notes/ --format docx
python tools/output_writer.py --input notes/ --format all   # 一次全部
```

### `tools/chunk_manager.py`
大文件上下文窗口分段：
```
python tools/chunk_manager.py --input large_file.md --max-tokens 8000
python tools/chunk_manager.py --merge chunk_*.json --output merged.md
```
支持按章节边界智能分段 + 重叠区保留 + 合并时衔接验证。

---

## 导入报告模板

```markdown
## 📥 法学资料导入报告 — {YYYY-MM-DD HH:MM}

### 概览
| 指标 | 数值 |
|------|------|
| 来源路径 | {path} (平台: {wechat/qq/custom}) |
| 发现文件 | {total_found} |
| 用户确认 | {total_confirmed} |
| 格式分布 | {docx: N, pdf: N, pptx: N, ...} |
| OCR 处理 | {ocr_count} 个文件 (引擎: {easyocr/tesseract}) |
| 成功导入 | {success_count} |
| 跳过/失败 | {skip_count} |

### 分类结果
| # | 原始文件 | 资料类型 | 课程 | 类型置信度 | 重点标记 | 质量标记 | 输出路径 | 状态 |
|---|---------|---------|------|-----------|---------|---------|---------|------|
| 1 | 民法笔记.docx | 笔记 | 民法总论 | 高 | — | — | 民法总论/笔记/民法笔记.md | ✅ |
| 2 | 刑法重点.pdf | 重点 | 刑法分论 | 高 | 【★重点】【必考】 | — | 刑法分论/重点与考纲/刑法重点.md | ✅ |
| 3 | 扫描件.png | (OCR) | 待确认 | — | — | [存疑:来源不明] | — | ⚠️ 需手动确认 |

### 课程分布
| 课程（用户命名） | 新增文件 | 类型分布 | 关键词建议 |
|------|---------|---------|----------|
| 民法总论 | 3 | 笔记×2, 案例×1 | 民法学 |
| 刑法分论 | 2 | 重点×1, 往年题×1 | 刑法学 |

### 上下文窗口分段
| 文件 | Token 估算 | 需求 | 处理方式 |
|------|-----------|------|---------|
| 民法学大笔记.docx | 12,000 | > 8k 上下文 | 拆为 2 段，按章切分 ✅ |
| 其他文件 | < 4,000 | 正常 | 直接处理 ✅ |

### 索引更新
- [x] `{课程}概述.md` — 新增 {N} 条笔记链接
- [x] `_原始文件/原始文件索引.md` — 新增 {N} 条 source 映射
- [x] `_原始文件/项目进度.md` — 已更新

### 下一步建议
- 📝 本次导入课程：{用户命名的课程列表}
- ⚠️ 待手动处理：{count} 个文件（类型不明/归属不明/OCR低置信度）
- 📋 如需生成复习材料：`/law-review-generator` 或回复"生成复习 for {课程名}"
- 🔍 本次发现 {syllabus_count} 份考纲、{key_points_count} 份重点文件 → 建议立即用于复习生成
```

---

## 安全原则

1. **只读原始文件**：绝不移动/删除/修改用户原始文件。导入 = 复制+转换。
2. **新增不覆盖**：目标位置同名文件自动加序号后缀 `_2` `_3`。
3. **来源可追溯**：每个输出文件 frontmatter 记录原始路径。
4. **失败安全**：单文件失败不中断整体流程。
5. **确认门禁**：Phase 0（文件选择）、Phase 3（分类结果）两次用户确认。
6. **OCR 数据本地处理**：OCR 在本地运行，不上传图片到任何云端服务。

---

## 依赖

```
# 核心（必需）
pip install python-docx PyPDF2 python-pptx markdownify ebooklib chardet

# OCR（至少安装一个）
pip install easyocr                    # 推荐：GPU 加速，中英混合
# 或
pip install pytesseract                # 轻量：需额外安装 Tesseract 引擎
# Windows Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
# macOS: brew install tesseract tesseract-lang
# Linux: apt install tesseract-ocr tesseract-ocr-chi-sim

# 输出格式（可选）
pip install weasyprint                 # PDF 输出
pip install jinja2                     # HTML 模板渲染
```

---

## law-review-generator 已融合

原 `law-review-generator` skill 的完整工作流已内化为本 skill 的 **Phase 7: 复习资料生成**。

对已有用户的兼容性：
- 如果用户已导入过资料（Obsidian 中已有课程目录），直接说"生成复习 for 民法总论" → 跳过 Phase 0-6，直接进入 Phase 7
- 如果用户从零开始 → `/law-import` → 走完整 7 Phase 管线
- 旧的 `/law-review-generator` 触发词仍有效，自动路由到 Phase 7

### 独立调用 Phase 7（已有资料，只需复习生成）

如果用户已经在 Obsidian 中有整理好的课程目录（不管是之前用 law-import 导入的，还是手动整理的），可以跳过导入直接生成复习：

```
用户："帮我生成民法总论的复习资料"
       "把XX法笔记整理成复习稿"
       "期末了，帮我整理XX法"

Claude：
  1. 扫描 {课程} 目录下所有 .md 文件
  2. 自动识别 syllabus（含"考纲/大纲"关键词）→ topic_map 骨架
  3. 自动识别 key_points（含【★重点】标记）→ 权重补充
  4. 自动识别 past_exams（含"简答题/论述题/名词解释"）→ 频次统计
  5. 如无 syllabus → 从笔记的 H1/H2 标题自动生成 topic_map
  6. 进入 Phase 7.3 → 逐章生成复习稿
```

这样用户不需要先跑导入——如果资料已经在 Obsidian 里了，直接生成复习就行。

---

## 开源分发清单

```
law-import/
├── SKILL.md                    # 本文件：Claude Code skill 定义（完整工作流）
├── README.md                   # GitHub README：安装/使用/架构/贡献
├── LICENSE                     # MIT
├── requirements.txt            # Python 依赖
├── tools/
│   ├── file_finder.py         # 跨平台微信/QQ 文件发现
│   ├── ocr_tool.py            # OCR 引擎（EasyOCR/Tesseract 自动降级）
│   ├── format_converter.py    # 多格式 → 统一 MD 转换
│   ├── classifier.py          # 资料类型 + 学科分类器
│   ├── output_writer.py       # MD/HTML/PDF/DOCX 多格式输出
│   └── chunk_manager.py       # 大文件上下文窗口分段+合并
├── config/
│   ├── platform_paths.json    # 微信/QQ 跨平台路径定义
│   ├── subject_keywords.json  # 16 学科关键词词典
│   └── material_types.json    # 10 种资料类型检测规则
├── templates/
│   ├── course_moc_template.md     # {课程}概述.md 模板
│   ├── frontmatter_template.md
│   ├── html_template.html
│   └── output_templates/
├── tests/
│   ├── test_classifier.py
│   ├── test_format_converter.py
│   └── test_fixtures/         # 测试用样例文件
└── examples/
    ├── demo_wechat_import.md  # 微信导入演示
    └── screenshot_before_after.png
```
