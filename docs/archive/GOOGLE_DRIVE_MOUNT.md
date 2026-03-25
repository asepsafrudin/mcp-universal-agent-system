# Google Drive Mount

Symlink/mount untuk folder Google Drive: https://drive.google.com/drive/folders/1xo4r9AhvvQhElViLBApZOMh4K1PzAZ21

## Lokasi Mount

```
/home/aseps/MCP/google_drive
```

## Setup

### 1. Instalasi (Sudah Selesai)

```bash
# Install rclone dan fuse3
sudo apt install -y rclone fuse3

# Enable user_allow_other di fuse
echo "user_allow_other" | sudo tee -a /etc/fuse.conf
```

### 2. Konfigurasi

File konfigurasi: `~/.config/rclone/rclone.conf`

```ini
[gdrive]
type = drive
scope = drive
service_account_file = /home/aseps/MCP/OneDrive_PUU/PUU_2026/MCP/credential/gdrive/oval-fort-461712-c0-78646012bddb.json
root_folder_id = 1xo4r9AhvvQhElViLBApZOMh4K1PzAZ21
```

## Penggunaan

### Mount Manual

```bash
# Mount
/home/aseps/MCP/mount_gdrive.sh

# Unmount
/home/aseps/MCP/unmount_gdrive.sh
```

### Auto-mount dengan Systemd

```bash
# Enable auto-mount on boot
/home/aseps/MCP/mcp-unified/systemd/enable_gdrive_mount.sh

# Atau manual:
systemctl --user start gdrive-mount.service
systemctl --user stop gdrive-mount.service
systemctl --user status gdrive-mount.service
```

### Verifikasi Mount

```bash
df -h | grep google_drive
ls -la /home/aseps/MCP/google_drive
```

## Troubleshooting

### Mount Failed

```bash
# Check log
tail -f /home/aseps/MCP/google_drive_mount.log

# Cek apakah user_allow_other sudah di-set
grep user_allow_other /etc/fuse.conf

# Force unmount jika stuck
fusermount -u /home/aseps/MCP/google_drive
```

### Permission Denied

Pastikan service account sudah di-share ke folder Google Drive:
1. Buka Google Drive
2. Share folder dengan email service account: `...@oval-fort-461712-c0.iam.gserviceaccount.com`

## Isi Folder

Folder berisi:
- Dokumen PUU (PDF)
- Folder: Perpres penghargaan olahraga
- Folder: SE dukungan Sensus Ekonomi
- Folder: Telegram bot
- Folder: Tugas Dirjen
- Folder: orientasi pppk
- Folder: sekolah terintegrasi
- Folder: tim monev R2P aceh sumatera
- Dan file-file lainnya

## Log File

```
/home/aseps/MCP/google_drive_mount.log
```
