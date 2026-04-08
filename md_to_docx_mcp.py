#!/usr/bin/env python3
"""md_to_docx_mcp.py

Skrip Python untuk mengonversi file Markdown (.md) menjadi Microsoft Word (.docx)
menggunakan utilitas yang sudah ada di *mcp-unified* (tools/office/docx_tools.py).

Fitur yang didukung:
- Paragraf biasa dan heading (h1‑h6)
- List bullet & numbered
- Tabel markdown
- Gambar/diagram (referensi file lokal)

Penggunaan:
    python md_to_docx_mcp.py <input.md> <output.docx>

Pastikan virtual environment dengan paket `markdown` dan `beautifulsoup4`
telah di‑install (sudah ada di ./venv).
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any

import markdown
from bs4 import BeautifulSoup

sys.path.append(str(Path(__file__).parent / "mcp-unified"))
from tools.office.docx_tools import write_docx, insert_image_docx, add_list_docx


def parse_markdown(md_text: str, base_path: Path) -> List[Dict[str, Any]]:
    """Ubah markdown menjadi struktur konten yang dapat dipakai oleh `write_docx`.
    Mengembalikan list of dict dengan kunci:
        - type: 'paragraph' | 'heading' | 'list' | 'table' | 'image'
        - data: tergantung tipe
    """
    html = markdown.markdown(md_text, extensions=["tables", "fenced_code", "codehilite"])
    soup = BeautifulSoup(html, "html.parser")
    content: List[Dict[str, Any]] = []

    for el in soup.contents:
        if el.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = int(el.name[1])
            content.append({"type": "heading", "level": level, "text": el.get_text()})
        elif el.name == "p":
            content.append({"type": "paragraph", "text": el.get_text()})
        elif el.name == "ul":
            items = [li.get_text() for li in el.find_all("li")]
            content.append({"type": "list", "style": "bullet", "items": items})
        elif el.name == "ol":
            items = [li.get_text() for li in el.find_all("li")]
            content.append({"type": "list", "style": "numbered", "items": items})
        elif el.name == "table":
            # Header
            header_cells = el.find("thead").find_all("th") if el.find("thead") else []
            header = [c.get_text().strip() for c in header_cells]
            rows: List[List[str]] = []
            for tr in el.find("tbody").find_all("tr"):
                rows.append([td.get_text().strip() for td in tr.find_all(["td", "th"])])
            if not header and rows:
                header = rows.pop(0)
            # Gabungkan header + rows menjadi tabel data
            table_data = [header] + rows if header else rows
            content.append({"type": "table", "data": table_data})
        elif el.name == "img":
            src = el.get("src")
            if src:
                img_path = (base_path / src).resolve()
                content.append({"type": "image", "path": str(img_path)})
        # ignore other tags (code, blockquote, etc.)
    return content


def build_docx(content: List[Dict[str, Any]], output_path: str) -> None:
    """Buat file DOCX menggunakan fungsi `write_docx` dan utilitas tambahan.
    """
    # `write_docx` menerima list of items dengan key 'type' dan 'data'.
    docx_items: List[Dict] = []
    for item in content:
        if item["type"] == "paragraph":
            docx_items.append({"type": "paragraph", "text": item["text"], "style": "Normal", "alignment": "LEFT"})
        elif item["type"] == "heading":
            docx_items.append({"type": "heading", "text": item["text"], "level": item["level"]})
        elif item["type"] == "list":
            # gunakan fungsi add_list_docx setelah dokumen dibuat
            # Simpan sementara untuk diproses terpisah
            pass
        elif item["type"] == "table":
            docx_items.append({"type": "table", "data": item["data"]})
        # gambar akan ditangani terpisah
    # Tulis dokumen dasar
    write_docx(output_path, docx_items)

    # Tambahkan list dan gambar secara terpisah
    for item in content:
        if item["type"] == "list":
            add_list_docx(output_path, items=item["items"], list_type=item["style"])
        elif item["type"] == "image":
            insert_image_docx(output_path, image_path=item["path"], paragraph_idx=None)


def main():
    if len(sys.argv) != 3:
        print("Usage: python md_to_docx_mcp.py <input.md> <output.docx>")
        sys.exit(1)
    md_path = Path(sys.argv[1])
    docx_path = sys.argv[2]
    if not md_path.is_file():
        print(f"File markdown tidak ditemukan: {md_path}")
        sys.exit(1)
    md_text = md_path.read_text(encoding="utf-8")
    content = parse_markdown(md_text, md_path.parent)
    build_docx(content, docx_path)
    print(f"Berhasil mengonversi '{md_path}' menjadi '{docx_path}'.")

if __name__ == "__main__":
    main()
