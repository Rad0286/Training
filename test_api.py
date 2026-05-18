"""Quick test of the TR endpoint connection."""
import sys
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

token = os.getenv("TR_ESSO_TOKEN", "")
print(f"Token length : {len(token)}")
print(f"Token preview: {token[:40]}...")

url = "https://aiopenarena.gcs.int.thomsonreuters.com/v3/inference"

payload = {
    "workflow_id": "4de98216-8278-49cc-a549-dcbf269588ab",
    "query": "Say hello in one sentence.",
    "is_persistence_allowed": False,
    "modelparams": {
        "system_prompt_LLM_task": {
            "system_prompt": "You are a helpful assistant."
        },
        "llm_LLM_task": {
            "effort": "high",
            "output_schema": {},
            "max_tokens": "500",
            "enable_websearch": "False",
            "enable_reasoning": "False"
        }
    },
    "input_variables": {},
    "conversation_id": None
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"bearer {token}"
}

print("\nSending test request to TR endpoint...")
try:
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
    print(f"HTTP Status : {r.status_code}")
    print(f"Response    : {r.text[:800]}")
except requests.exceptions.ConnectionError as e:
    print(f"Connection error (may need VPN): {e}")
except requests.exceptions.Timeout:
    print("Request timed out after 60 seconds.")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")