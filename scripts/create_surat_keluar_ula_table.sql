-- Table: surat_dari_luar_bangda (formerly surat_keluar_ula)
-- Purpose: Store surat keluar data from external ULA spreadsheet (data surat luar 2026)
-- Created: 2026-03-31
-- Source: Google Sheet ID 1N6K0mXrGU1aWaUAOB0O97n7LdpooKBI27hu3KqqOAYA

CREATE TABLE IF NOT EXISTS surat_dari_luar_bangda (
    id              BIGSERIAL PRIMARY KEY,
    unique_id       TEXT NOT NULL UNIQUE,
    
    -- Surat Masuk tab fields (mapped from Google Sheet columns)
    surat_dari      TEXT,           -- Pengirim surat (Col B)
    nomor_surat     TEXT,           -- Nomor surat (Col C)
    tgl_surat       DATE,           -- Tanggal surat (Col D)
    tgl_diterima_ula DATE,          -- Tanggal diterima ULA (Col E)
    perihal         TEXT,           -- Perihal surat (Col F)
    arahan_menteri  TEXT,           -- Arahan dari Menteri (Col G)
    arahan_sekjen   TEXT,           -- Arahan dari Sekjen (Col H)
    agenda_ula      TEXT,           -- Nomor agenda ULA format NNN/L (Col I)
    status_mailmerge TEXT,          -- Status mailmerge (Col J)
    
    -- Metadata
    timestamp_raw   TIMESTAMP,      -- Original timestamp from sheet (Col A)
    source_sheet    TEXT NOT NULL DEFAULT 'Surat Masuk',
    source_row      INTEGER,        -- Row number in original sheet
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_sdlb_nomor_surat ON surat_dari_luar_bangda(nomor_surat);
CREATE INDEX idx_sdlb_tgl_surat ON surat_dari_luar_bangda(tgl_surat DESC);
CREATE INDEX idx_sdlb_tgl_diterima ON surat_dari_luar_bangda(tgl_diterima_ula DESC);
CREATE INDEX idx_sdlb_agenda ON surat_dari_luar_bangda(agenda_ula);
CREATE INDEX idx_sdlb_unique ON surat_dari_luar_bangda(unique_id);

-- Table: lembar_disposisi_bangda
-- Purpose: Store disposisi lembar data from external spreadsheet
CREATE TABLE IF NOT EXISTS lembar_disposisi_bangda (
    id              BIGSERIAL PRIMARY KEY,
    unique_id       TEXT NOT NULL UNIQUE,
    surat_keluar_id BIGINT REFERENCES surat_dari_luar_bangda(id),
    
    -- Lembar Disposisi Dirjen fields
    nomor_disposisi TEXT,
    tanggal_disposisi DATE,
    dari_disposisi  TEXT,
    perihal_disposisi TEXT,
    
    -- Metadata
    source_sheet    TEXT NOT NULL DEFAULT 'Lembar Disposisi Dirjen',
    source_row      INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table: disposisi_distributions
-- Purpose: Store disposisi distribution data from multiple tabs
CREATE TABLE IF NOT EXISTS disposisi_distributions (
    id              BIGSERIAL PRIMARY KEY,
    unique_id       TEXT NOT NULL UNIQUE,
    surat_keluar_id BIGINT REFERENCES surat_dari_luar_bangda(id),
    
    -- Distribution fields (common across tabs)
    nomor_disposisi TEXT,
    tanggal_disposisi DATE,
    dari            TEXT,
    kepada          TEXT,
    isi_disposisi   TEXT,
    batas_waktu     DATE,
    
    -- Source identification
    source_tab      TEXT NOT NULL,  -- 'Dispo DJ/TU Pim' or 'Dispo Ses'
    source_row      INTEGER,
    
    -- Metadata
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for disposisi tables
CREATE INDEX idx_ldb_surat_id ON lembar_disposisi_bangda(surat_keluar_id);
CREATE INDEX idx_dd_surat_id ON disposisi_distributions(surat_keluar_id);
CREATE INDEX idx_dd_source_tab ON disposisi_distributions(source_tab);