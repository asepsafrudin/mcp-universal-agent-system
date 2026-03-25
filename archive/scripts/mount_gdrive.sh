#!/bin/bash
# Mount Google Drive using rclone

MOUNT_POINT="/home/aseps/MCP/google_drive"
LOG_FILE="/home/aseps/MCP/google_drive_mount.log"

# Unmount if already mounted
fusermount -u "$MOUNT_POINT" 2>/dev/null

# Wait a moment
sleep 2

# Mount with rclone
rclone mount gdrive: "$MOUNT_POINT" \
    --vfs-cache-mode writes \
    --vfs-cache-max-size 100M \
    --allow-other \
    --default-permissions \
    --uid $(id -u) \
    --gid $(id -g) \
    --file-perms 0777 \
    --dir-perms 0777 \
    --log-file="$LOG_FILE" \
    --log-level INFO \
    --daemon

sleep 3

# Check if mounted
if mountpoint -q "$MOUNT_POINT"; then
    echo "Google Drive mounted successfully at $MOUNT_POINT"
    echo "Contents:"
    ls -la "$MOUNT_POINT"
else
    echo "Failed to mount Google Drive"
    echo "Check log: $LOG_FILE"
    cat "$LOG_FILE" | tail -20
fi
