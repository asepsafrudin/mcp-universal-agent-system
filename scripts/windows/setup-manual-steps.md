# WSL Always-On Server — Manual Setup Steps

Jika script otomatis tidak berjalan, ikuti langkah manual ini.

---

## Step 1: Konfigurasi WSL (.wslconfig)

### 1.1 Buat file konfigurasi

Copy file `scripts/windows/.wslconfig` ke Windows home directory:

```powershell
# Di PowerShell (sebagai Administrator)
copy "\\wsl$\Ubuntu\home\aseps\MCP\scripts\windows\.wslconfig" "$env:USERPROFILE\.wslconfig"
```

Atau buat manual file di: `C:\Users\<username>\.wslconfig`

Isi file:
```ini
[wsl2]
autoMemoryReclaim=disabled
memory=8GB
processors=4
swap=2GB
localhostForwarding=true
kernelCommandLine=clocksource=tsc

[experimentalfeatures]
autoShutdown=false
```

### 1.2 Apply konfigurasi

```powershell
wsl --shutdown
# Tunggu 10 detik
wsl
```

---

## Step 2: Copy Scripts ke Windows

### 2.1 Buat direktori di Windows

```powershell
New-Item -ItemType Directory -Path "C:\Scripts" -Force
```

### 2.2 Copy scripts

```powershell
copy "\\wsl$\Ubuntu\home\aseps\MCP\scripts\windows\start-wsl.ps1" "C:\Scripts\"
```

---

## Step 3: Buat Scheduled Task (Manual)

### 3.1 Buka Task Scheduler

1. Tekan `Win + R`, ketik `taskschd.msc`, Enter
2. Atau search "Task Scheduler" di Start Menu

### 3.2 Create Basic Task

1. Klik **Create Task** (bukan Create Basic Task)
2. Tab **General**:
   - Name: `WSL-MCP-KeepAlive`
   - Description: `Keep WSL and MCP Unified Hub running`
   - Run whether user is logged on or not: ✅
   - Run with highest privileges: ✅
   - Configure for: Windows 10/11

3. Tab **Triggers**:
   - Klik **New...**
   - Begin the task: **At startup**
   - Delay task for: **2 minutes**
   - ✅ Repeat task every: **5 minutes**
   - For a duration of: **Indefinitely**
   - ✅ Enabled

   - Klik **New...** lagi
   - Begin the task: **At log on**
   - ✅ Any user

4. Tab **Actions**:
   - Klik **New...**
   - Action: **Start a program**
   - Program/script: `PowerShell.exe`
   - Add arguments: `-ExecutionPolicy Bypass -File "C:\Scripts\start-wsl.ps1"`

5. Tab **Conditions**:
   - ☐ Start the task only if computer is on AC power
   - ✅ Start only if the following network connection is available: Any connection

6. Tab **Settings**:
   - ✅ Allow task to be run on demand
   - ✅ If the task fails, restart every: **1 minute**
   - Attempt to restart up to: **3 times**
   - ✅ Stop the task if it runs longer than: **1 hour**

7. Klik **OK** → masukkan password admin

---

## Step 4: Test Task

### 4.1 Manual Run

1. Di Task Scheduler, cari task "WSL-MCP-KeepAlive"
2. Right-click → **Run**
3. Cek log file:
   ```powershell
   Get-Content C:\Scripts\wsl-keepalive.log -Tail 20
   ```

### 4.2 Cek WSL

```bash
# Di WSL
curl http://localhost:8000/health
```

---

## Step 5: Setup Health Monitor (WSL Side)

### 5.1 Copy service file

```bash
cd /home/aseps/MCP
sudo cp scripts/wsl-health-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### 5.2 Enable dan start

```bash
sudo systemctl enable wsl-health-monitor
sudo systemctl start wsl-health-monitor
sudo systemctl status wsl-health-monitor
```

---

## Troubleshooting

### Task tidak jalan

```powershell
# Cek task status
Get-ScheduledTask -TaskName "WSL-MCP-KeepAlive"

# Cek history
taskschd.msc
# → Task Scheduler Library → WSL-MCP-KeepAlive → History tab
```

### PowerShell execution policy

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope LocalMachine
```

### Log file tidak terbuat

Pastikan direktori `C:\Scripts` ada dan writable:
```powershell
Test-Path "C:\Scripts"
New-Item -Path "C:\Scripts\test.txt" -ItemType File
```

### WSL tidak start

```powershell
# Reset WSL
wsl --shutdown
wsl --unregister Ubuntu
wsl --install -d Ubuntu
```

---

## Verifikasi Lengkap

Setelah setup selesai, verifikasi dengan:

1. **Restart Windows** → cek apakah WSL auto-start
2. **Cek health endpoint** → `curl http://localhost:8000/health`
3. **Cek logs** → `journalctl -u mcp-unified -f`
4. **Biarkan 24 jam** → cek apakah service tetap berjalan
