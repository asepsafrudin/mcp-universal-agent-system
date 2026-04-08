#!/usr/bin/env python3
"""
SPM Parser v2 - Rule-based parser for "Surat Pernyataan Tanggung Jawab Belanja" documents.

Parses OCR text output into structured JSON with nested objects,
flat numeric fields, and proper entry separation.

Expected output format:
{
  "jenis_dokumen": "...",
  "nomor": "...",
  "satuan_kerja": {"kode": "...", "nama": "..."},
  "dipa": {"tanggal": "...", "nomor": "...", "revisi_ke": "..."},
  "klasifikasi_belanja": "...",
  "rincian_pembayaran": [...],
  "total_jumlah_rp": ...,
  "total_potongan_rp": ...,
  "keterangan": "...",
  "tempat_tanggal": "...",
  "penandatangan": {...}
}

Usage:
    python3 spm_parser.py --input <path_to_ocr_md_or_txt> --output <path_to_json>
    python3 spm_parser.py --demo
"""
import json
import re
import argparse
from pathlib import Path


# ============================================================
# OCR Correction Rules
# ============================================================

KNOWN_CORRECTIONS = {
    "Sisco8H": "Sisco, SH",
    "DITJFN": "DITJEN",
    "S. KOm": "S.Kom",
    "Kode Satuan Kera": "Kode Satuan Kerja",
}


def apply_known_corrections(text: str) -> str:
    """Apply known OCR typo corrections."""
    for wrong, right in KNOWN_CORRECTIONS.items():
        text = text.replace(wrong, right)
    return text


def fix_rupiah_amount(value: str) -> str:
    """Fix common OCR errors: 11:026.000 -> 11.026.000"""
    return re.sub(r'(\d):(\d{3})', r'\g<1>.\2', value)


def to_int_rupiah(value: str) -> int:
    """Convert string like '5.513.000' to int 5513000."""
    if not value:
        return 0
    fixed = fix_rupiah_amount(value.strip())
    cleaned = fixed.replace(".", "").replace(",", "")
    try:
        return int(cleaned)
    except ValueError:
        return 0


# ============================================================
# Extraction Functions
# ============================================================

def extract_after_label(text: str, label: str) -> str:
    """Extract value after label, supporting both same-line and next-line ':'."""
    # Try next-line pattern: "Label\n: value"
    p = re.compile(label + r'\s*\n\s*:\s*(.+?)(?:\n|$)', re.IGNORECASE)
    m = p.search(text)
    if m:
        return m.group(1).strip()
    # Try same-line pattern: "Label : value"
    p2 = re.compile(label + r'\s*:\s*(.+?)(?:\n|$)', re.IGNORECASE)
    m2 = p2.search(text)
    if m2:
        return m2.group(1).strip()
    return ""


def extract_header(text: str) -> dict:
    """Parse document header fields."""
    # Nomor surat
    no_surat = ""
    m = re.search(r'Nomor\s*:\s*(.+)', text)
    if m:
        no_surat = m.group(1).strip()
        # Fix I11 -> III
        no_surat = re.sub(r'\bI11\b', 'III', no_surat)

    # Satuan kerja
    kode_sk = extract_after_label(text, r'Kode\s+Satuan\s+Kerj[aoa]')
    nama_sk = extract_after_label(text, r'Nama\s+Satuan\s+Kerja')

    # Revisi ke (separate extraction — must happen before DIPA label search)
    rm = re.search(r'Revisi\s+ke\s+(\d+)', text)
    revisi_ke = rm.group(1) if rm else ""

    # DIPA
    dipa_raw = extract_after_label(text, r'Tgl/No\.\s*DIPA[\w\s]*')
    if dipa_raw:
        # Format: "21 Februari 2025/010.06.1.039729/2025"
        parts = dipa_raw.split("/")
        tgl_dipa = parts[0].strip()
        no_dipa = "/".join(p for p in parts[1:] if p).strip().rstrip("/")
    else:
        # Try alternate without revisi in label
        dipa_raw2 = extract_after_label(text, r'Tgl/No\.\s*DIPA')
        if dipa_raw2:
            parts = dipa_raw2.split("/")
            tgl_dipa = parts[0].strip()
            no_dipa = "/".join(p for p in parts[1:] if p).strip().rstrip("/")

    # Klasifikasi belanja
    kb = extract_after_label(text, r'Klasifikasi\s+Belanj[aoa]')

    return {
        "nomor": no_surat,
        "satuan_kerja": {
            "kode": kode_sk,
            "nama": nama_sk,
        },
        "dipa": {
            "tanggal": tgl_dipa,
            "nomor": no_dipa,
            "revisi_ke": revisi_ke,
        },
        "klasifikasi_belanja": kb,
    }


