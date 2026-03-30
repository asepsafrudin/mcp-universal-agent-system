#!/usr/bin/env python3
"""
Exchange authorization code → OAuth2 token untuk puu.bangda@gmail.com

Cara pakai:
1. Jalankan step 1 untuk dapatkan URL auth:
   python3 scripts/exchange_auth_code.py --get-url

2. Buka URL di browser, login sebagai puu.bangda@gmail.com, izinkan akses
   Browser akan redirect ke http://localhost:8080/?code=...&state=...
   (halaman akan error/kosong - itu normal)

3. Copy FULL URL dari address bar browser, lalu jalankan:
   python3 scripts/exchange_auth_code.py --code "URL_LENGKAP_DARI_BROWSER"
"""
import json, sys, os, argparse
import urllib.parse

CLIENT_SECRET_FILE = "/home/aseps/MCP/config/credentials/google/puubangda/client_secret.json"
TOKEN_FILE         = "/home/aseps/MCP/config/credentials/google/puubangda/token.json"
STATE_FILE         = "/tmp/puubangda_oauth_state.json"
REDIRECT_URI       = "http://localhost:8080/"
SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]

def get_url():
    import requests, secrets, hashlib, base64
    # Generate PKCE code verifier & challenge
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode()
    state = secrets.token_urlsafe(16)

    with open(CLIENT_SECRET_FILE) as f:
        cs = json.load(f)
    installed = cs.get("installed") or cs.get("web")
    client_id = installed["client_id"]

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode(params)

    # Simpan state dan verifier
    with open(STATE_FILE, "w") as f:
        json.dump({"state": state, "code_verifier": code_verifier}, f)

    print("\n" + "="*70)
    print("1. BUKA URL INI DI BROWSER (login sbg puu.bangda@gmail.com):")
    print("="*70)
    print(auth_url)
    print("="*70)
    print("\n2. Setelah login & izinkan akses:")
    print("   Browser akan redirect ke http://localhost:8080/?code=...&state=...")
    print("   (halaman akan error/kosong - itu NORMAL)")
    print("\n3. Copy FULL URL dari address bar browser, lalu jalankan:")
    print("   python3 scripts/exchange_auth_code.py --code 'URL_DARI_BROWSER'")


def exchange_code(redirect_url: str):
    parsed = urllib.parse.urlparse(redirect_url)
    params = urllib.parse.parse_qs(parsed.query)

    code = params.get("code", [None])[0]
    if not code:
        # Mungkin langsung paste code saja
        code = redirect_url.strip()

    if not code:
        print("ERROR: Tidak bisa menemukan authorization code")
        sys.exit(1)

    with open(STATE_FILE) as f:
        saved = json.load(f)
    code_verifier = saved.get("code_verifier", "")

    with open(CLIENT_SECRET_FILE) as f:
        cs = json.load(f)
    installed = cs.get("installed") or cs.get("web")

    import requests
    resp = requests.post("https://oauth2.googleapis.com/token", data={
        "code": code,
        "client_id": installed["client_id"],
        "client_secret": installed["client_secret"],
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
        "code_verifier": code_verifier,
    })
    resp.raise_for_status()
    tok = resp.json()

    token_data = {
        "token": tok["access_token"],
        "refresh_token": tok.get("refresh_token"),
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": installed["client_id"],
        "client_secret": installed["client_secret"],
        "scopes": SCOPES,
    }
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)

    print(f"\n✅ Token berhasil disimpan ke: {TOKEN_FILE}")
    print("\nSekarang jalankan sync:")
    print("  DATABASE_URL='postgresql://aseps:secure123@localhost:5432/mcp' python3 scripts/sync_disposisi_to_gdrive.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--get-url", action="store_true", help="Generate auth URL")
    parser.add_argument("--code", help="Redirect URL atau auth code dari browser")
    args = parser.parse_args()

    if args.get_url:
        get_url()
    elif args.code:
        exchange_code(args.code)
    else:
        # Default: generate URL
        get_url()
