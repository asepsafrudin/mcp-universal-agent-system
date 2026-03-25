#!/usr/bin/env python3
"""
Document Management System - Configuration
==========================================
Konfigurasi sentral untuk Unified Document Index.
Mendukung multiple sources: OneDrive, Google Drive, Local.
"""

import os
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, field

# Base paths
BASE_DIR = Path("/home/aseps/MCP")
SRC_DIR = BASE_DIR / "src" / "document_management"
DATA_DIR = BASE_DIR / "data" / "document_management"
LOG_DIR = BASE_DIR / "logs" / "document_management"

# Database paths
SQLITE_PATH = DATA_DIR / "unified_index.db"
SCHEMA_PATH = SRC_DIR / "core" / "schema.sql"

# Processing directories
EXTRACTED_DIR = DATA_DIR / "extracted"
THUMBNAILS_DIR = DATA_DIR / "thumbnails"
CACHE_DIR = DATA_DIR / "cache"

# PostgreSQL Configuration
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', '5433')),
    'database': os.getenv('POSTGRES_DB', 'mcp_knowledge'),
    'user': os.getenv('POSTGRES_USER', 'mcp_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'mcp_password_2024'),
    'table': 'unified_documents'
}

# Telegram Configuration
TELEGRAM_CONFIG = {
    'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
    'admin_chat_ids': os.getenv('TELEGRAM_ADMIN_IDS', '').split(','),
    'webhook_url': os.getenv('TELEGRAM_WEBHOOK_URL', ''),
}

# Google Drive Configuration
GOOGLE_DRIVE_CONFIG = {
    'credentials_path': os.getenv('GDRIVE_CREDENTIALS', str(BASE_DIR / 'config' / 'gdrive_credentials.json')),
    'token_path': os.getenv('GDRIVE_TOKEN', str(DATA_DIR / 'gdrive_token.json')),
    'sync_folder_id': os.getenv('GDRIVE_FOLDER_ID', ''),
}

# OneDrive Configuration
ONEDRIVE_CONFIG = {
    'base_path': Path(os.getenv('ONEDRIVE_PATH', '/home/aseps/OneDrive_PUU')),
    'categories': ['PUU_2024', 'PUU_2025', 'PUU_2026'],
}

# MIME type mapping
MIME_TYPES = {
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.doc': 'application/msword',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.xls': 'application/vnd.ms-excel',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.ppt': 'application/vnd.ms-powerpoint',
    '.txt': 'text/plain',
    '.csv': 'text/csv',
    '.zip': 'application/zip',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.bmp': 'image/bmp',
    '.tiff': 'image/tiff',
    '.webp': 'image/webp',
}

# Supported extensions for processing
SUPPORTED_EXTENSIONS = {
    'document': ['.pdf', '.docx', '.doc', '.txt', '.csv'],
    'spreadsheet': ['.xlsx', '.xls', '.csv'],
    'presentation': ['.pptx', '.ppt'],
    'image': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'],
    'archive': ['.zip'],
}