def find_entry_boundaries(lines: list) -> list:
    """
    Find boundaries of payment entries.
    Each entry starts with:  seq_no (alone) -> akun (6 digits)
    Returns list of (seq_no, start_line_idx, end_line_idx)
    """
    boundaries = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if re.match(r'^\d+$', stripped) and len(stripped) <= 2:
            seq_no = int(stripped)
            # Look ahead: next line should be 6-digit account number
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if re.match(r'^\d{6}$', next_line):
                    # Found entry start
                    prev_end = boundaries[-1][-1] if boundaries else -1
                    boundaries.append((seq_no, i))  # seq_no, start_idx
                    i += 2
                    continue
            else:
                # Last entry might not have following content
                pass
        i += 1

    # Add end indices
    result = []
    for idx, (seq_no, start_idx) in enumerate(boundaries):
        if idx + 1 < len(boundaries):
            end_idx = boundaries[idx + 1][1] - 1  # one before next entry
        else:
            end_idx = len(lines) - 1
        result.append((seq_no, start_idx, end_idx))

    return result


def extract_rincian(text: str) -> tuple:
    """
    Extract payment entries from table section.
    Returns (rincian_list, after_entries_text).
    """
    lines = text.split('\n')

    # Find table start (after column headers)
    table_start = 0
    for i, line in enumerate(lines):
        # Look for "Uraian" header which is the last header column
        # We want the line AFTER "Rab" (which comes after "Uraian" in multi-line headers)
        # Actually, find "Kode Satuan Kerja" section end - before "Perundang-undangan"
        # Better approach: find "Uraian" then skip header lines
        if line.strip().lower() == 'uraian':
            # Headers can span multiple lines, find the end
            # Table data starts after: No, Akun, Penerima, Uraian, (Rp), Kehadiran, PPh, Januari-, Februari
            table_start = i + 1
            break

    # Find entry lines (from table_start onwards)
    # Strategy: collect everything from table_start until "PEJABAT PEMBUAT KOMITMEN"
    content_lines = []
    for i in range(table_start, len(lines)):
        line = lines[i]
        if re.match(r'^PEJABAT\s+', line) or re.match(r'^SEKRETARIAT', line):
            break
        content_lines.append(line)
    else:
        # If not found, try from "Jakarta, " backwards
        for i in range(table_start, len(lines)):
            if lines[i].startswith("Jakarta,"):
                content_lines = lines[table_start:i]
                break

    # Find entry boundaries
    entry_bounds = find_entry_boundaries(content_lines)

    entries = []
    for seq_no, start_idx, end_idx in entry_bounds:
        entry_lines = content_lines[start_idx:end_idx + 1]
        entry = parse_single_entry(seq_no, entry_lines)
        entries.append(entry)

    return entries


