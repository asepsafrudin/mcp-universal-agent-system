# Setup: MCP Unified sebagai Persistent Service

## Prerequisites
- WSL2 dengan systemd aktif (cek: `ps -p 1 -o comm=`)
- PostgreSQL running (cek: `docker ps | grep mcp-pg`)
- Redis running (cek: `docker ps | grep redis`)
- Python dependencies terinstall

## Instalasi Dependencies

Jika starlette belum terinstall:
```bash
cd /home/aseps/MCP/mcp-unified
pip install starlette>=0.36.0
```

## Instalasi Service

### Step 1: Copy service file
```bash
sudo cp /home/aseps/MCP/mcp-unified/mcp-unified.service \
        /etc/systemd/system/mcp-unified.service
```

### Step 2: Reload systemd dan enable service
```bash
sudo systemctl daemon-reload
sudo systemctl enable mcp-unified
sudo systemctl start mcp-unified
```

### Step 3: Verifikasi
```bash
# Cek status
sudo systemctl status mcp-unified

# Cek health endpoint
curl http://localhost:8000/health

# Lihat logs
journalctl -u mcp-unified -f
```

## Cara Menggunakan dari Editor/Agent Lain

### Cline / Claude
Tambahkan ke konfigurasi MCP:
```json
{
  "mcpServers": {
    "mcp-unified": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

### Cursor / VS Code
Sama — gunakan URL: `http://localhost:8000/sse`

### Agent lain (Python)
```python
# Import portable client (akan dibuat di TASK-008)
from shared.mcp_client import PortableMCPClient
client = PortableMCPClient()  # Auto-discover via localhost:8000
```

## Maintenance

### Stop service
```bash
sudo systemctl stop mcp-unified
```

### Restart setelah update kode
```bash
sudo systemctl restart mcp-unified
```

### Lihat logs real-time
```bash
journalctl -u mcp-unified -f
```

### Cek apakah aktif setelah reboot WSL
```bash
curl http://localhost:8000/health
```

## Troubleshooting

### Service gagal start
```bash
journalctl -u mcp-unified -n 50 --no-pager
```

### Port sudah dipakai
```bash
ss -tuln | grep :8000
```

### Database tidak connect
Pastikan Docker container PostgreSQL berjalan:
```bash
docker ps | grep mcp-pg
docker start mcp-pg  # jika stopped
```

### Python module not found
Pastikan PYTHONPATH sudah di-set dengan benar:
```bash
export PYTHONPATH=/home/aseps/MCP/mcp-unified
```

## Vision Tools Setup

### Install dependencies
```bash
cd /home/aseps/MCP/mcp-unified
pip install Pillow pymupdf --break-system-packages
```

### Pull vision model
```bash
# Ringan, cepat — recommended untuk mulai
ollama pull moondream2

# Kualitas lebih tinggi — butuh GPU lebih besar
ollama pull llava:34b
```

### Override model via environment variable
```bash
export MCP_VISION_MODEL=moondream2  # default
export MCP_VISION_MODEL=llava:34b   # higher quality
```

### Verifikasi vision tools
```bash
curl -X POST http://localhost:8000/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "analyze_image",
    "arguments": {
      "image_path": "/tmp/test.png",
      "prompt": "Describe this image",
      "namespace": "test"
    }
  }'
```
