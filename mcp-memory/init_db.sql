-- Database initialization untuk Long-Term Memory System
-- PostgreSQL 16 + pgvector

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create memories table dengan vector support
CREATE TABLE IF NOT EXISTS memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(384),  -- 384 dimensi untuk all-minilm model
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes untuk performance optimization

-- Full-text search index untuk keyword matching
CREATE INDEX IF NOT EXISTS memories_fts_idx 
ON memories 
USING GIN (to_tsvector('indonesian', content));

-- Vector similarity index untuk semantic search
CREATE INDEX IF NOT EXISTS memories_vec_idx 
ON memories 
USING IVFFLAT (embedding vector_cosine_ops) 
WITH (lists = 32);

-- Composite index untuk better query performance
CREATE INDEX IF NOT EXISTS memories_key_idx 
ON memories (key);

CREATE INDEX IF NOT EXISTS memories_created_idx 
ON memories (created_at DESC);

-- Create function untuk automatic timestamp update
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger untuk auto-update updated_at
DROP TRIGGER IF EXISTS update_memories_updated_at ON memories;
CREATE TRIGGER update_memories_updated_at
    BEFORE UPDATE ON memories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data untuk testing (optional)
-- Uncomment jika ingin data test

/*
INSERT INTO memories (key, content, metadata) VALUES 
('welcome', 'Selamat datang di MCP Server dengan Long-Term Memory System', '{"category": "system", "tags": ["welcome", "setup"]}'),
('test', 'Ini adalah data test untuk memory system', '{"category": "test", "tags": ["testing"]}'),
('postgresql', 'PostgreSQL dengan pgvector untuk vector similarity search', '{"category": "database", "tags": ["postgresql", "vector", "search"]}')
ON CONFLICT (key) DO NOTHING;
*/

-- Grant permissions (adjust user as needed)
-- GRANT ALL PRIVILEGES ON memories TO aseps;
-- GRANT USAGE ON SCHEMA public TO aseps;

-- Show table info
\d memories

-- Show indexes
\di memories_*