def parse_single_entry(seq_no: int, lines: list) -> dict:
    """Parse a single payment entry."""
    akun = ""
    nama_penerima = ""  # Extract from first line after akun

    # First line is seq_no, second is akun
    if len(lines) >= 2:
        if re.match(r'^\d{6}$', lines[1].strip()):
            akun = lines[1].strip()

    # Penerima is typically right after akun on same line or next few chars
    # In this OCR format, the structure is: seq_no\nakun\nnama_penerima\nuraian...
    # But OCR often splits so we need to check
    if len(lines) > 2:
        third = lines[2].strip()
        # Check if it looks like a name (starts with capital letter, not a number or "Perundang")
        if third and len(third) > 3 and not re.match(r'^\d', third) and not third.startswith(('Perundang', 'Untuk')):
            nama_penerima = third
            # The rest is uraian
            uraian_start = 3
        else:
            uraian_start = 2
    else:
        uraian_start = 2

    # Collect uraian: from uraian_start until we hit a number (rupiah amount) or end marker
    uraian_parts = []
    jumlah_list = []
    stop_uraian = False  # Flag to stop collecting uraian after first "Jumlah"
    i = uraian_start
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # Stop markers: these indicate end of table section
        if line.startswith("Jumlah") or line.startswith("Bukti-bukti") or \
           line.startswith("Demikian") or line.startswith("Jakarta"):
            # Don't add to uraian — this is footer text
            break

        # Check if it's a rupiah amount
        if re.match(r'^[\d][\d.:.]+$', line):
            jumlah_list.append(fix_rupiah_amount(line))
            stop_uraian = True
            i += 1
            continue

        # If we've stopped uraian collection, only collect amounts
        if stop_uraian:
            if re.match(r'^[\d][\d.:.]+$', line):
                jumlah_list.append(fix_rupiah_amount(line))
            # skip other text after stop
            i += 1
            continue

        # It's part of uraian
        uraian_parts.append(line)
        i += 1

    uraian = " ".join(uraian_parts).strip()

    # Determine jumlah, potongan based on values
    # Typically: first number = jumlah, second = potongan (either kehadiran or PPh)
    jumlah_rp = ""
    potongan_kehadiran = 0
    potongan_pph = 0

    if len(jumlah_list) >= 1:
        jumlah_rp = jumlah_list[0]
    if len(jumlah_list) >= 2:
        # Second amount is typically PPh for this document type
        potongan_pph = to_int_rupiah(jumlah_list[1])

    # Convert jumlah to int
    jumlah_int = to_int_rupiah(jumlah_rp)

    # Try to extract penerima name from uraian if not found
    if not nama_penerima and uraian:
        # Look for "Untuk Pembayaran ... Nama_Penerima" pattern
        nama_match = re.search(r'(?:Untuk\s+Pembayaran\s+\S+\s+)([A-Z][A-Za-z]+(?:,\s*\S+\s*(?:,\s*\S+)?))', uraian)
        if nama_match:
            nama_penerima = nama_match.group(1).strip()
        # Try "Untuk Pembayaran Tenaga Pendukung Teknis Nama_Penerima"
        if not nama_penerima:
            nm2 = re.search(r'Teknis\s+Perundang-undangan\s*\(?([A-Z][A-Za-z]+(?:,\s*\S+(?:,\s*\S+)?)?)', uraian)
            if nm2:
                nama_penerima = nm2.group(1).strip()

    return {
        "no": seq_no,
        "akun": akun,
        "penerima": nama_penerima,
        "uraian": uraian,
        "jumlah_rp": jumlah_int,
        "potongan_kehadiran_rp": potongan_kehadiran,
        "potongan_pph_rp": potongan_pph,
    }


def extract_total(rincian: list) -> int:
    """Calculate total from rincian entries."""
    return sum(e["jumlah_rp"] for e in rincian)


def extract_total_potongan(rincian: list) -> int:
    """Calculate total potongan from rincian entries."""
    return sum(e["potongan_kehadiran_rp"] + e["potongan_pph_rp"] for e in rincian)