# Government document patterns for auto-labeling
GOVERNMENT_PATTERNS = {
    'UU': {
        'patterns': [r'UU\s+Nomor\s+\d+\s+Tahun\s+\d+', r'Undang-Undang\s+Nomor\s+\d+'],
        'jenis': 'Undang-Undang',
        'category': 'PERATURAN_UU'
    },
    'PP': {
        'patterns': [r'PP\s+Nomor\s+\d+', r'Peraturan\s+Pemerintah\s+Nomor\s+\d+'],
        'jenis': 'Peraturan Pemerintah',
        'category': 'PERATURAN_PP'
    },
    'PERPRES': {
        'patterns': [r'Perpres\s+Nomor\s+\d+', r'Peraturan\s+Presiden\s+Nomor\s+\d+'],
        'jenis': 'Peraturan Presiden',
        'category': 'PERATURAN_PERPRES'
    },
    'PERMEN': {
        'patterns': [r'PERMEN[A-Z]+', r'Peraturan\s+Menteri'],
        'jenis': 'Peraturan Menteri',
        'category': 'PERATURAN_PERMEN'
    },
    'PERDA': {
        'patterns': [r'Perda\s+Nomor\s+\d+', r'Peraturan\s+Daerah\s+Nomor\s+\d+'],
        'jenis': 'Peraturan Daerah',
        'category': 'PERATURAN_PERDA'
    },
    'KEPMEN': {
        'patterns': [r'Kepmen[A-Z]+', r'Keputusan\s+Menteri'],
        'jenis': 'Keputusan Menteri',
        'category': 'KEPUTUSAN_KEPMEN'
    },
    'SE': {
        'patterns': [r'SE\s+[A-Z]+', r'Surat\s+Edaran'],
        'jenis': 'Surat Edaran',
        'category': 'SURAT_SE'
    },
    'SURAT': {
        'patterns': [r'Surat\s+[A-Za-z]+'],
        'jenis': 'Surat',
        'category': 'SURAT'
    },
    'MOU': {
        'patterns': [r'MOU', r'Memorandum\s+of\s+Understanding'],
        'jenis': 'MoU',
        'category': 'KERJASAMA_MOU'
    },
    'PKS': {
        'patterns': [r'PKS', r'Perjanjian\s+Kerja\s+Sama'],
        'jenis': 'PKS',
        'category': 'KERJASAMA_PKS'
    },
}

# Instansi patterns
INSTANSI_PATTERNS = {
    'KEMENKUMHAM': [r'KEMENKUMHAM', r'Kementerian\s+Hukum\s+dan\s+HAM'],
    'KEMENKEU': [r'KEMENKEU', r'Kementerian\s+Keuangan'],
    'KEMENPAN': [r'KEMENPAN', r'Kementerian\s+PANRB'],
    'KOMINFO': [r'KOMINFO', r'Kementerian\s+Komunikasi'],
    'SETNEG': [r'SETNEG', r'Sekretariat\s+Negara'],
    'BPK': [r'BPK', r'Badan\s+Pemeriksa\s+Keuangan'],
    'OJK': [r'OJK', r'Otoritas\s+Jasa\s+Keuangan'],
    'KEMENDAGRI': [r'KEMENDAGRI', r'Kementerian\s+Dalam\s+Negeri'],
}

@dataclass
class SourceConfig:
    """Configuration for a document source"""
    source_type: str  # 'onedrive', 'googledrive', 'local'
    source_name: str
    enabled: bool = True
    config: Dict = field(default_factory=dict)
    sync_interval: int = 3600  # seconds
    last_sync: str = None

@dataclass
class ProcessingConfig:
    """Configuration for document processing"""
    enable_ocr: bool = True
    enable_extraction: bool = True
    enable_classification: bool = True
    ocr_engine: str = 'paddleocr'  # 'paddleocr', 'tesseract', 'easyocr'
    max_file_size_mb: int = 100
    batch_size: int = 10
    supported_languages: List[str] = field(default_factory=lambda: ['id', 'en'])

@dataclass
class SearchConfig:
    """Configuration for search functionality"""
    enable_fulltext: bool = True
    enable_fuzzy: bool = True
    max_results: int = 50
    highlight_matches: bool = True

# Initialize directories
def setup_directories():
    """Create necessary directories"""
    for dir_path in [DATA_DIR, LOG_DIR, EXTRACTED_DIR, THUMBNAILS_DIR, CACHE_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
    return True

# Default configurations
DEFAULT_SOURCES = [
    SourceConfig(
        source_type='onedrive',
        source_name='OneDrive_PUU',
        config=ONEDRIVE_CONFIG
    ),
    SourceConfig(
        source_type='googledrive',
        source_name='Google_Drive',
        config=GOOGLE_DRIVE_CONFIG,
        enabled=False  # Enable manually after setup
    ),
]

DEFAULT_PROCESSING = ProcessingConfig()
DEFAULT_SEARCH = SearchConfig()

if __name__ == "__main__":
    setup_directories()
    print("✅ Directories setup complete")
    print(f"📁 Data dir: {DATA_DIR}")
    print(f"📁 Log dir: {LOG_DIR}")
    print(f"📁 Extracted dir: {EXTRACTED_DIR}")