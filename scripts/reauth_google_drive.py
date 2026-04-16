#!/usr/bin/env python3
"""
Re-autentikasi Google Drive OAuth2
====================================
Jalankan script ini untuk memperbarui token Google yang expired.
Browser akan terbuka otomatis untuk login.

Jalankan:
  python3 scripts/reauth_google_drive.py
"""
import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

TOKEN_FILE = "/home/aseps/MCP/config/credentials/google/puubangda/token.json"
CLIENT_SECRET_FILE = "/home/aseps/MCP/config/credentials/google/puubangda/client_secret.json"

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/contacts",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/userinfo.profile",
]

print("=== Re-autentikasi Google OAuth2 ===")
print(f"Client secret: {CLIENT_SECRET_FILE}")
print()

flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)

# Coba buka browser lokal, atau tampilkan URL manual
# Coba buka browser lokal
try:
    creds = flow.run_local_server(
        port=0, 
        open_browser=True, 
        success_message='Autentikasi berhasil! Silakan kembali ke terminal.'
    )
except Exception as e:
    print(f"Error: {e}")
    print("\nSilakan ikuti instruksi di atas untuk menyelesaikan autentikasi.")
    exit(1)

# Simpan token baru
token_data = {
    "token": creds.token,
    "refresh_token": creds.refresh_token,
    "token_uri": creds.token_uri,
    "client_id": creds.client_id,
    "client_secret": creds.client_secret,
    "scopes": creds.scopes,
}
with open(TOKEN_FILE, "w") as f:
    json.dump(token_data, f, indent=2)

print(f"\n✅ Token baru disimpan ke: {TOKEN_FILE}")
print("Sekarang jalankan:")
print("  DATABASE_URL='postgresql://aseps:secure123@localhost:5432/mcp' python3 scripts/sync_disposisi_to_gdrive.py")
