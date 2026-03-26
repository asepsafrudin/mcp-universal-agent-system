
import requests
import json
import uuid

VANE_URL = "http://localhost:3001"
GROQ_API_KEY = "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"

def setup():
    print("Fetching current config...")
    resp = requests.get(f"{VANE_URL}/api/config")
    config = resp.json()
    values = config['values']
    
    # 1. Update Groq
    # Find Groq in modelProviders or add it
    model_providers = values.get('modelProviders', [])
    groq_provider = next((p for p in model_providers if p.get('type') == 'groq'), None)
    
    if not groq_provider:
        # Get ID for groq from fields if possible, or use a new one
        groq_field = next((p for p in config['fields']['modelProviders'] if p['key'] == 'groq'), None)
        groq_provider = {
            "id": str(uuid.uuid4()),
            "name": "Groq",
            "type": "groq",
            "config": {"apiKey": GROQ_API_KEY}
        }
        model_providers.append(groq_provider)
    else:
        groq_provider['config'] = {"apiKey": GROQ_API_KEY}
    
    # 2. Set Setup Complete
    values['setupComplete'] = True
    values['modelProviders'] = model_providers
    
    # 3. Post back updates
    # The API /api/config POST takes {key, value} where value is stringified JSON for many things
    # According to route.ts: configManager.updateConfig(body.key, body.value)
    
    print("Updating setupComplete...")
    requests.post(f"{VANE_URL}/api/config", json={"key": "setupComplete", "value": "true"})
    
    print("Updating modelProviders...")
    requests.post(f"{VANE_URL}/api/config", json={"key": "modelProviders", "value": json.dumps(model_providers)})
    
    print("Setup done.")

if __name__ == "__main__":
    setup()
