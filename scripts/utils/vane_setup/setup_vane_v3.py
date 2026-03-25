
import requests
import json
import uuid

VANE_URL = "http://localhost:3000"
GROQ_API_KEY = "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"
GEMINI_API_KEY = "AIzaSyCm7b-z_acPbex-tthNPcwKKHY3y83xNAg"

def setup():
    print("Fetching current config...")
    resp = requests.get(f"{VANE_URL}/api/config")
    config = resp.json()
    values = config['values']
    
    model_providers = []
    
    # Add Transformers (for embedding)
    trans_provider = {
        "id": str(uuid.uuid4()),
        "name": "Transformers",
        "type": "transformers",
        "config": {},
        "chatModels": [],
        "embeddingModels": [],
        "hash": ""
    }
    model_providers.append(trans_provider)

    # Add Groq
    groq_provider = {
        "id": str(uuid.uuid4()),
        "name": "Groq",
        "type": "groq",
        "config": {"apiKey": GROQ_API_KEY},
        "chatModels": [],
        "embeddingModels": [],
        "hash": ""
    }
    model_providers.append(groq_provider)
    
    # Add Gemini
    gemini_provider = {
        "id": str(uuid.uuid4()),
        "name": "Gemini",
        "type": "gemini",
        "config": {"apiKey": GEMINI_API_KEY},
        "chatModels": [],
        "embeddingModels": [],
        "hash": ""
    }
    model_providers.append(gemini_provider)
    
    values['setupComplete'] = True
    values['modelProviders'] = model_providers
    
    print("Updating setupComplete...")
    requests.post(f"{VANE_URL}/api/config", json={"key": "setupComplete", "value": True})
    
    print("Updating modelProviders...")
    requests.post(f"{VANE_URL}/api/config", json={"key": "modelProviders", "value": model_providers})
    
    print("Setup done.")

if __name__ == "__main__":
    setup()
