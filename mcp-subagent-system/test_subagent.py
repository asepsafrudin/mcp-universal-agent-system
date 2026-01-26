import asyncio
import json
import requests
import time

def test_execute_task():
    """Test tool execute_task pada server sub-agent"""
    # Pastikan server berjalan di port 8001
    url = "http://localhost:8001/"
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "execute_task",
            "arguments": {
                "task_content": "Sebutkan isi direktori saat ini dan simpan ke memori"
            }
        },
        "id": 1
    }
    
    try:
        print("[*] Mengirim tugas ke Sub-Agent System (Port 8001)...")
        print("[*] Payload:", json.dumps(payload, indent=2))
        response = requests.post(url, json=payload, timeout=30)
        print(f"[*] Status Code: {response.status_code}")
        print("[*] Response:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    test_execute_task()
