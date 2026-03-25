#!/bin/bash
# Unmount Google Drive

MOUNT_POINT="/home/aseps/MCP/google_drive"

echo "Unmounting Google Drive from $MOUNT_POINT..."
fusermount -u "$MOUNT_POINT" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "Google Drive unmounted successfully"
else
    echo "Failed to unmount or not mounted"
fi