def extract_keterangan(text: str) -> str:
    """Extract 'keterangan' paragraph (starts with 'Bukti-bukti pengeluaran...')."""
    m = re.search(r'(Bukti-bukti\s+pengeluaran\s+anggaran.+?)\s*\n\s*Demikian', text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip().replace('\n', ' ')
    return ""


def extract_tempat_tanggal(text: str) -> str:
    """Extract place and date: 'Jakarta, 3 Maret 2025'."""
    m = re.search(r'((\w+),\s*(\d+\s+\w+\s+\d{4}))', text)
    if m:
        result = m.group(1).strip()
        # Remove leading/trailing whitespace and newlines
        result = re.sub(r'\s+', ' ', result).strip()
        return result
    return ""


def extract_penandatangan(text: str) -> dict:
    """Extract signatory info."""
    jabatan = ""
    nama = ""
    nip = ""

    # Find "PEJABAT PEMBUAT KOMITMEN" section
    pm = re.search(r'PEJABAT\s+PEMBUAT\s+KOMITMEN\s*\n(.+)', text)
    if pm:
        jabatan_line = pm.group(1).strip().rstrip(',').rstrip('.')
        instansi_match = re.search(r'(SEKRETARIAT\s+DITJEN\s+BINA\s+PEMBANGUNAN\s+DAERAH(?:,)?)', text)
        if instansi_match:
            jabatan = f"PEJABAT PEMBUAT KOMITMEN {instansi_match.group(1).rstrip(',')}".strip()
        else:
            jabatan = f"PEJABAT PEMBUAT KOMITMEN {jabatan_line}".strip()

    # Extract nama and jabatan separately
    # Find the full signature block
    sig_block = re.search(
        r'PEJABAT\s+PEMBUAT\s+KOMITMEN\s*\n(.+?)\n(.+?)\n(.+?)\nNIP\.?\s*([\d\s]+)',
        text, re.DOTALL
    )
    if sig_block:
        jabatan_line = sig_block.group(1).strip().rstrip(',')
        instansi_line = sig_block.group(2).strip().rstrip(',')
        nama_line = sig_block.group(3).strip()
        nip_val = sig_block.group(4).strip()
        nip_val = re.sub(r'\s{2,}', ' ', nip_val)

        jabatan = f"{jabatan_line} {instansi_line}".strip()
        nama = nama_line
        nip = nip_val
    else:
        # Fallback: try simpler pattern for nama
        nm = re.search(r'([A-Z][A-Z\s]+,\s*\S+[\s.]?\w*)\nNIP', text)
        if nm:
            nama = nm.group(1).strip()

    # Extract NIP
    np = re.search(r'NIP\.?\s*([\d\s]+)', text)
    if np:
        nip = np.group(1).strip()
        nip = re.sub(r'\s{2,}', ' ', nip)  # Clean up extra spaces but keep single space

    return {
        "jabatan": jabatan,
        "nama": nama,
        "nip": nip,
    }


# ============================================================
# Main Parser
# ============================================================

def parse_spm_document(text: str) -> dict:
    """Parse Surat Pernyataan Tanggung Jawab Belanja document."""
    text = apply_known_corrections(text)

    header = extract_header(text)
    rincian = extract_rincian(text)
    total_jumlah = extract_total(rincian)
    total_potongan = extract_total_potongan(rincian)
    keterangan = extract_keterangan(text)
    tempat_tanggal = extract_tempat_tanggal(text)
    penandatangan = extract_penandatangan(text)

    return {
        "jenis_dokumen": "Surat Pernyataan Tanggung Jawab Belanja",
        "nomor": header["nomor"],
        "satuan_kerja": header["satuan_kerja"],
        "dipa": header["dipa"],
        "klasifikasi_belanja": header["klasifikasi_belanja"],
        "rincian_pembayaran": rincian,
        "total_jumlah_rp": total_jumlah,
        "total_potongan_rp": total_potongan,
        "keterangan": keterangan,
        "tempat_tanggal": tempat_tanggal,
        "penandatangan": penandatangan,
    }


def extract_full_text_from_md(md_path: str) -> str:
    """Extract OCR text from markdown file."""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'```text\n([\s\S]*?)\n```', content)
    return match.group(1) if match else content


def main():
    parser = argparse.ArgumentParser(description='Parse SPM document from OCR output')
    parser.add_argument('--input', '-i', help='Path to OCR markdown/txt file')
    parser.add_argument('--output', '-o', help='Path to output JSON file')
    parser.add_argument('--demo', action='store_true', help='Run with demo data')
    args = parser.parse_args()

    if args.demo:
        input_path = "/home/aseps/MCP/xlsx-gdrive-workflow/arsip-2025/scan/arsip20260402_08370635.md"
        output_path = "/home/aseps/MCP/xlsx-gdrive-workflow/arsip-2025/scan/arsip20260402_08370635.json"
    elif args.input:
        input_path = args.input
        output_path = args.output or args.input.replace('.md', '.json').replace('.txt', '.json')
    else:
        parser.print_help()
        return

    print(f"Reading: {input_path}")
    full_text = extract_full_text_from_md(input_path)

    print("Parsing document...")
    result = parse_spm_document(full_text)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Output written to: {output_path}")
    print()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()