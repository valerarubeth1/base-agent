from typing import Any
from fastapi import FastAPI, Response, Request
import requests
import json
import base64
import os

app = FastAPI()

PAY_TO = "0x801108CA1B7Caf261D2e4a11E7701aF7cD377e8a"
USDC_ASSET = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
RESOURCE_URL = "https://base-agent-production.up.railway.app/tokens"
FACILITATOR_URL = "https://x402.org/facilitator"

def settle_payment(payment_header: str) -> bool:
    try:
        res = requests.post(
            f"{FACILITATOR_URL}/settle",
            json={
                "x402Version": 2,
                "paymentPayload": payment_header,
                "paymentRequirements": {
                    "scheme": "exact",
                    "network": "eip155:8453",
                    "amount": "1000",
                    "asset": USDC_ASSET,
                    "payTo": PAY_TO,
                    "maxTimeoutSeconds": 300,
                    "extra": {"name": "USD Coin", "version": "2"}
                }
            },
            timeout=10
        )
        print(f"Settle: {res.status_code} {res.text}")
        return res.status_code == 200
    except Exception as e:
        print(f"Settle error: {e}")
        return False

def fetch_hot_tokens():
    try:
        response = requests.get('https://api.dexscreener.com/token-profiles/latest/v1', timeout=5)
        if response.status_code == 200:
            profiles = response.json()
            base_addresses = [p['tokenAddress'] for p in profiles if p.get('chainId') == 'base']
            if base_addresses:
                addrs_str = ','.join(base_addresses[:30])
                pairs_res = requests.get(f'https://api.dexscreener.com/latest/dex/tokens/{addrs_str}', timeout=5)
                if pairs_res.status_code == 200:
                    pairs_data = pairs_res.json().get('pairs', [])
                    tokens_list = []
                    for pair in pairs_data:
                        liquidity = pair.get('liquidity', {}).get('usd', 0)
                        if pair.get('chainId') == 'base' and liquidity >= 5000:
                            tokens_list.append({
                                "symbol": pair.get('baseToken', {}).get('symbol', 'UNKNOWN'),
                                "address": pair.get('baseToken', {}).get('address', ''),
                                "price_usd": pair.get('priceUsd', '0'),
                                "volume_24h": float(pair.get('volume', {}).get('h24', 0)),
                                "liquidity_usd": float(liquidity),
                                "url": pair.get('url', '')
                            })
                    return sorted(tokens_list, key=lambda x: x['volume_24h'], reverse=True)[:10]
    except Exception as e:
        print(f"DexScreener error: {e}")
    return []

def make_402_response():
    payment_envelope = {
        "x402Version": 2,
        "error": "Payment required",
        "resource": {
            "url": RESOURCE_URL,
            "description": "Top Base tokens by 24h volume with liquidity > $5000",
            "mimeType": "application/json"
        },
        "accepts": [
            {
                "scheme": "exact",
                "network": "eip155:8453",
                "amount": "1000",
                "asset": USDC_ASSET,
                "payTo": PAY_TO,
                "maxTimeoutSeconds": 300,
                "extra": {"name": "USD Coin", "version": "2"}
            }
        ],
        "extensions": {
            "bazaar": {
                "info": {
                    "input": {"type": "http", "method": "GET", "queryParams": {}},
                    "output": {
                        "type": "json",
                        "example": {
                            "agent": "Base Token Parser",
                            "count": 10,
                            "tokens": [{"symbol": "TOKEN", "price_usd": "0.001", "volume_24h": 100000}],
                            "wallet": PAY_TO
                        }
                    }
                },
                "schema": {
                    "type": "object",
                    "properties": {
                        "agent": {"type": "string"},
                        "count": {"type": "number"},
                        "tokens": {"type": "array"},
                        "wallet": {"type": "string"}
                    }
                }
            }
        }
    }
    encoded = base64.b64encode(json.dumps(payment_envelope, separators=(',', ':')).encode()).decode()
    return Response(
        status_code=402,
        content=json.dumps({"error": "Payment Required"}),
        media_type="application/json",
        headers={
            "PAYMENT-REQUIRED": encoded,
            "Access-Control-Expose-Headers": "PAYMENT-REQUIRED"
        }
    )

@app.middleware("http")
async def x402_middleware(request: Request, call_next):
    if request.url.path == "/tokens":
        payment_header = request.headers.get("payment-signature")
        if not payment_header:
            return make_402_response()
        print(f"Payment received: {payment_header[:60]}...")
        response = await call_next(request)
        settle_payment(payment_header)
        return response
    return await call_next(request)

@app.get("/")
def home():
    return {"agent": "Base Token Parser", "wallet": PAY_TO, "price": "0.001 USDC", "endpoint": "/tokens"}

@app.get("/tokens")
async def handler() -> dict[str, Any]:
    tokens = fetch_hot_tokens()
    return {"agent": "Base Token Parser", "count": len(tokens), "tokens": tokens, "wallet": PAY_TO}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
