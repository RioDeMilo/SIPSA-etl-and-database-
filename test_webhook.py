#!/usr/bin/env python3
"""
test_webhook.py — Simulate both Meta interactions locally.

Run the FastAPI server first:
    cd /agroprecios/app
    uvicorn main:app --reload --port 8000

Then in another terminal:
    python test_webhook.py
"""

import json
import httpx

BASE = "http://localhost:8000"
VERIFY_TOKEN = "agroprecios_verify_token"   # must match your .env

# ─────────────────────────────────────────────────────────────────────────────
# 1. Verification handshake (GET /webhook)
# ─────────────────────────────────────────────────────────────────────────────
print("=== Test 1: Webhook verification ===")
resp = httpx.get(
    f"{BASE}/webhook",
    params={
        "hub.mode": "subscribe",
        "hub.verify_token": VERIFY_TOKEN,
        "hub.challenge": "CHALLENGE_12345",
    },
)
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
assert resp.text == "CHALLENGE_12345", f"Expected challenge echo, got: {resp.text}"
print(f"  ✓ Status: {resp.status_code}")
print(f"  ✓ Body:   {resp.text}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Bad verify token (should return 403)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== Test 2: Bad verify token ===")
resp = httpx.get(
    f"{BASE}/webhook",
    params={
        "hub.mode": "subscribe",
        "hub.verify_token": "wrong_token",
        "hub.challenge": "CHALLENGE_12345",
    },
)
assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
print(f"  ✓ Status: {resp.status_code}  (correctly rejected)")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Incoming text message (POST /webhook)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== Test 3: Incoming text message ===")
payload = {
    "object": "whatsapp_business_account",
    "entry": [
        {
            "id": "ENTRY_ID",
            "changes": [
                {
                    "field": "messages",
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "15550001234",
                            "phone_number_id": "PHONE_NUMBER_ID",
                        },
                        "contacts": [
                            {"profile": {"name": "Agricultor Test"}, "wa_id": "573001234567"}
                        ],
                        "messages": [
                            {
                                "from": "573001234567",
                                "id": "wamid.TEST001",
                                "timestamp": "1700000001",
                                "type": "text",
                                "text": {"body": "Hola, quiero consultar precios"},
                            }
                        ],
                    },
                }
            ],
        }
    ],
}
resp = httpx.post(f"{BASE}/webhook", json=payload)
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
print(f"  ✓ Status: {resp.status_code}")
print(f"  ✓ Response: {resp.json()}")

# ─────────────────────────────────────────────────────────────────────────────
# 4. Incoming list reply (interactive)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== Test 4: Incoming interactive list reply ===")
payload["entry"][0]["changes"][0]["value"]["messages"] = [
    {
        "from": "573001234567",
        "id": "wamid.TEST002",
        "timestamp": "1700000002",
        "type": "interactive",
        "interactive": {
            "type": "list_reply",
            "list_reply": {
                "id": "city_1",
                "title": "Bogotá",
                "description": "",
            },
        },
    }
]
resp = httpx.post(f"{BASE}/webhook", json=payload)
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
print(f"  ✓ Status: {resp.status_code}")
print(f"  ✓ Response: {resp.json()}")

print("\n✅ All tests passed — check the server terminal for log output.")
