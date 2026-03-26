"""
Test Vane: groq/compound-mini (support response_format) + Gemini embedding
"""
import requests

VANE_URL = "http://localhost:3001"

# Provider IDs dari output sebelumnya
GROQ_PROVIDER_IDS = [
    "9eb9873d-a50c-4a81-a89c-60cb1e61c399",  # Groq set 1
    "cb95bef3-6fb1-4581-b1f2-c46563ede645",  # Groq set 2
]
GEMINI_PROVIDER_ID = "064c4a9f-c7d3-4e41-8e62-8a4363d03ef2"  # Gemini embedding

# Model yang support response_format di Groq
# Prioritas: compound-mini > llama-4-scout > compound
CANDIDATE_MODELS = [
    "groq/compound-mini",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "groq/compound",
]

def find_provider_for_model(model_key):
    """Cari provider_id yang punya model ini."""
    resp = requests.get(f"{VANE_URL}/api/providers", timeout=10)
    providers = resp.json().get('providers', [])
    for p in providers:
        keys = [m['key'] for m in p.get('chatModels', [])]
        if model_key in keys:
            return p['id']
    return None

def test_search(chat_provider_id, chat_model, embed_provider_id, embed_key):
    payload = {
        "chatModel": {"providerId": chat_provider_id, "key": chat_model},
        "embeddingModel": {"providerId": embed_provider_id, "key": embed_key},
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
        return r.status_code, r.json() if r.status_code == 200 else r.text[:300]
    except requests.Timeout:
        return "TIMEOUT", None
    except Exception as e:
        return "ERROR", str(e)

def run():
    requests.post(f"{VANE_URL}/api/config", json={"key": "setupComplete", "value": True}, timeout=5)

    for model in CANDIDATE_MODELS:
        provider_id = find_provider_for_model(model)
        if not provider_id:
            print(f"⚠️  {model} — tidak ditemukan di provider manapun, skip")
            continue

        print(f"\n{'='*60}")
        print(f"Testing: {model}")
        print(f"Provider: {provider_id[:8]}...")
        print(f"Embed:    gemini-embedding-001")
        print(f"{'='*60}")

        status, result = test_search(
            provider_id, model,
            GEMINI_PROVIDER_ID, "models/gemini-embedding-001"
        )

        if status == 200:
            msg = result.get('message', '')
            srcs = result.get('sources', [])
            print(f"\n✅ BERHASIL dengan model: {model}")
            print(f"Jawaban ({len(msg)} karakter):\n{msg[:800]}")
            print(f"\nSumber ({len(srcs)}):")
            for s in srcs[:5]:
                m = s.get('metadata', {})
                print(f"  • {m.get('url','')}")
            print(f"\n🎯 Model terbaik: {model} (provider: {provider_id})")
            return  # Berhasil, stop
        elif status == "TIMEOUT":
            print(f"❌ TIMEOUT (>90s) — SearxNG mungkin lambat scraping")
        else:
            print(f"❌ Error {status}: {result}")
            # Coba model berikutnya

    print("\n❌ Semua model gagal. Lihat docker logs vane --tail 20")

if __name__ == "__main__":
    run()
