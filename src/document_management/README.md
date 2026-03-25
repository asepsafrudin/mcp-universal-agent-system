# Document Management System (DMS/ECM)

Sistem manajemen dokumen terpadu untuk indexing, OCR, auto-labeling, dan pencarian dokumen dari multiple sources (OneDrive, Google Drive, Local).

## 📁 Struktur Folder

```
document_management/
├── core/                   # Core components
│   ├── config.py          # Konfigurasi
│   ├── schema.sql         # Database schema
│   └── database.py        # Database manager
├── connectors/            # Source connectors
│   ├── base_connector.py
│   ├── onedrive_connector.py
│   └── googledrive_connector.py
├── processors/            # Document processors
│   ├── classifier.py      # Auto-labeling
│   └── ocr_engine.py      # OCR & text extraction
├── telegram/              # Telegram bot
│   └── bot.py
└── indexer.py             # Main CLI
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Install dependencies
pip install paddleocr pdfplumber python-docx openpyxl pdf2image
pip install python-telegram-bot google-auth google-auth-oauthlib google-api-python-client

# Install poppler untuk PDF (Ubuntu/Debian)
sudo apt-get install poppler-utils
```

### 2. Konfigurasi

Set environment variables:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_ADMIN_IDS="your_chat_id"
export ONEDRIVE_PATH="/home/aseps/OneDrive_PUU"
```

### 3. Inisialisasi Database

```bash
cd src/document_management
python3 indexer.py --stats
```

### 4. Sync Dokumen

```bash
# Sync semua sources
python3 indexer.py --sync

# Sync specific source
python3 indexer.py --sync --source OneDrive_PUU

# Sync by type
python3 indexer.py --sync --type onedrive
```

### 5. Auto-Labeling

```bash
# Classify semua dokumen pending
python3 indexer.py --classify

# Limit jumlah dokumen
python3 indexer.py --classify --limit 50
```

### 6. Run Telegram Bot

```bash
python3 telegram/bot.py
```

## 📊 Database Schema

### Tabel Utama

| Tabel | Deskripsi |
|-------|-----------|
| `file_sources` | Konfigurasi sumber (OneDrive, Google Drive, Local) |
| `file_documents` | Index semua file |
| `document_content` | Hasil OCR & text extraction |
| `document_labels` | Auto-labeling (jenis, instansi, tahun, dll) |
| `government_metadata` | Metadata spesifik dokumen pemerintah |
| `telegram_uploads` | Log upload dari Telegram |
| `sync_log` | Log sinkronisasi |
| `document_fts` | Full-text search virtual table |

## 🔌 Connectors

### OneDrive Connector
- Index file lokal dari symlink
- Mendukung folder: PUU_2024, PUU_2025, PUU_2026
- Auto-sync dengan hash checking

### Google Drive Connector
- Menggunakan Google Drive API v3
- OAuth2 authentication
- Auto-export Google Workspace files

**Setup Google Drive:**
1. Buat project di Google Cloud Console
2. Enable Google Drive API
3. Download credentials.json
4. Jalankan: `python3 connectors/googledrive_connector.py`

## 🏷️ Auto-Labeling

Sistem mendeteksi otomatis:

### Jenis Dokumen
- **UU** - Undang-Undang
- **PP** - Peraturan Pemerintah
- **PERPRES** - Peraturan Presiden
- **PERMEN** - Peraturan Menteri (PERMENKUMHAM, PERMENKEU, dll)
- **PERDA** - Peraturan Daerah
- **KEPMEN** - Keputusan Menteri
- **SE** - Surat Edaran
- **MOU** - Memorandum of Understanding
- **PKS** - Perjanjian Kerja Sama

### Instansi
- KEMENKUMHAM, KEMENKEU, KEMENPAN
- KOMINFO, SETNEG, BPK, OJK, KEMENDAGRI

### Metadata yang Diekstrak
- Nomor dokumen
- Tahun
- Judul
- Tentang (subjek)

## 🤖 Telegram Bot Commands

| Command | Deskripsi |
|---------|-----------|
| `/start` | Mulai bot |
| `/help` | Bantuan |
| `/search <keyword>` | Full-text search |
| `/find jenis=X tahun=Y` | Filter search |
| `/stats` | Statistik database |
| `/recent` | 10 dokumen terbaru |
| `/status` | Status sistem |
| `/sync` | Trigger sync (admin only) |

### Upload Dokumen
Kirim file langsung ke bot:
- PDF, DOCX, XLSX, TXT
- Gambar (PNG, JPG) - akan di-OCR

## 🔍 Pencarian

### Full-Text Search
```bash
# Via CLI
python3 -c "from core.database import get_db; db = get_db(); print(db.search_documents('kepolisian'))"

# Via Telegram
/search UU Kepolisian
/search "peraturan pemerintah"
```

### Filter Search
```bash
# Via Telegram
/find jenis=UU tahun=2023
/find instansi=KEMENKUMHAM
/find category=PUU_2024
```

## 📝 OCR Engine

### Supported Formats
- **Native extraction**: PDF (text-based), DOCX, XLSX, TXT
- **OCR**: PDF (image-based), PNG, JPG, TIFF, BMP, WEBP

### Smart Processing
1. Coba native text extraction dulu (lebih cepat)
2. Fallback ke OCR jika diperlukan
3. Auto-detect language (Indonesia)

## 📈 Monitoring

### Statistics
```bash
python3 indexer.py --stats
```

Output:
- Total dokumen
- Dengan konten / OCR
- By status, source, category
- Top jenis dokumen

### Sync History
```bash
# Via database query
sqlite3 data/document_management/unified_index.db "SELECT * FROM sync_log ORDER BY started_at DESC LIMIT 5;"
```

## 🔧 Maintenance

### Reset Database
```bash
python3 indexer.py --reset
```

### Backup Database
```bash
cp data/document_management/unified_index.db backup/$(date +%Y%m%d)_unified_index.db
```

## 🛠️ Development

### Menambah Connector Baru

1. Buat class di `connectors/` inherit dari `BaseConnector`
2. Implement method: `connect()`, `disconnect()`, `list_files()`, `get_file()`, `file_exists()`, `get_file_hash()`
3. Register di `connectors/__init__.py`

### Menambah Pattern Labeling

Edit `core/config.py`:
```python
GOVERNMENT_PATTERNS['NEW_TYPE'] = {
    'patterns': [r'pattern1', r'pattern2'],
    'jenis': 'Nama Jenis',
    'category': 'KATEGORI'
}
```

## 📚 Dependencies

```
paddleocr>=2.7.0
pdfplumber>=0.10.0
python-docx>=0.8.11
openpyxl>=3.1.0
pdf2image>=1.16.0
python-telegram-bot>=20.0
google-auth>=2.22.0
google-auth-oauthlib>=1.0.0
google-api-python-client>=2.95.0
```

## 📄 License

Private - For internal use only