# MCP Long-Term Memory Server (Python + PostgreSQL)

Sistem memori jangka panjang yang persisten untuk sistem Multi-Agent (seperti CrewAI) dan integrasi IDE (seperti Antigravity). Sistem ini menggunakan backend **FastAPI**, **PostgreSQL 16**, dan **pgvector** untuk pencarian hybrid (semantic + keyword).

## 🚀 Fitur Utama

- **Hybrid Search**: Kombinasi semantic vector search (via pgvector) dan full-text search tradisional.
- **FastAPI Backend**: Interface JSON-RPC 2.0 yang cepat dan kompatibel dengan Model Context Protocol.
- **PostgreSQL Persistence**: Penyimpanan data yang handal dengan dukungan metadata fleksibel.
- **Multi-Agent Ready**: Dirancang khusus untuk digunakan oleh `Researcher`, `Writer`, dan `Checker` dalam sistem CrewAI.

## 🛠️ Tools Memori

| Tool | Deskripsi | Parameter Utama |
|------|-----------|-----------------|
| `memory_save` | Simpan informasi ke database | `key`, `content`, `metadata` |
| `memory_search` | Cari memori dengan strategi hybrid | `query`, `strategy`, `limit` |
| `memory_list` | Lihat daftar memori tersimpan | `limit`, `offset` |
| `memory_delete` | Hapus memori | `id` atau `key` |

## 🔄 Workflow Lengkap

### 1. Inisialisasi & Koneksi
- Server dijalankan via `uvicorn` (FastAPI).
- Pada saat startup, server membuka connection pool ke PostgreSQL.
- Driver `psycopg` v3 digunakan untuk performa asinkron yang optimal.

### 2. Penyimpanan Memori (`memory_save`)
1. Agen mengirimkan konten yang ingin diingat (contoh: hasil riset atau ringkasan project).
2. Server menghasilkan embeddings (vector) untuk konten tersebut (opsional, jika Ollama/OpenAI aktif).
3. Data disimpan ke tabel `memories` di PostgreSQL beserta metadata (timestamp, tags, dll).

### 3. Pemrosesan & Pencarian (`memory_search`)
1. User/Agen melakukan pencarian menggunakan bahasa alami.
2. Server mengeksekusi hybrid query:
   - **Semantic**: Mencari kemiripan makna menggunakan vector.
   - **Keyword**: Mencari kecocokan kata kunci menggunakan Full-Text Search.
3. Hasil digabungkan dengan pembobotan (Reciprocal Rank Fusion) untuk akurasi maksimal.

### 4. Integrasi ke Workflow Agen
- **Researcher**: Menggunakan `memory_search` untuk mencari pengetahuan yang sudah ada sebelum melakukan riset baru.
- **Writer**: Menggunakan `memory_save` untuk menyimpan draft atau produk akhir dokumentasi.
- **Checker**: Menggunakan `memory_search` untuk memvalidasi konsistensi data dengan memori sebelumnya.

## 📁 Struktur Direktori

```text
mcp-memory/
├── mcp_server.py      # Core FastAPI Server & JSON-RPC Handler
├── tools/
│   ├── memory.py      # Logika Database PostgreSQL & pgvector
│   ├── file_writer.py # Tool File Operations
│   └── ...            # Tool lainnya (read_file, run_shell)
├── init_db.sql        # Skema Database & Vector Setup
└── Dockerfile         # Containerization
```

## ⚙️ Cara Menjalankan

1. pastikan PostgreSQL dengan ekstensi `pgvector` sudah berjalan.
2. Jalankan server:
   ```bash
   python mcp_server.py
   ```
3. Server akan mendengarkan di `http://0.0.0.0:8000`.
