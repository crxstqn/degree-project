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
    regex = r'^(?=(?:TITOLO\s+[IVXLCDM]+|Art\.\s*\d+))'
    blocks = re.split(regex, text, flags=re.MULTILINE)

    articles = []
    current_title = ""
    for block in blocks:
        block = block.strip()
        if block.startswith('TITOLO'):
            current_title = block.split('\n', 1)[0]
            continue
        if not block.startswith('Art'):
            continue

        lines = block.split('\n', 1)
        header = lines[0].strip()
        content = lines[1].strip() if len(lines) > 1 else ""

        match_num = re.search(r'(Art\.)\s*(\d+(\.\d+)?(-[a-z]+)?)', header)
        number = match_num.group(2) if match_num else ""

        articles.append({
            "document": document,
            "title": current_title,
            "number": number,
            "header": header,
            "text": content
        })

    return articles

def remove_duplicates(articles):
    seen = {}
    for a in articles:
        key = (a["document"], a["number"])
        if key not in seen:
            seen[key] = a
        else:
            if len(a["text"]) > len(seen[key]["text"]):
                seen[key] = a
    return list(seen.values())

def process_documents():
    paths = {
        "statuto":     ROOT / "data" / "raw" / "statuto.pdf",
        "regolamento": ROOT / "data" / "raw" / "regolamento.pdf"
    }

    output_dir = ROOT / "data" / "processed"
    all_articles = []

    for name, path in paths.items():
        text = pdf_to_string(str(path))
        articles = extract_articles(text, name)
        all_articles.extend(articles)

    all_articles = remove_duplicates(all_articles)
    output_json = output_dir / "processed_articles.json"
    with open(output_json, "w", encoding="utf-8") as f:
       json.dump(all_articles, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    process_documents()