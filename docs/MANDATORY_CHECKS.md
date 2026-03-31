# Mandatory Checks untuk Cline

## ⚠️ WAJIB: Pemeriksaan MCP-UNIFIED di Awal Tugas

Setiap kali Cline memulai tugas baru, **WAJIB** melakukan pemeriksaan koneksi MCP-UNIFIED dan service yang dibutuhkan terlebih dahulu.

---

## Alasan

1. **Mencegah Error**: Banyak tool MCP bergantung pada database PostgreSQL. Jika database tidak terhubung, tool akan gagal dengan error yang membingungkan.
2. **Menghemat Waktu**: Mendeteksi masalah di awal lebih baik daripada mengetahuinya di tengah tugas.
3. **Konsistensi**: Memastikan environment selalu dalam kondisi siap sebelum eksekusi.

---

## Script Health Check

Lokasi: `/home/aseps/MCP/scripts/mcp_health_check.sh`

### Penggunaan

```bash
/home/aseps/MCP/scripts/mcp_health_check.sh
```

### Exit Code
- `0`: Semua check lulus, sistem siap digunakan
- `1`: Ada masalah, periksa output untuk detail

---

## Yang Diperiksa

| # | Service | Port | Status Jika Gagal |
|---|---------|------|-------------------|
| 1 | PostgreSQL (mcp) | 5432 | ❌ Critical |
| 2 | PostgreSQL (mcp_knowledge) | 5433 | ❌ Critical |
| 3 | Redis | 6379 | ⚠️ Optional |
| 4 | MCP Server SSE | 8000 | ❌ Critical |
| 5 | Database Connections | - | ❌ Critical |

---

## Troubleshooting

### PostgreSQL Tidak Berjalan
```bash
sudo systemctl start postgresql
```

### MCP Server SSE Tidak Berjalan
```bash
cd /home/aseps/MCP/mcp-unified
nohup python3 mcp_server_sse.py > /tmp/mcp_server.log 2>&1 &
```

### Redis Tidak Berjalan
```bash
sudo systemctl start redis-server
```

---

## Best Practices

1. **Selalu jalankan health check** sebelum memulai tugas yang menggunakan MCP tools
2. **Perhatikan exit code** - jika `1`, selesaikan masalah sebelum melanjutkan
3. **Simpan log** jika ada masalah untuk debugging

---

## Referensi

- MCP Server: `/home/aseps/MCP/mcp-unified/`
- Log MCP: `/tmp/mcp_server.log`
- Konfigurasi: `/home/aseps/MCP/.env`