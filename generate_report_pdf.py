"""Script to compile REPORT.md into a professional 4-page REPORT.pdf using headless Edge."""
import os
import subprocess
from pathlib import Path

def generate_pdf():
    md_path = Path("REPORT.md")
    html_path = Path("REPORT.html")
    pdf_path = Path("report.pdf")
    pdf_upper_path = Path("REPORT.pdf")
    
    if not md_path.exists():
        print(f"Error: {md_path} not found.")
        return
        
    # Read markdown content
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Convert markdown to HTML (basic conversion for report)
    import re
    
    # Simple clean markdown to HTML conversion with rich styling
    html_body = md_text
    # Escape special characters
    # Headers
    html_body = re.sub(r"^# (.*?)$", r"<h1>\1</h1>", html_body, flags=re.MULTILINE)
    html_body = re.sub(r"^## (.*?)$", r"<h2>\1</h2>", html_body, flags=re.MULTILINE)
    html_body = re.sub(r"^### (.*?)$", r"<h3>\1</h3>", html_body, flags=re.MULTILINE)
    html_body = re.sub(r"^#### (.*?)$", r"<h4>\1</h4>", html_body, flags=re.MULTILINE)
    
    # Bold / Italic
    html_body = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", html_body)
    html_body = re.sub(r"\*(.*?)\*", r"<em>\1</em>", html_body)
    
    # Code blocks
    html_body = re.sub(r"```(.*?)```", r"<pre><code>\1</code></pre>", html_body, flags=re.DOTALL)
    html_body = re.sub(r"`([^`]+)`", r"<code>\1</code>", html_body)
    
    # Horizontal rules
    html_body = re.sub(r"^---$", r"<hr/>", html_body, flags=re.MULTILINE)
    
    # Process Tables
    def table_repl(match):
        lines = match.group(0).strip().split("\n")
        if len(lines) < 2:
            return match.group(0)
        headers = [c.strip() for c in lines[0].strip("|").split("|")]
        th_html = "".join(f"<th>{h}</th>" for h in headers)
        thead = f"<thead><tr>{th_html}</tr></thead>"
        
        rows = []
        for line in lines[2:]:
            cells = [c.strip() for c in line.strip("|").split("|")]
            td_html = "".join(f"<td>{c}</td>" for c in cells)
            rows.append(f"<tr>{td_html}</tr>")
        tbody = f"<tbody>{''.join(rows)}</tbody>"
        return f"<table class='data-table'>{thead}{tbody}</table>"

    html_body = re.sub(r"(\|.+?\|\n\|[-: |]+\|\n(?:\|.+?\|\n?)+)", table_repl, html_body)
    
    # Paragraphs and Lists
    paragraphs = []
    for block in html_body.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if block.startswith(("<h1", "<h2", "<h3", "<h4", "<pre", "<table", "<hr")):
            paragraphs.append(block)
        elif block.startswith(("- ", "1. ", "2. ", "3. ", "4. ", "5. ")):
            items = block.split("\n")
            li_html = "".join(f"<li>{re.sub(r'^[-0-9.]+\s*', '', item)}</li>" for item in items if item.strip())
            paragraphs.append(f"<ul>{li_html}</ul>")
        else:
            paragraphs.append(f"<p>{block}</p>")
            
    content = "\n".join(paragraphs)

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>VoiceOps 2026 Capstone Report - ZentroMart</title>
<style>
    @page {{
        size: A4;
        margin: 18mm 18mm 18mm 18mm;
        @bottom-right {{
            content: counter(page) " of " counter(pages);
        }}
    }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #1e293b;
        line-height: 1.5;
        font-size: 10pt;
        margin: 0;
        padding: 0;
    }}
    h1 {{
        color: #0f172a;
        font-size: 18pt;
        border-bottom: 2px solid #2563eb;
        padding-bottom: 6px;
        margin-top: 0;
        margin-bottom: 12px;
    }}
    h2 {{
        color: #1e3a8a;
        font-size: 13pt;
        border-bottom: 1px solid #cbd5e1;
        padding-bottom: 4px;
        margin-top: 16px;
        margin-bottom: 8px;
        page-break-after: avoid;
    }}
    h3 {{
        color: #1e293b;
        font-size: 11pt;
        margin-top: 12px;
        margin-bottom: 6px;
        page-break-after: avoid;
    }}
    p {{
        margin-top: 0;
        margin-bottom: 8px;
        text-align: justify;
    }}
    ul, ol {{
        margin-top: 0;
        margin-bottom: 8px;
        padding-left: 20px;
    }}
    li {{
        margin-bottom: 4px;
    }}
    pre {{
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        padding: 8px 12px;
        font-size: 8.5pt;
        overflow-x: auto;
        margin: 8px 0;
    }}
    code {{
        font-family: "Cascadia Code", Consolas, Monaco, monospace;
        background: #f1f5f9;
        padding: 1px 4px;
        border-radius: 3px;
        font-size: 9pt;
    }}
    table.data-table {{
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0 14px 0;
        font-size: 8.5pt;
        page-break-inside: avoid;
    }}
    table.data-table th {{
        background: #f1f5f9;
        color: #0f172a;
        border: 1px solid #cbd5e1;
        padding: 6px 8px;
        text-align: left;
        font-weight: 600;
    }}
    table.data-table td {{
        border: 1px solid #e2e8f0;
        padding: 5px 8px;
    }}
    table.data-table tr:nth-child(even) {{
        background: #f8fafc;
    }}
    hr {{
        border: 0;
        border-top: 1px solid #e2e8f0;
        margin: 14px 0;
    }}
    .badge {{
        display: inline-block;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 8pt;
        font-weight: bold;
    }}
    .badge-success {{
        background: #dcfce7;
        color: #166534;
    }}
    .page-break {{
        page-break-before: always;
    }}
</style>
</head>
<body>
{content}
</body>
</html>
"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)
        
    print(f"Generated {html_path}")
    
    # Convert HTML to PDF using msedge
    msedge_exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(msedge_exe):
        msedge_exe = "msedge"
        
    cmd = [
        msedge_exe,
        "--headless",
        "--disable-gpu",
        f"--print-to-pdf={pdf_path.resolve()}",
        "--no-pdf-header-footer",
        str(html_path.resolve())
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and pdf_path.exists():
        print(f"Successfully generated {pdf_path} ({pdf_path.stat().st_size} bytes)")
    else:
        print(f"PDF generation failed: {res.stderr}")

if __name__ == "__main__":
    generate_pdf()
