import sqlite3
import re
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for margin_name, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{margin_name}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

conn = sqlite3.connect('export/telegram_archive.db')
cursor = conn.cursor()

query = """
SELECT id, text FROM posts 
WHERE text LIKE '%❌%' AND (text LIKE '%⁉%' OR text LIKE '%❓%') AND text LIKE '%✅%'
ORDER BY id DESC
"""
cursor.execute(query)
rows = cursor.fetchall()

candidates = []
seen = set()

for pid, text in rows:
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    i = 0
    while i < len(lines):
        if lines[i].startswith('❌'):
            wrong_text = re.sub(r'^[❌\s"«]+|[»"\s]+$', '', lines[i]).strip()
            ru_text = ""
            correct_text = ""
            
            j = i + 1
            while j < len(lines) and not lines[j].startswith('❌'):
                if lines[j].startswith('⁉') or lines[j].startswith('❓'):
                    ru_text = re.sub(r'^[⁉❓\s"«]+|[»"\s]+$', '', lines[j]).strip()
                elif lines[j].startswith('✅'):
                    correct_text = re.sub(r'^[✅\s"«]+|[»"\s]+$', '', lines[j]).strip()
                j += 1
            
            # Keep only crisp, beautiful phrase pairs
            if wrong_text and correct_text and ru_text and wrong_text not in seen:
                if 2 < len(wrong_text) < 55 and 2 < len(ru_text) < 55 and 2 < len(correct_text) < 55:
                    if not any(stop in correct_text for stop in ["айтылады", "деген", "етістігі", "септікті"]):
                        seen.add(wrong_text)
                        candidates.append({
                            "id": pid,
                            "wrong": wrong_text,
                            "ru": ru_text,
                            "correct": correct_text
                        })
            i = j
        else:
            i += 1

print(f"Total curated clean candidates: {len(candidates)}")
selected = candidates[:30]

# Build Word Document
doc = Document()

for section in doc.sections:
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

# Title
title_p = doc.add_paragraph()
title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run_title = title_p.add_run("«Калькасыз қазақ тілі» — 30 мысал")
run_title.font.name = "Arial"
run_title.font.size = Pt(20)
run_title.font.bold = True
run_title.font.color.rgb = RGBColor(14, 116, 144)

# Subtitle
sub_p = doc.add_paragraph()
sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run_sub = sub_p.add_run("Назгүл Қожабектің @kalkastop Telegram арнасынан алынған қате калькалар мен олардың дұрыс баламалары")
run_sub.font.name = "Arial"
run_sub.font.size = Pt(11)
run_sub.font.italic = True
run_sub.font.color.rgb = RGBColor(100, 116, 139)

doc.add_paragraph()

# Table
table = doc.add_table(rows=1, cols=5)
table.alignment = WD_TABLE_ALIGNMENT.CENTER
table.autofit = False

headers = ["№", "❌ Қате (калька)", "⁉️ Орысша түпнұсқасы", "✅ Дұрыс баламасы", "Жазба #"]
widths = [Inches(0.4), Inches(2.3), Inches(2.1), Inches(2.4), Inches(0.8)]

hdr_cells = table.rows[0].cells
for i, h in enumerate(headers):
    hdr_cells[i].text = h
    hdr_cells[i].width = widths[i]
    set_cell_background(hdr_cells[i], "0F172A")
    set_cell_margins(hdr_cells[i], top=120, bottom=120, left=100, right=100)
    p = hdr_cells[i].paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in p.runs:
        r.font.name = "Arial"
        r.font.size = Pt(10)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

for idx, item in enumerate(selected, 1):
    row_cells = table.add_row().cells
    bg_color = "F8FAFC" if idx % 2 == 0 else "FFFFFF"
    
    # 0: No
    row_cells[0].text = str(idx)
    row_cells[0].width = widths[0]
    p0 = row_cells[0].paragraphs[0]
    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if p0.runs:
        p0.runs[0].font.name = "Arial"
        p0.runs[0].font.size = Pt(9.5)
        p0.runs[0].font.bold = True
        p0.runs[0].font.color.rgb = RGBColor(100, 116, 139)

    # 1: Wrong
    row_cells[1].text = item["wrong"]
    row_cells[1].width = widths[1]
    p1 = row_cells[1].paragraphs[0]
    if p1.runs:
        p1.runs[0].font.name = "Arial"
        p1.runs[0].font.size = Pt(9.5)
        p1.runs[0].font.bold = True
        p1.runs[0].font.color.rgb = RGBColor(225, 29, 72)

    # 2: Russian
    row_cells[2].text = item["ru"]
    row_cells[2].width = widths[2]
    p2 = row_cells[2].paragraphs[0]
    if p2.runs:
        p2.runs[0].font.name = "Arial"
        p2.runs[0].font.size = Pt(9.5)
        p2.runs[0].font.italic = True
        p2.runs[0].font.color.rgb = RGBColor(71, 85, 105)

    # 3: Correct
    row_cells[3].text = item["correct"]
    row_cells[3].width = widths[3]
    p3 = row_cells[3].paragraphs[0]
    if p3.runs:
        p3.runs[0].font.name = "Arial"
        p3.runs[0].font.size = Pt(9.5)
        p3.runs[0].font.bold = True
        p3.runs[0].font.color.rgb = RGBColor(13, 148, 136)

    # 4: Post ID
    row_cells[4].text = f"#{item['id']}"
    row_cells[4].width = widths[4]
    p4 = row_cells[4].paragraphs[0]
    p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if p4.runs:
        p4.runs[0].font.name = "Arial"
        p4.runs[0].font.size = Pt(9)
        p4.runs[0].font.color.rgb = RGBColor(14, 116, 144)

    for cell in row_cells:
        set_cell_background(cell, bg_color)
        set_cell_margins(cell, top=100, bottom=100, left=100, right=100)

doc.add_paragraph()

# Footer note
footer_p = doc.add_paragraph()
r_ft = footer_p.add_run("Дереккөз: ")
r_ft.font.name = "Arial"
r_ft.font.bold = True
r_ft.font.size = Pt(9.5)
r_ft2 = footer_p.add_run("Назгүл Қожабек, «Калькасыз қазақ тілі» Telegram арнасы (@kalkastop).\nОнлайн веб-архив: https://web-tau-ten-13.vercel.app")
r_ft2.font.name = "Arial"
r_ft2.font.size = Pt(9.5)
r_ft2.font.color.rgb = RGBColor(100, 116, 139)

output_path = "export/Калькасыз_қазақ_тілі_30_мысал.docx"
doc.save(output_path)
print(f"Successfully saved Word document to: {output_path}")

# Copy to web/public so it's also directly downloadable from the website!
import shutil
shutil.copy(output_path, "web/public/kalkasyz_qazaq_tili_30_mysal.docx")
print("Also copied to web/public/kalkasyz_qazaq_tili_30_mysal.docx")

import json
with open("export/selected_30_examples.json", "w", encoding="utf-8") as f:
    json.dump(selected, f, ensure_ascii=False, indent=2)

