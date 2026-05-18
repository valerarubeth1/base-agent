from fastapi import FastAPI
from fastapi.responses import Response
import requests
import json
import base64

app = FastAPI()

WALLET_ADDRESS = "0x801108CA1B7Caf261D2e4a11E7701aF7cD377e8a"

def make_402_response():
    payment_required = {
        "x402Version": 2,
        "accepts": [
    {
        "scheme": "exact",
        "network": "eip155:8453",
        "amount": "10000",
        "resource": {
            "url": "https://base-agent-production.up.railway.app/tokens",
            "description": "Fresh Base token data from DexScreener",
            "mimeType": "application/json"
        },
        "resource.url": "https://base-agent-production.up.railway.app/tokens",
        "payTo": WALLET_ADDRESS,
        "maxTimeoutSeconds": 300,
        "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    }
],
        "error": "Payment required to access this endpoint",
        "extensions": {
            "bazaar": {
                "info": {
                    "name": "Base Token Parser",
                    "description": "Get fresh token data from Base network including price, volume and liquidity",
                    "category": "data",
                    "tags": ["base", "tokens", "defi", "crypto"],
                    "output": {
                        "description": "Returns JSON array of top 10 tokens on Base network with symbol, name, address, price in USD, 24h volume, and liquidity",
                        "contentType": "application/json",
                        "example": {
                            "agent": "Base Token Parser",
                            "wallet": "0x801108CA1B7Caf261D2e4a11E7701aF7cD377e8a",
                            "tokens": [
                                {
                                    "symbol": "USDC",
                                    "name": "USD Coin",
                                    "address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
                                    "price_usd": "1.00",
                                    "volume_24h": 500000,
                                    "liquidity_usd": 1000000,
                                    "url": "https://dexscreener.com/base/0x..."
                                }
                            ],
                            "count": 10
                        }
                    }
                },
                "schema": {
                    "type": "object",
                    "properties": {
                        "agent": {"type": "string"},
                        "wallet": {"type": "string"},
                        "tokens": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "symbol": {"type": "string"},
                                    "name": {"type": "string"},
                                    "address": {"type": "string"},
                                    "price_usd": {"type": "string"},
                                    "volume_24h": {"type": "number"},
                                    "liquidity_usd": {"type": "number"},
                                    "url": {"type": "string"}
                                }
                            }
                        },
                        "count": {"type": "number"}
                    }
                }
            }
        }
    }

    encoded = base64.b64encode(json.dumps(payment_required).encode()).decode()

    return Response(
        status_code=402,
        headers={"PAYMENT-REQUIRED": encoded},
        content=json.dumps({"error": "Payment Required"}),
        media_type="application/json"
    )

@app.get("/")
def home():
    return {
        "agent": "Base Token Parser",
        "wallet": WALLET_ADDRESS,
        "price_per_request": "0.01 USDC",
        "endpoint": "/tokens",
        "network": "base"
    }

@app.get("/tokens")
def get_tokens(tx: str = None):
    if not tx or not tx.startswith("0x") or len(tx) < 60:
        return make_402_response()

    response = requests.get(
        "https://api.dexscreener.com/latest/dex/search?q=base",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    data = response.json()
    pairs = data.get("pairs", [])
    base_tokens = []

    for p in pairs:
        if p.get("chainId") != "base":
            continue
        base_tokens.append({
            "symbol": p.get("baseToken", {}).get("symbol", "???"),
            "name": p.get("baseToken", {}).get("name", "???"),
            "address": p.get("baseToken", {}).get("address", ""),
            "price_usd": p.get("priceUsd", "0"),
            "volume_24h": p.get("volume", {}).get("h24", 0),
            "liquidity_usd": p.get("liquidity", {}).get("usd", 0),
            "url": f"https://dexscreener.com/base/{p.get('pairAddress','')}"
        })
        if len(base_tokens) >= 10:
            break

    return {
        "agent": "Base Token Parser",
        "wallet": WALLET_ADDRESS,
        "paid_with_tx": tx,
        "tokens": base_tokens,
        "count": len(base_tokens)
    }
