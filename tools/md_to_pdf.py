#!/usr/bin/env python3
"""Convert review markdown to PDF using weasyprint."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

try:
    from weasyprint import HTML
except ImportError:
    print("Please install weasyprint: pip install weasyprint")
    sys.exit(1)

MD_FILE = Path(r'D:\环资法\环境资源法复习\review\复习材料_终稿.md')
PDF_FILE = Path(r'D:\环资法\环境资源法复习\review\环境资源法_期末复习材料.pdf')

if not MD_FILE.exists():
    print(f"Error: {MD_FILE} not found")
    sys.exit(1)

# Read markdown
md_content = MD_FILE.read_text('utf-8')
total_lines = len(md_content.splitlines())
print(f"读取：{MD_FILE}")
print(f"总行数：{total_lines}")
print(f"正在生成 PDF...")

# Create HTML with styling
html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<style>
@page {{
    size: A4;
    margin: 2cm 2.5cm;
    @bottom-center {{
        content: "第 " counter(page) " 页";
        font-size: 10pt;
        color: #666;
    }}
}}
body {{
    font-family: "SimSun", "Songti SC", "Noto Serif CJK SC", serif;
    font-size: 11pt;
    line-height: 1.8;
    color: #333;
}}
h1 {{
    font-size: 20pt;
    text-align: center;
    margin-top: 3cm;
    page-break-before: always;
}}
h2 {{
    font-size: 16pt;
    margin-top: 2em;
    color: #1a5276;
    border-bottom: 2px solid #1a5276;
    padding-bottom: 0.3em;
}}
h3 {{
    font-size: 13pt;
    margin-top: 1.5em;
    color: #2e86c1;
}}
h4 {{
    font-size: 11pt;
    margin-top: 1em;
    color: #555;
}}
table {{
    width: 100%;
    border-collapse: collapse;
    margin: 1em 0;
    font-size: 10pt;
}}
th, td {{
    border: 1px solid #999;
    padding: 6px 10px;
    text-align: left;
}}
th {{
    background-color: #2e86c1;
    color: white;
}}
tr:nth-child(even) {{
    background-color: #f2f8ff;
}}
code {{
    background-color: #f5f5f5;
    padding: 1px 4px;
    border-radius: 3px;
    font-family: monospace;
}}
blockquote {{
    border-left: 4px solid #2e86c1;
    margin: 1em 0;
    padding: 0.5em 1em;
    background-color: #f9f9f9;
}}
img {{
    max-width: 100%;
}}
strong {{
    color: #c0392b;
}}
em {{
    color: #555;
}}
ul, ol {{
    margin: 0.5em 0;
    padding-left: 2em;
}}
li {{
    margin: 0.3em 0;
}}
hr {{
    border: none;
    border-top: 1px solid #ddd;
    margin: 2em 0;
}}
.page-break {{
    page-break-before: always;
}}
</style>
</head>
<body>
<div id="content">
{md_content}
</div>
</body>
</html>"""

# Write HTML temp
html_file = PDF_FILE.with_suffix('.html')
html_file.write_text(html_content, 'utf-8')

try:
    HTML(str(html_file)).write_pdf(str(PDF_FILE))
    print(f"PDF 生成成功：{PDF_FILE}")
    import os
    size_kb = os.path.getsize(str(PDF_FILE)) / 1024
    print(f"文件大小：{size_kb:.1f} KB")
except Exception as e:
    print(f"PDF 生成失败：{e}")
    sys.exit(1)
