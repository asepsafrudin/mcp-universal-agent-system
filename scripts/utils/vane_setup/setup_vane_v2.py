import requests
import json
import os
import uuid

VANE_URL = "http://localhost:3001"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

def setup():
    if not GROQ_API_KEY:
        print("GROQ_API_KEY belum diset. Abort.")
        return

    print("Fetching current config...")
    try:
        resp = requests.get(f"{VANE_URL}/api/config")
        config = resp.json()
    except Exception as e:
        print(f"Failed to connect to Vane: {e}")
        return

    values = config['values']
    
    # Prepare modelProviders as actual list of dicts
    groq_provider = {
        "id": str(uuid.uuid4()),
        "name": "Groq",
        "type": "groq",
        "config": {"apiKey": GROQ_API_KEY},
        "chatModels": [],
        "embeddingModels": [],
        "hash": "" # Vane will probably regenerate hash or I can leave it
    }
    
    # We want to replace or add Groq
    current_providers = [p for p in values.get('modelProviders', []) if p.get('type') != 'groq']
    current_providers.append(groq_provider)
    
    # 1. Update setupComplete with BOOLEAN true
    print("Updating setupComplete (boolean)...")
    r1 = requests.post(f"{VANE_URL}/api/config", json={"key": "setupComplete", "value": True})
    print(f"Status: {r1.status_code}, Response: {r1.text}")
    
    # 2. Update modelProviders with LIST
    print("Updating modelProviders (list)...")
    r2 = requests.post(f"{VANE_URL}/api/config", json={"key": "modelProviders", "value": current_providers})
    print(f"Status: {r2.status_code}, Response: {r2.text}")
    
    print("Setup attempt finished.")

if __name__ == "__main__":
    setup()
