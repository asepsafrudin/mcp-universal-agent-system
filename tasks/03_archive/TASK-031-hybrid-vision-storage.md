# TASK-031: Implementasi Hybrid Storage untuk Vision Results

**Status:** 🔵 READY TO START  
**Priority:** HIGH  
**Created:** 2026-03-03  
**Assignee:** AI Assistant  
**Estimated Effort:** 2-3 hours

---

## 📋 Overview

Implementasi sistem penyimpanan hybrid untuk hasil pemrosesan Vision/OCR dengan confidence-based filtering ke PostgreSQL database. Hasil dengan confidence tinggi akan tersimpan di tabel SQL terstruktur untuk keperluan audit, reporting, dan analytics.

---

## 🎯 Objectives

1. ✅ Buat tabel `vision_results` di PostgreSQL dengan schema enterprise-grade
2. ✅ Implementasi confidence-based filtering (high: ≥0.8, medium: ≥0.7, low: <0.7)
3. ✅ Buat repository module untuk operasi CRUD vision results
4. ✅ Integrasi dengan existing vision pipeline (`vision_enhanced.py`)
5. ✅ Buat query interface untuk filtering dan reporting
6. ✅ Implementasi automatic linking dengan LTM (Long-Term Memory)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    VISION PROCESSING PIPELINE                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
         ┌──────────────────┴──────────────────┐
         │    analyze_image_enhanced()         │
         │    analyze_with_ocr_fallback()      │
         └──────────────────┬──────────────────┘
                            │
                    ┌───────▼────────┐
                    │ Confidence     │
                    │ Calculation    │
                    └───────┬────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
        High (≥0.8)    Medium (0.7)   Low (<0.7)
              │             │             │
      ┌───────▼───┐   ┌────▼────┐   ┌────▼────┐
      │ LTM + SQL │   │ LTM only│   │ Reject  │
      │(verified) │   │(review) │   │(retry)  │
      └───────────┘   └─────────┘   └─────────┘
```

---

## 📁 Deliverables

### 1. Database Migration
- **File:** `mcp-unified/migrations/003_vision_results_table.sql`
- **Description:** Schema tabel vision_results dengan index dan constraints

### 2. Repository Module
- **File:** `mcp-unified/memory/vision_repository.py`
- **Functions:**
  - `save_vision_result_with_confidence()`
  - `get_high_confidence_results()`
  - `get_results_by_document_type()`
  - `get_processing_stats()`
  - `update_confidence_threshold()`

### 3. Configuration Module
- **File:** `mcp-unified/core/vision_config.py`
- **Contents:** Thresholds, storage policies, retention settings

### 4. Enhanced Vision Tools
- **File:** `mcp-unified/execution/tools/vision_enhanced.py` (update)
- **Integration:** Automatic save dengan confidence filtering

### 5. Query Interface
- **File:** `mcp-unified/tools/vision_queries.py`
- **Functions:**
  - `query_by_confidence_range()`
  - `query_by_date_range()`
  - `query_by_document_type()`
  - `export_to_csv()`

### 6. Test Suite
- **File:** `mcp-unified/tests/test_vision_repository.py`
- **Coverage:** Unit tests dan integration tests

---

## 📊 Database Schema

```sql
-- Tabel utama vision results
CREATE TABLE vision_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    processing_id UUID DEFAULT gen_random_uuid(),
    
    -- File info
    file_name TEXT NOT NULL,
    file_path TEXT,
    file_hash VARCHAR(64),
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    
    -- Processing
    namespace TEXT DEFAULT 'default',
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processing_time_ms INTEGER,
    
    -- Vision results
    extracted_text TEXT,
    confidence_score DECIMAL(4,3) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    confidence_threshold DECIMAL(4,3) DEFAULT 0.8,
    processing_method VARCHAR(50), -- 'vision', 'ocr', 'hybrid'
    model_used VARCHAR(100),
    
    -- Classification
    document_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'success',
    
    -- Metadata & entities (JSONB)
    extracted_entities JSONB,
    processing_metadata JSONB,
    
    -- LTM linking (optional)
    ltm_key TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_vision_confidence ON vision_results(confidence_score);
CREATE INDEX idx_vision_processed_at ON vision_results(processed_at);
CREATE INDEX idx_vision_document_type ON vision_results(document_type);
CREATE INDEX idx_vision_status ON vision_results(status);
CREATE INDEX idx_vision_namespace ON vision_results(namespace);
CREATE INDEX idx_vision_file_hash ON vision_results(file_hash);
```

---

## ⚙️ Configuration

```python
# vision_config.py
VISION_STORAGE_CONFIG = {
    'confidence_thresholds': {
        'high': 0.80,      # Save to BOTH LTM and SQL
        'medium': 0.70,    # Save to LTM only
        'low': 0.50        # Reject
    },
    'storage_policy': {
        'high_confidence_to_sql': True,
        'all_to_ltm': True,
        'reject_low_confidence': True
    },
    'retention': {
        'sql_results_days': 365,
        'ltm_results_days': 90
    }
}
```

---

## ✅ Acceptance Criteria

- [ ] Migration script berjalan tanpa error
- [ ] Tabel `vision_results` terbuat dengan index lengkap
- [ ] Repository module bisa melakukan CRUD operations
- [ ] Vision pipeline otomatis menyimpan high-confidence results ke SQL
- [ ] Query interface bisa filtering berdasarkan confidence, date, document type
- [ ] Test suite pass semua test cases
- [ ] Dokumentasi penggunaan tersedia

---

## 🔗 Dependencies

- PostgreSQL database (sudah ada)
- Table `memories` untuk LTM (sudah ada)
- Module `vision_enhanced.py` (sudah ada)
- Module `longterm.py` untuk LTM operations (sudah ada)

---

## 📚 References

- [VISION_CAPABILITY_INSPECTION_REPORT.md](../VISION_CAPABILITY_INSPECTION_REPORT.md)
- [mcp-unified/memory/longterm.py](../mcp-unified/memory/longterm.py)
- [mcp-unified/execution/tools/vision_enhanced.py](../mcp-unified/execution/tools/vision_enhanced.py)

---

## 📝 Notes

- Implementasi mengikuti best practice enterprise (AWS Textract, Google Document AI pattern)
- Dual storage: LTM untuk semantic search, SQL untuk structured data & audit
- Confidence filtering mencegah database bloat dengan data low-quality
- Schema designed untuk multi-tenant dengan namespace field

---

**Next Action:** Toggle to Act mode untuk memulai implementasi
