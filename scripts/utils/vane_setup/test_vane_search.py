
import requests
import json

VANE_URL = "http://localhost:3001"

# Data dari providers API sebelumnya
PROVIDER_ID = "6907e68d-cf2e-442a-8a60-8da858f043d2" # Groq
MODEL_KEY = "llama-3.1-8b-instant"
EMBED_PROVIDER = "842ef658-523e-49b7-900d-2a24759fd9f6" # Transformers
EMBED_KEY = "Xenova/all-MiniLM-L6-v2"

def test_search():
    payload = {
        "chatModel": {
            "providerId": PROVIDER_ID,
            "key": MODEL_KEY
        },
        "embeddingModel": {
            "providerId": EMBED_PROVIDER,
            "key": EMBED_KEY
        },
        "optimizationMode": "balanced",
        "sources": ["web"],
        "query": "Jelaskan 6 urusan pemerintahan wajib yang berkaitan dengan pelayanan dasar menurut UU 23 Tahun 2014",
        "stream": False
    }
    
    print(f"Sending search query to Vane: {payload['query']}")
    headers = {"Content-Type": "application/json"}
    resp = requests.post(f"{VANE_URL}/api/search", json=payload, headers=headers, timeout=120)
    
    if resp.status_code == 200:
        result = resp.json()
        print("\n=== ANSWER ===")
        print(result.get('message'))
        print("\n=== SOURCES ===")
        for i, source in enumerate(result.get('sources', []), 1):
            meta = source.get('metadata', {})
            print(f"{i}. {meta.get('title')} ({meta.get('url')})")
    else:
        print(f"Error: {resp.status_code}")
        print(resp.text)

if __name__ == "__main__":
    test_search()
