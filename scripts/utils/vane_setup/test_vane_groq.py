"""Test Vane dengan Groq qwen/qwen3-32b dan Ollama llama3.2:3b"""
import requests
import json

VANE_URL = "http://localhost:3000"

def run():
    # Cek providers
    print("=== Providers ===")
    resp = requests.get(f"{VANE_URL}/api/providers", timeout=10)
    data = resp.json()
    
    groq_id = None
    groq_model = None
    ollama_id = None
    ollama_embed = None
    trans_id = None
    trans_embed = None
    
    for p in data.get('providers', []):
        models = [m['key'] for m in p.get('chatModels', [])[:3]]
        embeds = [m['key'] for m in p.get('embeddingModels', [])[:2]]
        print(f"  [{p['name']}] id={p['id'][:8]}... chat={models} embed={embeds}")
        
        if p['name'] == 'Groq':
            groq_id = p['id']
            # Pilih qwen/qwen3-32b
            all_keys = [m['key'] for m in p.get('chatModels', [])]
            if 'qwen/qwen3-32b' in all_keys:
                groq_model = 'qwen/qwen3-32b'
            elif all_keys:
                groq_model = all_keys[0]
                
        if p['name'] == 'Ollama':
            ollama_id = p['id']
            e_models = p.get('embeddingModels', [])
            if e_models:
                ollama_embed = e_models[0]['key']
                
        if p['name'] == 'Transformers':
            trans_id = p['id']
            tr_e = p.get('embeddingModels', [])
            if tr_e:
                trans_embed = tr_e[0]['key']
    
    # Tentukan chat + embed
    chat_pid = groq_id
    chat_model = groq_model
    embed_pid = ollama_id or trans_id
    embed_key = ollama_embed or trans_embed
    
    print(f"\n=== Pilihan Model ===")
    print(f"Chat:  {chat_model} @ {chat_pid}")
    print(f"Embed: {embed_key} @ {embed_pid}")
    
    if not chat_pid or not chat_model:
        print("❌ Tidak ada chat provider")
        return
    if not embed_pid or not embed_key:
        print("❌ Tidak ada embed provider")
        return
    
    # Setup complete
    requests.post(f"{VANE_URL}/api/config", json={"key": "setupComplete", "value": True}, timeout=5)
    
    # Test search
    print("\n=== Testing Search (timeout=90s) ===")
    payload = {
        "chatModel": {"providerId": chat_pid, "key": chat_model},
        "embeddingModel": {"providerId": embed_pid, "key": embed_key},
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
            print(f"\n✅ BERHASIL! ({len(msg)} karakter)")
            print(f"\n--- JAWABAN ---")
            print(msg[:800])
            print(f"\n--- SUMBER ({len(srcs)}) ---")
            for s in srcs[:5]:
                m = s.get('metadata', {})
                print(f"  [{m.get('title','-')[:60]}] {m.get('url','')}")
        else:
            print(f"❌ Error {r.status_code}: {r.text[:300]}")
    except requests.Timeout:
        print("❌ TIMEOUT (>90s)")
    except Exception as e:
        print(f"❌ {e}")

if __name__ == "__main__":
    run()
