-- Document Management System - Database Schema
-- Unified Index untuk OneDrive, Google Drive, dan Local files
-- Version: 1.0.0
-- Created: 2026-03-10

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- ============================================================================
-- TABEL SOURCES
-- ============================================================================
-- Menyimpan konfigurasi sumber dokumen (OneDrive, Google Drive, Local)
CREATE TABLE IF NOT EXISTS file_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('onedrive', 'googledrive', 'local')),
    source_name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(200),
    enabled BOOLEAN DEFAULT TRUE,
    config_json TEXT,  -- JSON configuration
    sync_interval INTEGER DEFAULT 3600,  -- seconds
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABEL DOKUMEN UTAMA
-- ============================================================================
CREATE TABLE IF NOT EXISTS file_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Source reference
    source_id INTEGER NOT NULL,
    external_id TEXT,  -- ID dari source (Google Drive file ID, path relatif, dll)
    
    -- File info
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,  -- Path relatif atau URL
    file_hash VARCHAR(64),
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    extension VARCHAR(20),
    
    -- Kategori & Organisasi
    category VARCHAR(50),  -- PUU_2024, PUU_2025, PUU_2026, PERATURAN, dll
    subcategory TEXT,      -- Subfolder atau subkategori
    
    -- Status processing
    status VARCHAR(20) DEFAULT 'indexed' 
        CHECK (status IN ('indexed', 'processing', 'processed', 'failed', 'archived')),
    processing_stage VARCHAR(30),  -- Stage terakhir yang dijalankan
    
    -- Timestamps
    file_created_at TIMESTAMP,   -- Original file creation time
    file_modified_at TIMESTAMP,  -- Original file modification time
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_processed_at TIMESTAMP,
    
    -- Audit
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(source_id, file_path),
    FOREIGN KEY (source_id) REFERENCES file_sources(id) ON DELETE CASCADE
);

-- ============================================================================
-- TABEL KONTEN & OCR
-- ============================================================================
CREATE TABLE IF NOT EXISTS document_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    
    -- Extracted content
    extracted_text TEXT,  -- Full text content
    text_extraction_method VARCHAR(50),  -- 'pdfplumber', 'python-docx', 'paddleocr', dll
    
    -- OCR specific
    ocr_required BOOLEAN DEFAULT FALSE,
    ocr_engine VARCHAR(50),  -- 'paddleocr', 'tesseract', dll
    ocr_confidence DECIMAL(4,3),  -- 0.000 - 1.000
    ocr_language VARCHAR(10),  -- 'id', 'en', 'id+en'
    
    -- Processing info
    extracted_at TIMESTAMP,
    processing_time_seconds REAL,
    error_message TEXT,
    
    FOREIGN KEY (document_id) REFERENCES file_documents(id) ON DELETE CASCADE,
    UNIQUE(document_id)
);

-- ============================================================================
-- TABEL LABELS (Auto & Manual)
-- ============================================================================
CREATE TABLE IF NOT EXISTS document_labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    
    -- Label info
    label_type VARCHAR(30) NOT NULL,  -- 'jenis_dokumen', 'instansi', 'tahun', 'tema', dll
    label_value VARCHAR(200) NOT NULL,
    label_display TEXT,  -- Display name (optional)
    
    -- Source & Confidence
    source VARCHAR(20) DEFAULT 'auto' CHECK (source IN ('auto', 'manual', 'ml', 'rule')),
    confidence DECIMAL(4,3),  -- 0.000 - 1.000 (untuk auto-labeling)
    
    -- Pattern matched (untuk debug)
    matched_pattern TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (document_id) REFERENCES file_documents(id) ON DELETE CASCADE,
    UNIQUE(document_id, label_type, label_value)
);

-- ============================================================================
-- TABEL METADATA PEMERINTAHAN
-- ============================================================================
CREATE TABLE IF NOT EXISTS government_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    
    -- Identifikasi dokumen pemerintah
    jenis_dokumen VARCHAR(100),  -- Undang-Undang, Peraturan Pemerintah, dll
    nomor_dokumen VARCHAR(50),   -- Nomor peraturan
    tahun_dokumen INTEGER,       -- Tahun
    
    -- Instansi
    instansi_pembuat VARCHAR(200),  -- Kemenkumham, Kemenkeu, dll
    instansi_tingkat VARCHAR(50),   -- Pusat, Provinsi, Kabupaten
    
    -- Deskripsi
    judul TEXT,
    tentang TEXT,  -- "Tentang ..."
    
    -- Status dokumen
    status_dokumen VARCHAR(50),  -- Berlaku, Dicabut, Diubah
    mengubah TEXT,  -- Referensi ke dokumen yang diubah
    dicabut_oleh TEXT,  -- Referensi ke dokumen yang mencabut
    
    -- Tanggal penting
    tanggal_ditetapkan DATE,
    tanggal_diundangkan DATE,
    tanggal_berlaku DATE,
    
    -- Lampiran
    berita_negara_no VARCHAR(50),
    tambahan_berita_negara VARCHAR(50),
    
    -- Metadata extraction
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence DECIMAL(4,3),
    
    FOREIGN KEY (document_id) REFERENCES file_documents(id) ON DELETE CASCADE,
    UNIQUE(document_id)
);

