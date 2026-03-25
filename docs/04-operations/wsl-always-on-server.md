# WSL Always-On Server Setup

Panduan lengkap untuk menjadikan WSL sebagai "always-on" server untuk MCP Unified Hub.

---

## 📋 Overview

### Masalah yang Dipecahkan

| Masalah | Solusi |
|---------|--------|
| WSL auto-shutdown saat idle | `.wslconfig` dengan `autoShutdown=false` |
| WSL mati saat Windows reboot | Task Scheduler auto-start |
| MCP service tidak restart otomatis | systemd service + health monitor |
| Tidak ada monitoring | Health check every 5 minutes |

### Arsitektur

```
┌─────────────────────────────────────────────────────────────┐
│                         Windows                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Task Scheduler (WSL-MCP-KeepAlive)                 │    │
│  │  • Trigger: Startup, Logon, Every 5 min            │    │
│  │  • Script: C:\Scripts\start-wsl.ps1                │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  WSL2 Ubuntu                                        │    │
│  │  ┌─────────────────────────────────────────────┐    │    │
│  │  │  systemd                                      │    │    │
│  │  │  ┌─────────────┐  ┌──────────────────────┐ │    │    │
│  │  │  │mcp-unified  │  │wsl-health-monitor    │ │    │    │
│  │  │  │  Service    │  │  Service             │ │    │    │
│  │  │  └──────┬──────┘  └──────────────────────┘ │    │    │
│  │  │         │                                 │    │    │
│  │  │         ▼                                 │    │    │
│  │  │  ┌─────────────────────────────────────┐  │    │    │
│  │  │  │  MCP Server (port 8000)              │  │    │    │
│  │  │  │  • Health endpoint: /health          │  │    │    │
│  │  │  │  • SSE endpoint: /sse                │  │    │    │
│  │  │  └─────────────────────────────────────┘  │    │    │
│  │  └─────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Windows 10/11 dengan WSL2
- Ubuntu (atau distro WSL lain) terinstall
- MCP Unified Hub sudah setup (`mcp-unified/`)

### One-Liner Setup

```bash
# Di WSL
cd /home/aseps/MCP
chmod +x scripts/wsl-status.sh scripts/wsl-restart.sh
sudo cp scripts/wsl-health-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable wsl-health-monitor
```

```powershell
# Di PowerShell (sebagai Administrator)
# 1. Copy .wslconfig
copy "\\wsl$\Ubuntu\home\aseps\MCP\scripts\windows\.wslconfig" "$env:USERPROFILE\.wslconfig"

# 2. Copy scripts
New-Item -ItemType Directory -Path "C:\Scripts" -Force
copy "\\wsl$\Ubuntu\home\aseps\MCP\scripts\windows\start-wsl.ps1" "C:\Scripts\"

# 3. Setup Task Scheduler
PowerShell.exe -ExecutionPolicy Bypass -File "\\wsl$\Ubuntu\home\aseps\MCP\scripts\windows\setup-task-scheduler.ps1"

# 4. Restart WSL
wsl --shutdown
```

---

## 📁 File Structure

```
scripts/
├── windows/
│   ├── .wslconfig                    # WSL config (copy ke C:\Users\<user>\.wslconfig)
│   ├── start-wsl.ps1                 # PowerShell keep-alive script
│   ├── setup-task-scheduler.ps1      # Auto-setup Task Scheduler
│   └── setup-manual-steps.md         # Panduan manual (backup)
├── wsl-health-monitor.py             # Python health monitor
├── wsl-health-monitor.service        # systemd service file
├── wsl-status.sh                     # Status checker script
└── wsl-restart.sh                    # Force restart script

docs/04-operations/
└── wsl-always-on-server.md           # Dokumentasi ini
```

---

## 🔧 Detailed Setup

### 1. WSL Configuration (Windows Side)

#### 1.1 Copy .wslconfig

File `.wslconfig` mengontrol behavior global WSL:

```powershell
# Di PowerShell (sebagai Administrator)
copy "\\wsl$\Ubuntu\home\aseps\MCP\scripts\windows\.wslconfig" "$env:USERPROFILE\.wslconfig"
```

#### 1.2 Isi File .wslconfig

```ini
[wsl2]
# Mencegah WSL shutdown saat idle
autoMemoryReclaim=disabled

# Resource allocation (sesuaikan dengan kebutuhan)
memory=8GB
processors=4
swap=2GB

# Network settings
localhostForwarding=true
kernelCommandLine=clocksource=tsc

[experimentalfeatures]
# Mencegah auto-shutdown WSL
autoShutdown=false
```

#### 1.3 Apply Changes

```powershell
wsl --shutdown
# Tunggu 10 detik, lalu buka WSL lagi
wsl
```

---

### 2. Windows Task Scheduler Setup

#### 2.1 Otomatis (Recommended)

```powershell
# Jalankan sebagai Administrator
PowerShell.exe -ExecutionPolicy Bypass -File "C:\Scripts\setup-task-scheduler.ps1"
```

#### 2.2 Manual

Jika script otomatis gagal, ikuti [setup-manual-steps.md](../../scripts/windows/setup-manual-steps.md).

---

### 3. Health Monitor Service (WSL Side)

#### 3.1 Install Service

```bash
cd /home/aseps/MCP

# Copy service file
sudo cp scripts/wsl-health-monitor.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start
sudo systemctl enable wsl-health-monitor

