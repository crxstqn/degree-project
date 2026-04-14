# Copyright (C) 2026 Cristian Liporace
# Licensed under the GNU General Public License v3.0
# See LICENSE file for details.

import pdfplumber
import re
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent


def pdf_to_string(path_pdf):
    text_pages = []
    with pdfplumber.open(path_pdf) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_pages.append(text)

    full_text = "\n".join(text_pages)
    full_text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', full_text)
    full_text = re.sub(r'^\s*\d+\s*$\n?', '', full_text, flags=re.MULTILINE)
    return full_text


def extract_articles(text, document):
    regex = r'^(?=(?:TITOLO|Titolo\s+[IVXLCDM]+|Art\.|Articolo\s*\d+))'
    blocks = re.split(regex, text, flags=re.MULTILINE)

    articles = []
    current_title = ""
    for block in blocks:
        block = block.strip()
        if block.lower().startswith('titolo'):
            current_title = block.split('\n', 1)[0]
            continue
        if not block.startswith('Art') and not block.startswith('Articolo'):
            continue

        lines = block.split('\n', 1)
        header = lines[0].strip()
        content = lines[1].strip() if len(lines) > 1 else ""

        match_num = re.search(r'(Art\.|Articolo)\s*(\d+(\.\d+)?(-[a-z]+)?)', header)
        number = match_num.group(2) if match_num else ""

        paragraphs = re.split(r'^(?=\d+\.\s+)', content, flags=re.MULTILINE)
        for paragraph in paragraphs:
            if len(paragraph)>0:
                match_para = re.search(r'^(\d+)\.\s+', paragraph.strip())
                num_paragraph = match_para.group(1) if match_para else ""
                text_paragraph = re.sub(r'^(\d+)\.\s+', r'', paragraph.strip())
                text_paragraph = re.sub(r'\nCAPO\s+[IVXLCDM]+\s[-–]*\s+[\w+|\s|,|\\n]+', r'', text_paragraph)

                articles.append({
                    "document": document,
                    "title": current_title,
                    "number": number,
                    "header": header,
                    "paragraph": num_paragraph,
                    "text": text_paragraph
                })

    return articles

def remove_duplicates(articles):
    seen = {}
    for a in articles:
        if a["paragraph"] == "":
            continue
        key = (a["document"], a["number"], a["paragraph"])
        if key not in seen:
            seen[key] = a
        else:
            if len(a["text"]) > len(seen[key]["text"]):
                seen[key] = a
    return list(seen.values())

def process_documents():
    paths = {
        "statuto":     ROOT / "data" / "raw" / "statuto-unical.pdf",
        "regolamento": ROOT / "data" / "raw" / "regolamento-unical.pdf"
    }

    output_dir = ROOT / "data" / "processed"
    all_articles = []

    for name, path in paths.items():
        text = pdf_to_string(str(path))
        articles = extract_articles(text, name)
        all_articles.extend(articles)

    all_articles = remove_duplicates(all_articles)
    output_json = output_dir / "processed_articles_unical.json"
    with open(output_json, "w", encoding="utf-8") as f:
       json.dump(all_articles, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    process_documents()