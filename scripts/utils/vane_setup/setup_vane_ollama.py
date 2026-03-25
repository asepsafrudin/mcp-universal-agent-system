"""
Setup Vane dengan Ollama lokal + test search
Dari Docker, Ollama diakses via Docker bridge: 172.17.0.1:11434
"""
import requests
import json
import uuid
import sys

VANE_URL = "http://localhost:3000"
# Docker gateway IP untuk akses Ollama dari dalam container
OLLAMA_URL_FOR_DOCKER = "http://172.17.0.1:11434"

def get_providers():
    try:
        resp = requests.get(f"{VANE_URL}/api/providers", timeout=10)
        return resp.json()
    except Exception as e:
        print(f"Error: {e}")
        return {}

def setup_ollama():
    """Tambahkan Ollama provider ke Vane."""
    print("=== Step 1: Fetching current config ===")
    resp = requests.get(f"{VANE_URL}/api/config", timeout=10)
    config = resp.json()
    values = config['values']

    # Buat Ollama provider
    ollama_provider = {
        "id": str(uuid.uuid4()),
        "name": "Ollama",
        "type": "ollama",
        "config": {"baseURL": OLLAMA_URL_FOR_DOCKER},
        "chatModels": [],
        "embeddingModels": [],
        "hash": ""
    }

    # Remove existing ollama, tambah yang baru
    current = [p for p in values.get('modelProviders', []) if p.get('type') != 'ollama']
    current.append(ollama_provider)

    print("=== Step 2: Updating setupComplete ===")
    r = requests.post(f"{VANE_URL}/api/config", json={"key": "setupComplete", "value": True}, timeout=10)
    print(f"  -> Status: {r.status_code}")

    print("=== Step 3: Updating modelProviders with Ollama ===")
    r = requests.post(f"{VANE_URL}/api/config", json={"key": "modelProviders", "value": current}, timeout=10)
    print(f"  -> Status: {r.status_code}, {r.text[:100]}")

    print("\n=== Step 4: Verifying providers ===")
    providers = get_providers()
    for p in providers.get('providers', []):
        print(f"  [{p['name']}] chat_models={len(p.get('chatModels',[]))}, embed_models={len(p.get('embeddingModels',[]))}")
        if p['name'] == 'Ollama' and p.get('chatModels'):
            return p['id'], p['chatModels'][0]['key']
    return None, None

def test_search(provider_id, model_key, embed_provider_id, embed_key):
    """Test search dengan timeout pendek."""
    print(f"\n=== Step 5: Testing search ===")
    print(f"  Chat: {model_key} @ provider {provider_id}")
    print(f"  Embed: {embed_key} @ provider {embed_provider_id}")

    payload = {
        "chatModel": {"providerId": provider_id, "key": model_key},
        "embeddingModel": {"providerId": embed_provider_id, "key": embed_key},
        "optimizationMode": "speed",
        "sources": ["web"],
        "query": "urusan pemerintahan wajib UU 23 2014",
        "stream": False
    }

    print("  -> Sending request (timeout 60s)...")
    try:
        resp = requests.post(
            f"{VANE_URL}/api/search",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        if resp.status_code == 200:
            result = resp.json()
            answer = result.get('message', '')
            sources = result.get('sources', [])
            print(f"\n✅ SUCCESS!")
            print(f"Answer ({len(answer)} chars): {answer[:500]}...")
            print(f"\nSources ({len(sources)}):")
            for s in sources[:3]:
                print(f"  - {s.get('metadata',{}).get('url','')}")
        else:
            print(f"❌ Error {resp.status_code}: {resp.text[:200]}")
    except requests.Timeout:
        print("❌ TIMEOUT (>60s) - model terlalu lambat atau SearXNG bermasalah")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    # Setup
    chat_provider_id, chat_model = setup_ollama()

    if not chat_provider_id:
        print("❌ Ollama provider tidak ditemukan di Vane setelah setup")
        sys.exit(1)

    # Dapatkan embed provider (Transformers atau Ollama nomic-embed)
    providers = get_providers()
    embed_provider_id = None
    embed_key = None
    for p in providers.get('providers', []):
        if p['name'] == 'Transformers' and p.get('embeddingModels'):
            embed_provider_id = p['id']
            embed_key = p['embeddingModels'][0]['key']
            break
        if p['name'] == 'Ollama' and p.get('embeddingModels'):
            embed_provider_id = p['id']
            embed_key = p['embeddingModels'][0]['key']
            break

    if embed_provider_id:
        test_search(chat_provider_id, chat_model, embed_provider_id, embed_key)
    else:
        print("❌ Tidak ada embedding model tersedia")