# Start service
sudo systemctl start wsl-health-monitor

# Verify
sudo systemctl status wsl-health-monitor
```

#### 3.2 Konfigurasi Health Monitor

Edit `scripts/wsl-health-monitor.py` untuk mengubah:

```python
# Health check interval (detik)
HEALTH_CHECK_INTERVAL = 300  # 5 menit

# Max retry attempts
MAX_RETRIES = 3

# Service name
MCP_SERVICE = "mcp-unified"
```

---

### 4. Utility Scripts

#### 4.1 Status Checker

```bash
# Cek status semua komponen
./scripts/wsl-status.sh
```

Output:
```
========================================
   WSL + MCP Unified Hub Status Check
========================================

Systemd Status:
  ✓ Systemd is running

MCP Unified Service:
  ✓ mcp-unified is active

HTTP Health Check (localhost:8000):
  ✓ MCP server is responding
    Tools available: 42

Resource Usage:
  Memory:
    Mem:  4.2G/7.8G used
    Swap: 0.5G/2.0G used
```

#### 4.2 Force Restart

```bash
# Restart services only
./scripts/wsl-restart.sh

# Full WSL restart (Windows side)
./scripts/wsl-restart.sh --full
```

---

## 🔄 Maintenance

### Daily Checks

```bash
# Cek status
curl http://localhost:8000/health | python3 -m json.tool

# Cek logs
sudo journalctl -u mcp-unified --since "1 hour ago"
sudo journalctl -u wsl-health-monitor --since "1 hour ago"
```

### Weekly Checks

```powershell
# Windows - cek Task Scheduler logs
Get-Content C:\Scripts\wsl-keepalive.log -Tail 50

# WSL - cek resource usage
./scripts/wsl-status.sh
```

### Log Rotation

Windows log auto-rotate saat mencapai 10MB.

WSL logs:
```bash
# Manual cleanup
sudo journalctl --vacuum-size=100M
sudo journalctl --vacuum-time=7d
```

---

## 🐛 Troubleshooting

### WSL Tidak Auto-Start

**Symptom**: Setelah Windows reboot, WSL tidak berjalan

**Check**:
```powershell
# Cek Task Scheduler
Get-ScheduledTask -TaskName "WSL-MCP-KeepAlive"

# Cek last run time
(taskschd.msc) → Task Scheduler Library → WSL-MCP-KeepAlive
```

**Fix**:
```powershell
# Re-run setup
PowerShell.exe -ExecutionPolicy Bypass -File "C:\Scripts\setup-task-scheduler.ps1"
```

---

### MCP Service Tidak Start

**Symptom**: Health check gagal, service inactive

**Check**:
```bash
sudo systemctl status mcp-unified
sudo journalctl -u mcp-unified -n 50
```

**Fix**:
```bash
# Restart
./scripts/wsl-restart.sh

# Atau manual
sudo systemctl restart mcp-unified
```

---

### Port Conflict

**Symptom**: Address already in use

**Check**:
```bash
ss -tuln | grep :8000
lsof -i :8000
```

**Fix**:
```bash
# Kill process yang pakai port 8000
sudo kill -9 $(lsof -t -i:8000)
sudo systemctl restart mcp-unified
```

---

### WSL Memory Issue

**Symptom**: WSL lambat atau out of memory

**Check**:
```bash
free -h
sudo dmesg | tail -20
```

**Fix**:
```ini
# Edit .wslconfig, tambah memory
[wsl2]
memory=12GB  # Naikkan dari 8GB
swap=4GB
```

---

## 📊 Monitoring

### Health Endpoint

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "mcp-unified",
  "version": "1.0.0",
  "transport": "SSE",
  "host": "127.0.0.1",
  "port": 8000,
  "tools_available": 42
}
```

### Windows Event Logs

```powershell
# Cek Task Scheduler events
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-TaskScheduler/Operational'; ID=102,103,110,111} | Select-Object -First 10
```

---

## 🔒 Security Notes

- **Localhost only**: MCP server hanya listen di `127.0.0.1:8000`
- **No external exposure**: Tidak ada port forwarding ke network luar
- **Task runs as SYSTEM**: Task Scheduler berjalan dengan highest privileges
- **Log files**: Pastikan log files tidak readable oleh user lain

---

## 📝 Checklist Setup

- [ ] Copy `.wslconfig` ke `C:\Users\<user>\.wslconfig`
- [ ] Run `wsl --shutdown` dan restart WSL
- [ ] Copy `start-wsl.ps1` ke `C:\Scripts\`
- [ ] Run `setup-task-scheduler.ps1` sebagai Admin
- [ ] Verifikasi Task Scheduler ada task "WSL-MCP-KeepAlive"
- [ ] Copy `wsl-health-monitor.service` ke `/etc/systemd/system/`
- [ ] Enable dan start `wsl-health-monitor` service
- [ ] Test restart Windows → verify WSL auto-start
- [ ] Test health endpoint: `curl http://localhost:8000/health`
- [ ] Monitor logs selama 24 jam pertama

---

## 📞 References

- [MCP Persistent Service](./persistent-service.md)
- [Windows Task Scheduler Docs](https://docs.microsoft.com/en-us/windows/win32/taskschd/task-scheduler-start-page)
- [WSL Configuration](https://docs.microsoft.com/en-us/windows/wsl/wsl-config)
- [systemd.service](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
