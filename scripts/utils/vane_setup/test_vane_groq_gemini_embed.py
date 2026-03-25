"""
Test Vane: Groq chat + Gemini embedding (tanpa Transformers download)
"""
import requests

VANE_URL = "http://localhost:3000"

# Dari output providers sebelumnya:
# Groq provider yang punya qwen/qwen3-32b
GROQ_PROVIDER_ID = "cb95bef3-6fb1-4581-b1f2-c46563ede645"
# Gemini provider (untuk embedding - sudah live, tidak perlu download)
GEMINI_PROVIDER_ID = "064c4a9f-c7d3-4e41-8e62-8a4363d03ef2"

def run():
    # Pastikan setup sudah complete
    requests.post(f"{VANE_URL}/api/config", json={"key": "setupComplete", "value": True}, timeout=5)

    # Verifikasi model yang tersedia di Groq
    print("=== Cek model Groq ===")
    resp = requests.get(f"{VANE_URL}/api/providers", timeout=10)
    providers = resp.json().get('providers', [])
    for p in providers:
        if p['id'] == GROQ_PROVIDER_ID:
            keys = [m['key'] for m in p.get('chatModels', [])]
            print(f"Groq ({p['id'][:8]}...): {keys[:5]}")
            break

    print("\n=== Testing Search ===")
    print("Chat:  qwen/qwen3-32b  @ Groq")
    print("Embed: gemini-embedding-001 @ Gemini")
    print("Query: '6 urusan pemerintahan wajib UU 23 2014'")
    print("Mode:  speed | Sources: web")
    print("Timeout: 90s\n")

    payload = {
        "chatModel": {
            "providerId": GROQ_PROVIDER_ID,
            "key": "qwen/qwen3-32b"
        },
        "embeddingModel": {
            "providerId": GEMINI_PROVIDER_ID,
            "key": "models/gemini-embedding-001"
        },
        "optimizationMode": "speed",
        "sources": ["web"],
        "query": "6 urusan pemerintahan wajib berkaitan pelayanan dasar UU 23 tahun 2014",
        "stream": False
    }

    try:
        r = requests.post(
            f"{VANE_URL}/api/search",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=90
        )
        if r.status_code == 200:
            result = r.json()
            msg = result.get('message', '')
            srcs = result.get('sources', [])
            print(f"✅ BERHASIL! ({len(msg)} karakter, {len(srcs)} sumber)")
            print(f"\n--- JAWABAN ---\n{msg[:1000]}")
            print(f"\n--- SUMBER ({len(srcs)}) ---")
            for s in srcs[:5]:
                m = s.get('metadata', {})
                print(f"  • [{m.get('title','')[:60]}]\n    {m.get('url','')}")
        else:
            print(f"❌ Error {r.status_code}:\n{r.text[:400]}")
    except requests.Timeout:
        print("❌ TIMEOUT (>90s) — Cek docker logs vane --tail 20")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    run()