-- ============================================================================
-- TABEL TELEGRAM INTEGRATION
-- ============================================================================
CREATE TABLE IF NOT EXISTS telegram_uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    
    -- Telegram info
    chat_id BIGINT NOT NULL,
    message_id BIGINT,
    file_id TEXT,  -- Telegram file ID
    
    -- Upload info
    uploaded_by VARCHAR(100),  -- Username atau ID
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Processing status
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP,
    error_message TEXT,
    
    -- Forwarded to
    forwarded_to_source_id INTEGER,
    
    FOREIGN KEY (document_id) REFERENCES file_documents(id) ON DELETE SET NULL,
    FOREIGN KEY (forwarded_to_source_id) REFERENCES file_sources(id)
);

-- ============================================================================
-- TABEL SYNC LOG
-- ============================================================================
CREATE TABLE IF NOT EXISTS sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    source_id INTEGER,
    sync_type VARCHAR(20) NOT NULL CHECK (sync_type IN ('full', 'incremental', 'manual', 'scheduled')),
    
    -- Statistics
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    files_total INTEGER DEFAULT 0,
    files_new INTEGER DEFAULT 0,
    files_updated INTEGER DEFAULT 0,
    files_failed INTEGER DEFAULT 0,
    files_deleted INTEGER DEFAULT 0,
    
    -- Status
    status VARCHAR(20) DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed', 'partial')),
    error_message TEXT,
    log_details TEXT,  -- JSON log
    
    FOREIGN KEY (source_id) REFERENCES file_sources(id) ON DELETE SET NULL
);

-- ============================================================================
-- TABEL FULL-TEXT SEARCH VIRTUAL
-- ============================================================================
CREATE VIRTUAL TABLE IF NOT EXISTS document_fts USING fts5(
    content='document_content',
    content_rowid='document_id',
    extracted_text,
    tokenize='porter unicode61'
);

-- Triggers untuk maintain FTS index
CREATE TRIGGER IF NOT EXISTS document_content_ai AFTER INSERT ON document_content BEGIN
    INSERT INTO document_fts(rowid, extracted_text) VALUES (new.document_id, new.extracted_text);
END;

CREATE TRIGGER IF NOT EXISTS document_content_ad AFTER DELETE ON document_content BEGIN
    INSERT INTO document_fts(document_fts, rowid, extracted_text) VALUES ('delete', old.document_id, old.extracted_text);
END;

CREATE TRIGGER IF NOT EXISTS document_content_au AFTER UPDATE ON document_content BEGIN
    INSERT INTO document_fts(document_fts, rowid, extracted_text) VALUES ('delete', old.document_id, old.extracted_text);
    INSERT INTO document_fts(rowid, extracted_text) VALUES (new.document_id, new.extracted_text);
END;

-- ============================================================================
-- INDEXES
-- ============================================================================
-- Documents indexes
CREATE INDEX IF NOT EXISTS idx_doc_source ON file_documents(source_id);
CREATE INDEX IF NOT EXISTS idx_doc_category ON file_documents(category);
CREATE INDEX IF NOT EXISTS idx_doc_status ON file_documents(status);
CREATE INDEX IF NOT EXISTS idx_doc_extension ON file_documents(extension);
CREATE INDEX IF NOT EXISTS idx_doc_modified ON file_documents(file_modified_at);
CREATE INDEX IF NOT EXISTS idx_doc_hash ON file_documents(file_hash);
CREATE INDEX IF NOT EXISTS idx_doc_path ON file_documents(file_path);

-- Content indexes
CREATE INDEX IF NOT EXISTS idx_content_doc ON document_content(document_id);
CREATE INDEX IF NOT EXISTS idx_content_ocr ON document_content(ocr_required);

-- Labels indexes
CREATE INDEX IF NOT EXISTS idx_label_doc ON document_labels(document_id);
CREATE INDEX IF NOT EXISTS idx_label_type ON document_labels(label_type);
CREATE INDEX IF NOT EXISTS idx_label_value ON document_labels(label_value);
CREATE INDEX IF NOT EXISTS idx_label_source ON document_labels(source);

-- Government metadata indexes
CREATE INDEX IF NOT EXISTS idx_gov_jenis ON government_metadata(jenis_dokumen);
CREATE INDEX IF NOT EXISTS idx_gov_tahun ON government_metadata(tahun_dokumen);
CREATE INDEX IF NOT EXISTS idx_gov_instansi ON government_metadata(instansi_pembuat);
CREATE INDEX IF NOT EXISTS idx_gov_status ON government_metadata(status_dokumen);

-- Sync log indexes
CREATE INDEX IF NOT EXISTS idx_sync_source ON sync_log(source_id);
CREATE INDEX IF NOT EXISTS idx_sync_started ON sync_log(started_at);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Documents pending processing (OCR/Extraction)
CREATE VIEW IF NOT EXISTS pending_processing AS
SELECT 
    d.id,
    d.file_name,
    d.file_path,
    d.category,
    d.extension,
    d.mime_type,
    d.indexed_at,
    CASE 
        WHEN c.ocr_required IS NULL AND d.extension IN ('.pdf', '.png', '.jpg', '.jpeg') THEN 'ocr_needed'
        WHEN c.extracted_text IS NULL THEN 'extraction_needed'
        ELSE 'processed'
    END as processing_needed
