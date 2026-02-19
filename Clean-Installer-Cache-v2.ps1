#Requires -Version 5.1
<#
.SYNOPSIS
    Clean-Installer-Cache-v2.ps1
    Pembersihan .msi orphan di C:\Windows\Installer - VERSI PERBAIKAN

.DESCRIPTION
    Menggunakan Windows Installer COM API (Microsoft.Installers.Session)
    untuk query produk yang benar-benar terdaftar dan masih aktif.
    Lalu cross-reference dengan file .msi di folder Installer.
    File yang tidak terlink ke produk manapun = orphan = aman dihapus.

.NOTES
    Jalankan sebagai ADMINISTRATOR.
#>

# ============================================================
# KONFIGURASI
# ============================================================
$InstallerPath = "C:\Windows\Installer"
$BackupRoot = Join-Path $env:USERPROFILE "Documents\MSI_Backup"
$LogFile = Join-Path $BackupRoot "cleanup_log_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
$EnableBackup = $true

# $DryRun = $true  -> cuma laporan, tidak hapus
# $DryRun = $false -> hapus setelah konfirmasi
$DryRun = $false
# ============================================================


function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] [$Level] $Message"
    $color = switch ($Level) { "ERROR" { "Red" } "WARN" { "Yellow" } "SUCCESS" { "Green" } default { "Cyan" } }
    Write-Host $line -ForegroundColor $color
    if ($LogFile -and (Test-Path (Split-Path $LogFile))) {
        Add-Content -Path $LogFile -Value $line
    }
}

function Get-LinkedMSIFiles {
    <#
        Pakai Windows Installer COM API untuk:
        1. Ambil semua produk yang terinstall (Win32_Product)
        2. Ambil LocalPackage (path ke .msi cache di C:\Windows\Installer)
        Hasilnya = hashtable berisi filename .msi yang masih dipakai.
    #>
    $linked = @{}

    try {
        # Metode 1: Win32_Product — ambil IdentifyingNumber + LocalPackage
        # LocalPackage adalah path sebenarnya di C:\Windows\Installer\xxxx.msi
        $products = Get-CimInstance -ClassName Win32_Product -ErrorAction SilentlyContinue
        foreach ($p in $products) {
            # Cek LocalPackage (ini yang valid untuk cache)
            if ($p.PSObject.Properties["LocalPackage"] -and $p.LocalPackage) {
                $fn = [System.IO.Path]::GetFileName($p.LocalPackage).ToLower()
                if ($fn -match "\.msi$") {
                    $linked[$fn] = "$($p.Name) (Win32_Product)"
                }
            }
        }
        Write-Log "Win32_Product query selesai."
    }
    catch {
        Write-Log "Win32_Product gagal: $_" "WARN"
    }

    # Metode 2: Scan registry HKLM\SOFTWARE\Classes\Installer\Products\{GUID}\LocalPackage
    # Note: Di Registry, key-nya seringkali "LocalPackage" atau hanya ada "PackageCode" yang merujuk ke file
    # Kita cek 'LocalPackage' jika ada.
    $regBase = "HKLM:\SOFTWARE\Classes\Installer\Products"
    if (Test-Path $regBase) {
        Get-ChildItem -Path $regBase -ErrorAction SilentlyContinue | ForEach-Object {
            try {
                $lp = Get-ItemPropertyValue -Path $_.PSPath -Name "LocalPackage" -ErrorAction SilentlyContinue
                if ($lp) {
                    $fn = [System.IO.Path]::GetFileName($lp).ToLower()
                    if ($fn -match "\.msi$") {
                        if (-not $linked.ContainsKey($fn)) {
                            $linked[$fn] = "Registry: $($_.PSChildName)"
                        }
                    }
                }
            }
            catch {}
        }
    }

    # Metode 3: Scan HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer\UserData
    # Ini lokasi yang lebih lengkap untuk LocalPackage
    $userDataBase = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer\UserData"
    if (Test-Path $userDataBase) {
        # UserData folder struct: S-1-5-18\Products\{GUID}\InstallProperties -> LocalPackage
        Get-ChildItem -Path $userDataBase -Recurse -Filter "InstallProperties" -ErrorAction SilentlyContinue | ForEach-Object {
            try {
                $lp = Get-ItemPropertyValue -Path $_.PSPath -Name "LocalPackage" -ErrorAction SilentlyContinue
                if ($lp) {
                    $fn = [System.IO.Path]::GetFileName($lp).ToLower()
                    if ($fn -match "\.msi$") {
                        if (-not $linked.ContainsKey($fn)) {
                            $linked[$fn] = "UserData Registry"
                        }
                    }
                }
            }
            catch {}
        }
    }

    return $linked
}


# ============================================================
# MAIN
# ============================================================

if ($EnableBackup) {
    New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
}

Write-Log "=================================================="
Write-Log "  MSI Installer Cache Cleanup v2 - START"
Write-Log "  DryRun  : $DryRun"
Write-Log "  Backup  : $EnableBackup"
Write-Log "=================================================="

