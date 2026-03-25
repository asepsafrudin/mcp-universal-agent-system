#!/usr/bin/env python3
"""
Document Management System - Database Manager
=============================================
SQLite database manager untuk Unified Document Index.
"""

import os
import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from contextlib import contextmanager

from .config import SQLITE_PATH, SCHEMA_PATH, setup_directories


class DatabaseManager:
    """SQLite database manager for document management system"""
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or SQLITE_PATH
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Ensure database exists with proper schema"""
        setup_directories()
        
        if not self.db_path.exists() or self.db_path.stat().st_size == 0:
            self._init_schema()
    
    def _init_schema(self):
        """Initialize database schema"""
        if not SCHEMA_PATH.exists():
            raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
        
        with open(SCHEMA_PATH, 'r') as f:
            schema = f.read()
        
        with self.get_connection() as conn:
            conn.executescript(schema)
            conn.commit()
        
        print(f"✅ Database initialized: {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    @contextmanager
    def get_cursor(self):
        """Get database cursor"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
    
    # =========================================================================
    # SOURCE MANAGEMENT
    # =========================================================================
    
    def get_sources(self, enabled_only: bool = False) -> List[Dict]:
        """Get all document sources"""
        with self.get_cursor() as cursor:
            sql = "SELECT * FROM file_sources"
            if enabled_only:
                sql += " WHERE enabled = TRUE"
            sql += " ORDER BY source_name"
            
            cursor.execute(sql)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_source_by_name(self, source_name: str) -> Optional[Dict]:
        """Get source by name"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM file_sources WHERE source_name = ?",
                (source_name,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def add_source(self, source_type: str, source_name: str, 
                   display_name: str = None, config: dict = None,
                   enabled: bool = True) -> int:
        """Add new document source"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO file_sources (source_type, source_name, display_name, 
                                         enabled, config_json)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(source_name) DO UPDATE SET
                    source_type = excluded.source_type,
                    display_name = excluded.display_name,
                    config_json = excluded.config_json,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (source_type, source_name, display_name, enabled, 
                  json.dumps(config) if config else '{}'))
            return cursor.fetchone()[0]
    
    def update_source_sync_time(self, source_id: int):
        """Update last sync time for source"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE file_sources 
                SET last_sync_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (source_id,))
    
    def enable_source(self, source_name: str, enabled: bool = True):
        """Enable/disable source"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE file_sources SET enabled = ? WHERE source_name = ?
            """, (enabled, source_name))
    
    # =========================================================================
    # DOCUMENT OPERATIONS
    # =========================================================================
    
    def add_document(self, source_id: int, file_name: str, file_path: str,
                     file_hash: str = None, file_size: int = None,
                     mime_type: str = None, extension: str = None,
                     category: str = None, subcategory: str = None,
                     external_id: str = None, file_modified_at: str = None) -> int:
        """Add or update document"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO file_documents (
                    source_id, external_id, file_name, file_path, file_hash,
                    file_size_bytes, mime_type, extension, category, subcategory,
                    file_modified_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id, file_path) DO UPDATE SET
                    file_hash = excluded.file_hash,
                    file_size_bytes = excluded.file_size_bytes,
                    file_modified_at = excluded.file_modified_at,
                    updated_at = CURRENT_TIMESTAMP,
                    status = CASE 
                        WHEN file_documents.file_hash != excluded.file_hash 
                        THEN 'indexed' 
                        ELSE file_documents.status 
                    END
                RETURNING id
            """, (source_id, external_id, file_name, file_path, file_hash,
                  file_size, mime_type, extension, category, subcategory,
                  file_modified_at))
            return cursor.fetchone()[0]
    
    def get_document_by_path(self, source_id: int, file_path: str) -> Optional[Dict]:
        """Get document by source and path"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM file_documents 
                WHERE source_id = ? AND file_path = ?
            """, (source_id, file_path))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_document_by_id(self, doc_id: int) -> Optional[Dict]:
        """Get document by ID"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM file_documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_document_status(self, doc_id: int, status: str, 
                               stage: str = None, error: str = None):
        """Update document processing status"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE file_documents 
                SET status = ?, processing_stage = ?, last_processed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, stage, doc_id))
    
    def get_pending_documents(self, limit: int = None) -> List[Dict]:
        """Get documents pending processing"""
        with self.get_cursor() as cursor:
            sql = """
                SELECT d.*, s.source_name, s.source_type
                FROM file_documents d
                JOIN file_sources s ON d.source_id = s.id
                WHERE d.status IN ('indexed', 'processing')
                ORDER BY d.indexed_at ASC
            """
            if limit:
                sql += f" LIMIT {limit}"
            cursor.execute(sql)
            return [dict(row) for row in cursor.fetchall()]
    
    # =========================================================================
    # CONTENT & OCR
    # =========================================================================
    
    def add_document_content(self, document_id: int, extracted_text: str = None,
                            extraction_method: str = None, ocr_required: bool = False,
                            ocr_engine: str = None, ocr_confidence: float = None,
                            ocr_language: str = 'id', processing_time: float = None,
                            error_message: str = None):
        """Add or update document content"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO document_content (
                    document_id, extracted_text, text_extraction_method,
                    ocr_required, ocr_engine, ocr_confidence, ocr_language,
                    extracted_at, processing_time_seconds, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
                ON CONFLICT(document_id) DO UPDATE SET
                    extracted_text = COALESCE(excluded.extracted_text, document_content.extracted_text),
                    text_extraction_method = COALESCE(excluded.text_extraction_method, document_content.text_extraction_method),
                    ocr_required = COALESCE(excluded.ocr_required, document_content.ocr_required),
                    ocr_engine = COALESCE(excluded.ocr_engine, document_content.ocr_engine),
                    ocr_confidence = COALESCE(excluded.ocr_confidence, document_content.ocr_confidence),
                    ocr_language = COALESCE(excluded.ocr_language, document_content.ocr_language),
                    extracted_at = CURRENT_TIMESTAMP,
                    processing_time_seconds = COALESCE(excluded.processing_time_seconds, document_content.processing_time_seconds),
                    error_message = excluded.error_message
            """, (document_id, extracted_text, extraction_method, ocr_required,
                  ocr_engine, ocr_confidence, ocr_language, processing_time, error_message))
    
    def get_document_content(self, document_id: int) -> Optional[Dict]:
        """Get document content"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM document_content WHERE document_id = ?
            """, (document_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_documents_needing_ocr(self, limit: int = 10) -> List[Dict]:
        """Get documents that need OCR processing"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT d.*, s.source_name
                FROM file_documents d
                JOIN file_sources s ON d.source_id = s.id
                LEFT JOIN document_content c ON d.id = c.document_id
                WHERE d.extension IN ('.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.webp')
                AND (c.ocr_required IS NULL OR c.ocr_required = TRUE)
                AND (c.extracted_text IS NULL OR c.ocr_engine IS NULL)
                AND d.status != 'failed'
                ORDER BY d.indexed_at ASC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # =========================================================================
    # LABELS
    # =========================================================================
    
    def add_label(self, document_id: int, label_type: str, label_value: str,
                  label_display: str = None, source: str = 'auto',
                  confidence: float = None, matched_pattern: str = None):
        """Add label to document"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO document_labels 
                (document_id, label_type, label_value, label_display, source, confidence, matched_pattern)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(document_id, label_type, label_value) DO UPDATE SET
                    label_display = excluded.label_display,
                    source = excluded.source,
                    confidence = excluded.confidence,
                    matched_pattern = excluded.matched_pattern
            """, (document_id, label_type, label_value, label_display, source, confidence, matched_pattern))
    
    def get_document_labels(self, document_id: int) -> List[Dict]:
        """Get all labels for a document"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM document_labels 
                WHERE document_id = ? 
                ORDER BY label_type, confidence DESC
            """, (document_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_labels_by_type(self, label_type: str, limit: int = 100) -> List[Dict]:
        """Get all labels of a specific type"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT label_value, COUNT(*) as count
                FROM document_labels
                WHERE label_type = ?
                GROUP BY label_value
                ORDER BY count DESC
                LIMIT ?
            """, (label_type, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    # =========================================================================
    # GOVERNMENT METADATA
    # =========================================================================
    
    def add_government_metadata(self, document_id: int, **kwargs):
        """Add government document metadata"""
        fields = [
            'jenis_dokumen', 'nomor_dokumen', 'tahun_dokumen', 'instansi_pembuat',
            'instansi_tingkat', 'judul', 'tentang', 'status_dokumen', 'mengubah',
            'dicabut_oleh', 'tanggal_ditetapkan', 'tanggal_diundangkan',
            'tanggal_berlaku', 'berita_negara_no', 'tambahan_berita_negara', 'confidence'
        ]
        
        valid_fields = {k: v for k, v in kwargs.items() if k in fields and v is not None}
        
        if not valid_fields:
            return
        
        columns = ['document_id'] + list(valid_fields.keys())
        placeholders = ', '.join(['?' for _ in columns])
        updates = ', '.join([f"{k} = excluded.{k}" for k in valid_fields.keys()])
        
        sql = f"""
            INSERT INTO government_metadata ({', '.join(columns)})
            VALUES ({placeholders})
            ON CONFLICT(document_id) DO UPDATE SET
                {updates},
                extracted_at = CURRENT_TIMESTAMP
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(sql, [document_id] + list(valid_fields.values()))
    
    def get_government_metadata(self, document_id: int) -> Optional[Dict]:
        """Get government metadata for document"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM government_metadata WHERE document_id = ?
            """, (document_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # =========================================================================
    # SYNC LOG
    # =========================================================================
    
    def start_sync_log(self, source_id: int, sync_type: str = 'incremental') -> int:
        """Start sync log entry"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO sync_log (source_id, sync_type, status)
                VALUES (?, ?, 'running')
                RETURNING id
            """, (source_id, sync_type))
            return cursor.fetchone()[0]
    
    def complete_sync_log(self, log_id: int, status: str = 'completed',
                         files_total: int = 0, files_new: int = 0,
                         files_updated: int = 0, files_failed: int = 0,
                         error_message: str = None):
        """Complete sync log entry"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE sync_log SET
                    completed_at = CURRENT_TIMESTAMP,
                    status = ?,
                    files_total = ?,
                    files_new = ?,
                    files_updated = ?,
                    files_failed = ?,
                    error_message = ?
                WHERE id = ?
            """, (status, files_total, files_new, files_updated, files_failed,
                  error_message, log_id))
    
    def get_sync_history(self, source_id: int = None, limit: int = 10) -> List[Dict]:
        """Get sync history"""
        with self.get_cursor() as cursor:
            sql = """
                SELECT l.*, s.source_name
                FROM sync_log l
                LEFT JOIN file_sources s ON l.source_id = s.id
            """
            if source_id:
                sql += " WHERE l.source_id = ?"
                cursor.execute(sql + " ORDER BY l.started_at DESC LIMIT ?", (source_id, limit))
            else:
                cursor.execute(sql + " ORDER BY l.started_at DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        with self.get_cursor() as cursor:
            stats = {}
            
            # Total documents
            cursor.execute("SELECT COUNT(*) FROM file_documents")
            stats['total_documents'] = cursor.fetchone()[0]
            
            # By status
            cursor.execute("""
                SELECT status, COUNT(*) FROM file_documents GROUP BY status
            """)
            stats['by_status'] = dict(cursor.fetchall())
            
            # By source
            cursor.execute("""
                SELECT s.source_name, COUNT(d.id)
                FROM file_sources s
                LEFT JOIN file_documents d ON s.id = d.source_id
                GROUP BY s.source_name
            """)
            stats['by_source'] = dict(cursor.fetchall())
            
            # By category
            cursor.execute("""
                SELECT category, COUNT(*) FROM file_documents 
                WHERE category IS NOT NULL
                GROUP BY category
            """)
            stats['by_category'] = dict(cursor.fetchall())
            
            # Documents with content
            cursor.execute("""
                SELECT COUNT(*) FROM document_content 
                WHERE extracted_text IS NOT NULL
            """)
            stats['with_content'] = cursor.fetchone()[0]
            
            # Documents with OCR
            cursor.execute("""
                SELECT COUNT(*) FROM document_content WHERE ocr_engine IS NOT NULL
            """)
            stats['with_ocr'] = cursor.fetchone()[0]
            
            # Total labels
            cursor.execute("SELECT COUNT(*) FROM document_labels")
            stats['total_labels'] = cursor.fetchone()[0]
            
            # Top jenis_dokumen
            cursor.execute("""
                SELECT label_value, COUNT(*) as count
                FROM document_labels
                WHERE label_type = 'jenis_dokumen'
                GROUP BY label_value
                ORDER BY count DESC
                LIMIT 10
            """)
            stats['top_jenis_dokumen'] = dict(cursor.fetchall())
            
            return stats
    
    def search_documents(self, query: str, limit: int = 50) -> List[Dict]:
        """Search documents using FTS"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT d.*, s.source_name, rank
                FROM document_fts fts
                JOIN file_documents d ON fts.rowid = d.id
                JOIN file_sources s ON d.source_id = s.id
                WHERE document_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def reset_database(self):
        """Reset database - drop all tables and recreate"""
        print("⚠️  Resetting database...")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Drop all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                if not table.startswith('sqlite_'):
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
            
            conn.commit()
        
        # Reinitialize schema
        self._init_schema()
        print("✅ Database reset complete")


# Singleton instance
_db_instance = None

def get_db() -> DatabaseManager:
    """Get singleton database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance


if __name__ == "__main__":
    # Test database
    db = get_db()
    
    print("\n📊 Database Statistics:")
    stats = db.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n📁 Sources:")
    for source in db.get_sources():
        print(f"  - {source['source_name']} ({source['source_type']}) - {'enabled' if source['enabled'] else 'disabled'}")