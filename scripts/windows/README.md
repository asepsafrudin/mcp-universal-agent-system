# WSL Always-On Server — Windows Scripts

Scripts PowerShell untuk setup WSL auto-start dan monitoring dari sisi Windows.

---

## 📂 Files

| File | Purpose |
|------|---------|
| `.wslconfig` | Konfigurasi global WSL (copy ke `C:\Users\<user>\.wslconfig`) |
| `start-wsl.ps1` | Keep-alive script yang dijalankan oleh Task Scheduler |
| `setup-task-scheduler.ps1` | Auto-setup Task Scheduler (recommended) |
| `setup-manual-steps.md` | Panduan manual jika script otomatis gagal |

---

## 🚀 Quick Setup

### Step 1: Copy .wslconfig

```powershell
# Sebagai Administrator
copy "\\wsl$\Ubuntu\home\aseps\MCP\scripts\windows\.wslconfig" "$env:USERPROFILE\.wslconfig"
wsl --shutdown
```

### Step 2: Copy Scripts

```powershell
New-Item -ItemType Directory -Path "C:\Scripts" -Force
copy "\\wsl$\Ubuntu\home\aseps\MCP\scripts\windows\start-wsl.ps1" "C:\Scripts\"
```

### Step 3: Setup Task Scheduler

```powershell
# Otomatis (recommended)
PowerShell.exe -ExecutionPolicy Bypass -File "\\wsl$\Ubuntu\home\aseps\MCP\scripts\windows\setup-task-scheduler.ps1"
```

Atau manual → lihat [setup-manual-steps.md](./setup-manual-steps.md)

---

## 📝 Task Scheduler Configuration

Task yang dibuat:
- **Name**: `WSL-MCP-KeepAlive`
- **Trigger 1**: At startup (delay 2 min)
- **Trigger 2**: At logon
- **Trigger 3**: Every 5 minutes (repeating)
- **Run as**: SYSTEM
- **Privileges**: Highest

---

## 🔍 Monitoring

### Check Log

```powershell
Get-Content C:\Scripts\wsl-keepalive.log -Tail 20
```

### Check Task Status

```powershell
Get-ScheduledTask -TaskName "WSL-MCP-KeepAlive"
```

### View Task History

1. Open `taskschd.msc`
2. Navigate to: Task Scheduler Library → WSL-MCP-KeepAlive
3. Click "History" tab

---

## 🐛 Troubleshooting

### Task tidak muncul

```powershell
# Cek apakah sudah ada
Get-ScheduledTask | Where-Object {$_.TaskName -like "*WSL*"}
```

### Script tidak jalan

```powershell
# Test manual
PowerShell.exe -ExecutionPolicy Bypass -File "C:\Scripts\start-wsl.ps1"
```

### Execution Policy

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope LocalMachine
```

---

## 📚 References

- [WSL Always-On Server Documentation](../../docs/04-operations/wsl-always-on-server.md)
- [Windows Task Scheduler](https://docs.microsoft.com/en-us/windows/win32/taskschd/task-scheduler-start-page)
