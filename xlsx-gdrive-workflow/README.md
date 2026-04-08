# XLSX GDrive Workflow MCP Server

## Struktur Data Ekstraksi SPTJB

Hasil ekstraksi dari gambar SPTJB disimpan dalam format JSON dengan struktur berikut:

### Struktur JSON Utama

```json
{
  "key": "arsip20260402_08370635_structured",
  "content": {
    "doc_id": "arsip20260402_08370635",
    "doc_type": "SPTJB",
    "nomor_surat": "002/F.2/LS/11172025",
    "satker": "...",
    "uraian": "SURAT PERNYATAAN TANGGUNG JAWAB BELANJA",
    "klasifikasi": "01/01/06/6112/EBA/522191",
    "extraction_date": "2026-04-02T...",
    "raw_ocr_full": "<full OCR text>",
    "sptjb": {
      "jenis_dokumen": "Surat Pernyataan Tanggung Jawab Belanja",
      "nomor": "002/F.2/LS/11172025",
      "satuan_kerja": {
        "kode": "039729",
        "nama": "DITJEN BINA BANGDA KEMENTERIAN DALAM NEGERI"
      },
      "dipa": {
        "tanggal": "21 Februari 2025",
        "nomor": "010.06.1.039729/2025",
        "revisi_ke": "01"
      },
      "klasifikasi_belanja": "01/01/06/6112/EBA/522191",
      "rincian_pembayaran": [
        {
          "no": 1,
          "akun": "522191",
          "penerima": "Yonatan Maryon Sisco, SH",
          "uraian": "Untuk Pembayaran Tenaga Pendukung...",
          "jumlah_rp": 5513000,
          "potongan_kehadiran_maret_rp": 0,
          "potongan_peh_rp": 0
        }
      ],
      "total_jumlah_rp": 5513000,
      "total_potongan_rp": 0,
      "keterangan": "Bukti-bukti pengeluaran...",
      "tempat_tanggal": "Jakarta, 3 Maret 2025",
      "penandatangan": {
        "jabatan": "PEJABAT PEMBUAT KOMITMEN",
        "nama": "LIA ARIFIYANI, S. Kom"
      }
    }
  }
}
```

### Ringkasan Kolom dalam `sptjb` Object

| Field | Tipe | Deskripsi | Contoh |
|-------|------|-----------|--------|
| `jenis_dokumen` | string | Jenis dokumen | "Surat Pernyataan Tanggung Jawab Belanja" |
| `nomor` | string | Nomor surat | "002/F.2/LS/11172025" |
| `satuan_kerja.kode` | string | Kode satker (DIPA) | "039729" |
| `satuan_kerja.nama` | string | Nama satker | "DITJEN BINA BANGDA KEMENTERIAN DALAM NEGERI" |
| `dipa.tanggal` | string | Tanggal DIPA | "21 Februari 2025" |
| `dipa.nomor` | string | Nomor DIPA | "010.06.1.039729/2025" |
| `dipa.revisi_ke` | string | Nomor revisi | "01" |
| `klasifikasi_belanja` | string | Kode klasifikasi | "01/01/06/6112/EBA/522191" |
| `rincian_pembayaran` | array | Daftar rincian | [...] |
| `rincian_pembayaran[].no` | int | Nomor urut | 1 |
| `rincian_pembayaran[].akun` | string | Kode akun | "522191" |
| `rincian_pembayaran[].penerima` | string | Nama penerima | "Yonatan Maryon Sisco, SH" |
| `rincian_pembayaran[].uraian` | string | Deskripsi pembayaran | "Untuk Pembayaran Tenaga..." |
| `rincian_pembayaran[].jumlah_rp` | int | Jumlah dalam Rupiah | 5513000 |
| `rincian_pembayaran[].potongan_kehadiran_maret_rp` | int | Potongan kehadiran | 0 |
| `rincian_pembayaran[].potongan_peh_rp` | int | Potongan PEH | 0 |
| `total_jumlah_rp` | int | Total semua rincian | 11026000 |
| `total_potongan_rp` | int | Total semua potongan | 13783 |
| `keterangan` | string | Catatan tambahan | "Bukti-bukti pengeluaran..." |
| `tempat_tanggal` | string | Tempat dan tanggal | "Jakarta, 3 Maret 2025" |
| `penandatangan.jabatan` | string | Jabatan penandatangan | "PEJABAT PEMBUAT KOMITMEN" |
| `penandatangan.nama` | string | Nama penandatangan | "LIA ARIFIYANI, S. Kom" |

## Files

### Parser dan Extractor
- `sptjb_parser.py` - Parser utama untuk ekstraksi SPTJB ke struktur JSON
- `re_ocr_full.py` - Re-OCR semua PNG + extract field dasar
- `extract_table.py` - Ekstraksi tabel (versi sederhana)
- `table_mapping.py` - Mapping tabel ke format rows untuk GSheets

### Mapping dan Transformasi
- `column_mapping.json` - Konfigurasi mapping kolom spreadsheet
- `mapping_engine.py` - Engine transformasi data ke spreadsheet
- `arkip_to_sheets.py` - Preview mapping ke sheet
- `sheet_append.py` - Append data ke GSheets

### Data Directories
- `arsip-2025/scan/` - File PNG hasil scan (sumber OCR)
- `arsip-extracted/` - File JSON dan MD hasil ekstraksi

## Usage

```bash
cd /home/aseps/MCP/xlsx-gdrive-workflow

# OCR ulang semua PNG dan extract semua field
python3 re_ocr_full.py

# Parse SPTJB ke struktur lengkap (jenis_dokumen, satuan_kerja, dipa, rincian, dll)
python3 sptjb_parser.py

# Preview data mapping ke spreadsheet
python3 arsip_to_sheets.py

# Preview mapping tabel detail
python3 table_mapping.py
```

## Column Mapping Spreadsheet (Main Sheet)

| Kolom | Header | Field JSON | Contoh |
|-------|--------|------------|--------|
| A | Boks | doc_id | arsip20260402_08370635 |
| C | KODE KLASIFIKASI | constant | 000.8 |
| D | NOMOR SURAT | nomor_surat | 002/F.2/LS/11172025 |
| E | URAIAN | uraian | SURAT PERNYATAAN TANGGUNG JAWAB BELANJA |
| F | KURUN WAKTU | extraction_date | 2026-04 |
| L | Klasifikasi | klasifikasi | 01/01/06/6112/EBA/522191 |
| O | UNIT PENGOLAH | satker | DITJEN BINA BANGDA KEMENTERIAN |