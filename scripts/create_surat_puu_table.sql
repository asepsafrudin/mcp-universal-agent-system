-- Table: surat_untuk_substansi_puu
-- Purpose: Filter/sortir surat yang diteruskan ke Substansi PUU
-- Created: 2026-03-31
-- Source: From disposisi_distributions where 'kepada' contains 'Substansi PUU'

CREATE TABLE IF NOT EXISTS surat_untuk_substansi_puu (
    id                  BIGSERIAL PRIMARY KEY,
    surat_id            BIGINT REFERENCES surat_dari_luar_bangda(id),
    
    -- Surat info (denormalized for quick access)
    agenda              TEXT,               -- From agenda_ula
    surat_dari          TEXT,                -- Pengirim surat
    nomor_surat         TEXT,               -- Nomor surat
    
    -- Disposisi info
    disposisi_kepada    TEXT,               -- Kepada (from disposisi_distributions.kepada)
    isi_disposisi       TEXT,                -- Arahan/catatan dari Ses
    tanggal_disposisi   DATE,               -- Tanggal disposisi Ses
    
    -- Status tracking
    status              TEXT DEFAULT 'pending',  -- pending, diproses, selesai
    catatan_internal    TEXT,               -- Catatan tambahan dari tim PUU
    tanggal_diterima    DATE,               -- Tanggal diterima oleh PUU
    tanggal_selesai     DATE,               -- Tanggal selesai diproses
    
    -- Metadata
    source_disposisi_id BIGINT,             -- FK back to disposisi_distributions
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_spuu_surat_id ON surat_untuk_substansi_puu(surat_id);
CREATE INDEX IF NOT EXISTS idx_spuu_agenda ON surat_untuk_substansi_puu(agenda);
CREATE INDEX IF NOT EXISTS idx_spuu_status ON surat_untuk_substansi_puu(status);
CREATE INDEX IF NOT EXISTS idx_spuu_source ON surat_untuk_substansi_puu(source_disposisi_id);

COMMENT ON TABLE surat_untuk_substansi_puu IS 'Sortir surat yang diteruskan ke Substansi PUU untuk ditindaklanjuti';

-- Populate from existing data
INSERT INTO surat_untuk_substansi_puu (
    surat_id,
    agenda,
    surat_dari,
    nomor_surat,
    disposisi_kepada,
    isi_disposisi,
    tanggal_disposisi,
    source_disposisi_id
)
SELECT DISTINCT ON (sdlb.id)
    sdlb.id,
    sdlb.agenda_ula,
    sdlb.surat_dari,
    sdlb.nomor_surat,
    dd.kepada,
    dd.isi_disposisi,
    dd.tanggal_disposisi,
    dd.id
FROM disposisi_distributions dd
JOIN surat_dari_luar_bangda sdlb ON sdlb.id = dd.surat_keluar_id
WHERE dd.kepada ILIKE '%Substansi PUU%'
   OR dd.kepada ILIKE '%PUU%';