# --- Step 1: Scan semua .msi ---
Write-Log "Scanning $InstallerPath ..."
$allMSI = Get-ChildItem -Path $InstallerPath -Filter "*.msi" -ErrorAction SilentlyContinue
$totalCount = $allMSI.Count
$totalSizeMB = [math]::Round(($allMSI | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
Write-Log "Ditemukan $totalCount file .msi | Total: $totalSizeMB MB"

# --- Step 2: Cari .msi yang masih dipakai ---
Write-Log "Mencari .msi yang masih di-link ke produk aktif..."
$linkedFiles = Get-LinkedMSIFiles
Write-Log "File .msi yang masih dipakai: $($linkedFiles.Count)"

# Tampilkan yang linked
if ($linkedFiles.Count -gt 0) {
    Write-Log ""
    Write-Log "=== FILE .MSI YANG MASIH DIPAKAI (JANGAN HAPUS) ==="
    $linkedFiles.Keys | Sort-Object | ForEach-Object {
        $sizeMB = 0
        $fullPath = Join-Path $InstallerPath $_
        if (Test-Path $fullPath) {
            $sizeMB = [math]::Round((Get-Item $fullPath).Length / 1MB, 2)
        }
        Write-Log "  [LINKED] $_ ($sizeMB MB) <- $($linkedFiles[$_])"
    }
    Write-Log ""
}

# --- Step 3: Identifikasi orphan ---
Write-Log "Mengidentifikasi file orphan..."

# Pakai array of PSCustomObject supaya Measure-Object bisa kerja
$orphanList = [System.Collections.Generic.List[PSCustomObject]]::new()
$linkedList = [System.Collections.Generic.List[PSCustomObject]]::new()

foreach ($msi in $allMSI) {
    $name = $msi.Name.ToLower()
    $sizeMB = [math]::Round($msi.Length / 1MB, 2)
    $obj = [PSCustomObject]@{
        Name   = $msi.Name
        SizeMB = $sizeMB
        Path   = $msi.FullName
    }

    if ($linkedFiles.ContainsKey($name)) {
        $linkedList.Add($obj)
    }
    else {
        $orphanList.Add($obj)
    }
}

# Hitung total ukuran orphan - sekarang pakai PSCustomObject, Measure-Object works
$orphanSizeMB = [math]::Round(($orphanList | Measure-Object -Property SizeMB -Sum).Sum, 2)

Write-Log "---------------------------------------------------"
Write-Log "  Linked (aman, jangan hapus) : $($linkedList.Count) file"
Write-Log "  Orphan (bisa dihapus)       : $($orphanList.Count) file"
Write-Log "  Ukuran orphan total         : $orphanSizeMB MB ($([math]::Round($orphanSizeMB / 1024, 2)) GB)"
Write-Log "---------------------------------------------------"

# --- Step 4: Top 15 orphan terbesar ---
Write-Log ""
Write-Log "=== TOP 15 ORPHAN TERBESAR ==="
$orphanList | Sort-Object -Property SizeMB -Descending | Select-Object -First 15 | ForEach-Object {
    Write-Log "  $($_.Name)   ->   $($_.SizeMB) MB"
}
Write-Log ""

# --- Step 5: Dry Run atau Hapus ---
if ($orphanList.Count -eq 0) {
    Write-Log "Tidak ada file orphan. Selesai." "SUCCESS"
    exit 0
}

if ($DryRun) {
    Write-Log "=============================================" "WARN"
    Write-Log "  MODE DRY RUN - tidak ada yang dihapus." "WARN"
    Write-Log "  Untuk eksekusi hapus:" "WARN"
    Write-Log "  Buka script, ubah: \$DryRun = \$false" "WARN"
    Write-Log "  Lalu jalankan lagi." "WARN"
    Write-Log "=============================================" "WARN"
    exit 0
}

# --- Konfirmasi sebelum hapus ---
Write-Host ""
Write-Host "=============================================" -ForegroundColor Yellow
Write-Host "  SIAP MENGHAPUS $($orphanList.Count) file orphan" -ForegroundColor Yellow
Write-Host "  Ruang yang akan bebas: $orphanSizeMB MB ($([math]::Round($orphanSizeMB / 1024, 2)) GB)" -ForegroundColor Yellow
if ($EnableBackup) {
    Write-Host "  Backup ke: $BackupRoot" -ForegroundColor Yellow
}
Write-Host "=============================================" -ForegroundColor Yellow
$confirm = Read-Host "Lanjut? (y/n)"

if ($confirm -ne "y") {
    Write-Log "Dibatalkan oleh user." "WARN"
    exit 0
}

# --- Eksekusi hapus ---
$deletedCount = 0
$deletedSizeMB = 0
$errorCount = 0

foreach ($item in $orphanList) {
    try {
        if ($EnableBackup) {
            Copy-Item -Path $item.Path -Destination $BackupRoot -Force -ErrorAction Stop
        }
        Remove-Item -Path $item.Path -Force -ErrorAction Stop
        $deletedCount++
        $deletedSizeMB += $item.SizeMB
        Write-Log "Dihapus: $($item.Name) ($($item.SizeMB) MB)" "SUCCESS"
    }
    catch {
        $errorCount++
        Write-Log "GAGAL: $($item.Name) - $_" "ERROR"
    }
}

# --- Laporan Akhir ---
Write-Log ""
Write-Log "=================================================="
Write-Log "  LAPORAN AKHIR"
Write-Log "=================================================="
Write-Log "  Berhasil dihapus : $deletedCount file"
Write-Log "  Ruang dibebaskan : $([math]::Round($deletedSizeMB, 2)) MB ($([math]::Round($deletedSizeMB / 1024, 2)) GB)"
Write-Log "  Error (skipped)  : $errorCount file"
if ($EnableBackup) { Write-Log "  Backup di        : $BackupRoot" }
Write-Log "  Log              : $LogFile"
Write-Log "=================================================="
Write-Log "Selesai." "SUCCESS"