"""
render_pdf.py
-------------
Renders the predicted question paper blueprint JSON into an authentic,
officially styled JNTUH examination paper PDF.
"""

import json
import subprocess
import os
from pathlib import Path

BLUEPRINT_PATH = Path("JAVA_sample-engine/output/predicted_paper_blueprint.json")
HTML_OUT_PATH  = Path("JAVA_sample-engine/output/predicted_java_paper.html")
PDF_OUT_DIR    = Path("JAVA_sample-engine/output")
PDF_FINAL_PATH = Path("JAVA_sample-engine/output/predicted_java_paper.pdf")

def generate_jntuh_html(bp: dict) -> str:
    subject = bp.get("subject", "OBJECT ORIENTED PROGRAMMING THROUGH JAVA").upper()
    reg = bp.get("regulation", "R22")
    max_marks = bp.get("total_marks", 60)
    part_a = bp.get("part_a", [])
    part_b = bp.get("part_b", [])

    char_labels = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
    part_a_rows = ""
    for idx, q in enumerate(part_a):
        label = char_labels[idx] if idx < len(char_labels) else f"({idx+1})"
        part_a_rows += f"""
        <tr>
            <td style="width: 5%; vertical-align: top; font-weight: bold;">1.{label})</td>
            <td style="width: 85%; vertical-align: top;">{q['text']}</td>
            <td style="width: 10%; vertical-align: top; text-align: right; font-weight: bold;">[{q['marks']}]</td>
        </tr>
        """

    part_b_sections = ""
    for pair in part_b:
        u = pair["unit"]
        q_num_a = u * 2
        q_num_b = u * 2 + 1
        
        # Choice I
        choice_i_rows = ""
        for idx, q in enumerate(pair["choiceI_questions"]):
            sub_label = f"{chr(97 + idx)}) " if len(pair["choiceI_questions"]) > 1 else ""
            choice_i_rows += f"""
            <div style="margin-bottom: 6px; display: flex; justify-content: space-between;">
                <span style="width: 90%;">{sub_label}{q['text']}</span>
                <span style="width: 10%; text-align: right; font-weight: bold;">[{q['marks']}]</span>
            </div>
            """

        # Choice II
        choice_ii_rows = ""
        for idx, q in enumerate(pair["choiceII_questions"]):
            sub_label = f"{chr(97 + idx)}) " if len(pair["choiceII_questions"]) > 1 else ""
            choice_ii_rows += f"""
            <div style="margin-bottom: 6px; display: flex; justify-content: space-between;">
                <span style="width: 90%;">{sub_label}{q['text']}</span>
                <span style="width: 10%; text-align: right; font-weight: bold;">[{q['marks']}]</span>
            </div>
            """

        part_b_sections += f"""
        <div style="margin-top: 14px;">
            <div style="text-align: center; font-weight: bold; margin-bottom: 6px; text-decoration: underline;">
                UNIT - {u}
            </div>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 5%; vertical-align: top; font-weight: bold;">{q_num_a}.</td>
                    <td style="width: 95%;">{choice_i_rows}</td>
                </tr>
            </table>
            <div style="text-align: center; font-weight: bold; margin: 6px 0;">OR</div>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 5%; vertical-align: top; font-weight: bold;">{q_num_b}.</td>
                    <td style="width: 95%;">{choice_ii_rows}</td>
                </tr>
            </table>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{
        size: A4;
        margin: 15mm;
    }}
    body {{
        font-family: 'Times New Roman', Times, serif;
        color: #000;
        font-size: 11pt;
        line-height: 1.3;
        margin: 0;
        padding: 0;
    }}
    .header-table {{
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 8px;
    }}
    .uni-title {{
        text-align: center;
        font-size: 13pt;
        font-weight: bold;
        letter-spacing: 0.5px;
        margin-bottom: 2px;
    }}
    .exam-title {{
        text-align: center;
        font-size: 11pt;
        font-weight: bold;
        margin-bottom: 2px;
    }}
    .subject-title {{
        text-align: center;
        font-size: 12pt;
        font-weight: bold;
        margin-bottom: 2px;
    }}
    .branch-title {{
        text-align: center;
        font-size: 10pt;
        font-style: italic;
        margin-bottom: 8px;
    }}
    .meta-table {{
        width: 100%;
        font-weight: bold;
        border-top: 1.5px solid #000;
        border-bottom: 1.5px solid #000;
        padding: 4px 0;
        margin-bottom: 8px;
    }}
    .note {{
        font-size: 9.5pt;
        margin-bottom: 10px;
    }}
    .section-header {{
        text-align: center;
        font-weight: bold;
        font-size: 11pt;
        margin-top: 10px;
        margin-bottom: 6px;
        border-top: 1px solid #000;
        border-bottom: 1px solid #000;
        padding: 3px 0;
    }}
    .part-a-table {{
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 10px;
    }}
    .part-a-table td {{
        padding: 3px 2px;
    }}
    .footer {{
        text-align: center;
        margin-top: 18px;
        font-weight: bold;
        font-size: 11pt;
    }}
    .ht-box {{
        display: inline-block;
        border: 1px solid #000;
        width: 16px;
        height: 18px;
        margin-left: 2px;
    }}
</style>
</head>
<body>

<table class="header-table">
    <tr>
        <td style="font-weight: bold; font-size: 10pt;">Code No: 183AK</td>
        <td style="text-align: right; font-weight: bold; font-size: 10pt;">{reg}</td>
    </tr>
    <tr>
        <td colspan="2" style="text-align: right; padding-top: 4px;">
            <span style="font-size: 9pt; font-weight: bold; margin-right: 4px;">Hall Ticket No:</span>
            {"".join(['<span class="ht-box"></span>' for _ in range(10)])}
        </td>
    </tr>
</table>

<div class="uni-title">JAWAHARLAL NEHRU TECHNOLOGICAL UNIVERSITY HYDERABAD</div>
<div class="exam-title">B.Tech II Year I Semester Examinations, February/March - 2025</div>
<div class="subject-title">{subject}</div>
<div class="branch-title">(Common to Computer Science & Engineering, Information Technology)</div>

<table class="meta-table">
    <tr>
        <td>Time: 3 Hours</td>
        <td style="text-align: right;">Max. Marks: {max_marks}</td>
    </tr>
</table>

<div class="note">
    <strong>Note:</strong> This question paper contains two parts A and B.<br>
    i. Part A is compulsory which carries 10 marks. All questions in Part A wish to be answered continuously.<br>
    ii. Part B consists of 5 Units. Answer any one full question from each unit. Each question carries 10 marks and may have a, b as sub questions.
</div>

<div class="section-header">PART - A (10 &times; 1 = 10 Marks)</div>
<table class="part-a-table">
    {part_a_rows}
</table>

<div class="section-header">PART - B (5 &times; 10 = 50 Marks)</div>
{part_b_sections}

<div class="footer">---ooOoo---</div>

</body>
</html>
"""
    return html

def main():
    if not BLUEPRINT_PATH.exists():
        print(f"Error: Blueprint file {BLUEPRINT_PATH} not found. Please run Engine.lean first.")
        return

    with open(BLUEPRINT_PATH, "r", encoding="utf-8") as f:
        bp = json.load(f)

    html_content = generate_jntuh_html(bp)
    with open(HTML_OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Rendered intermediate HTML layout: {HTML_OUT_PATH}")

    # Convert HTML to PDF via headless LibreOffice
    print("Converting to PDF via LibreOffice...")
    cmd = [
        "libreoffice",
        "--headless",
        "--convert-to", "pdf",
        str(HTML_OUT_PATH),
        "--outdir", str(PDF_OUT_DIR)
    ]
    subprocess.run(cmd, check=True)
    print(f"\n[SUCCESS] Formally predicted JNTUH exam paper generated successfully at:")
    print(f"  --> {PDF_FINAL_PATH.resolve()}")

if __name__ == "__main__":
    main()