FROM file_documents d
LEFT JOIN document_content c ON d.id = c.document_id
WHERE d.status IN ('indexed', 'processing')
AND (c.extracted_text IS NULL OR c.ocr_required IS NULL);

-- View: Documents with labels summary
CREATE VIEW IF NOT EXISTS document_summary AS
SELECT 
    d.id,
    d.file_name,
    d.file_path,
    d.category,
    d.status,
    d.file_size_bytes,
    d.indexed_at,
    s.source_name,
    s.source_type,
    (SELECT GROUP_CONCAT(label_value, ', ') 
     FROM document_labels 
     WHERE document_id = d.id AND label_type = 'jenis_dokumen') as jenis_dokumen,
    (SELECT GROUP_CONCAT(label_value, ', ') 
     FROM document_labels 
     WHERE document_id = d.id AND label_type = 'instansi') as instansi,
    (SELECT label_value 
     FROM document_labels 
     WHERE document_id = d.id AND label_type = 'tahun' LIMIT 1) as tahun,
    c.ocr_confidence,
    LENGTH(c.extracted_text) as text_length
FROM file_documents d
JOIN file_sources s ON d.source_id = s.id
LEFT JOIN document_content c ON d.id = c.document_id;

-- View: Statistics by source
CREATE VIEW IF NOT EXISTS source_stats AS
SELECT 
    s.id as source_id,
    s.source_name,
    s.source_type,
    s.enabled,
    COUNT(d.id) as total_files,
    SUM(CASE WHEN d.status = 'processed' THEN 1 ELSE 0 END) as processed_files,
    SUM(CASE WHEN d.status = 'indexed' THEN 1 ELSE 0 END) as pending_files,
    SUM(CASE WHEN d.status = 'failed' THEN 1 ELSE 0 END) as failed_files,
    SUM(d.file_size_bytes) as total_size_bytes,
    MIN(d.indexed_at) as first_indexed,
    MAX(d.indexed_at) as last_indexed
FROM file_sources s
LEFT JOIN file_documents d ON s.id = d.source_id
GROUP BY s.id, s.source_name, s.source_type, s.enabled;

-- View: Category statistics
CREATE VIEW IF NOT EXISTS category_stats AS
SELECT 
    category,
    COUNT(*) as total_files,
    SUM(CASE WHEN status = 'processed' THEN 1 ELSE 0 END) as processed,
    SUM(CASE WHEN status = 'indexed' THEN 1 ELSE 0 END) as pending,
    SUM(file_size_bytes) as total_size_bytes,
    MIN(indexed_at) as first_indexed,
    MAX(indexed_at) as last_indexed
FROM file_documents
GROUP BY category;

-- View: Government documents summary
CREATE VIEW IF NOT EXISTS government_docs_view AS
SELECT 
    d.id,
    d.file_name,
    d.file_path,
    g.jenis_dokumen,
    g.nomor_dokumen,
    g.tahun_dokumen,
    g.instansi_pembuat,
    g.judul,
    g.tentang,
    g.status_dokumen,
    g.tanggal_ditetapkan,
    g.tanggal_diundangkan
FROM file_documents d
JOIN government_metadata g ON d.id = g.document_id
ORDER BY g.tahun_dokumen DESC, g.nomor_dokumen DESC;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto update updated_at
CREATE TRIGGER IF NOT EXISTS trigger_file_documents_updated_at
    AFTER UPDATE ON file_documents
    FOR EACH ROW
BEGIN
    UPDATE file_documents SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trigger_file_sources_updated_at
    AFTER UPDATE ON file_sources
    FOR EACH ROW
BEGIN
    UPDATE file_sources SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Auto set ocr_required based on file type
CREATE TRIGGER IF NOT EXISTS trigger_auto_ocr_flag
    AFTER INSERT ON file_documents
    FOR EACH ROW
WHEN NEW.extension IN ('.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.webp')
BEGIN
    INSERT INTO document_content (document_id, ocr_required, extracted_text)
    VALUES (NEW.id, TRUE, NULL)
    ON CONFLICT(document_id) DO UPDATE SET ocr_required = TRUE;
END;

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Insert default sources (akan di-enable manual)
INSERT OR IGNORE INTO file_sources (source_type, source_name, display_name, enabled, config_json) VALUES
    ('onedrive', 'OneDrive_PUU', 'OneDrive - Peraturan UU', TRUE, '{"base_path": "/home/aseps/OneDrive_PUU", "categories": ["PUU_2024", "PUU_2025", "PUU_2026"]}'),
    ('googledrive', 'Google_Drive', 'Google Drive Documents', FALSE, '{"folder_id": "", "sync_mode": "incremental"}'),
    ('local', 'Local_Files', 'Local File System', FALSE, '{"base_path": "/home/aseps/Documents", "recursive": true}');

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================