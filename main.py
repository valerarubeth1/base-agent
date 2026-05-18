from fastapi import FastAPI
from fastapi.responses import Response
import requests
import json

app = FastAPI()

WALLET_ADDRESS = "0x801108CA1B7Caf261D2e4a11E7701aF7cD377e8a"
RESOURCE_URL = "https://base-agent-production.up.railway.app/tokens"

def make_402_response():
    payment_required = {
        "x402Version": 2,
        "resource": {
            "url": RESOURCE_URL,
            "description": "Fresh Base token data from DexScreener (new pools, volume spikes, risk score)",
            "mimeType": "application/json"
        },
        "accepts": [
            {
                "scheme": "exact",
                "network": "eip155:8453",
                "amount": "10000",           # 0.01 USDC
                "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC on Base
                "payTo": WALLET_ADDRESS,
                "maxTimeoutSeconds": 300
            }
        ],
        "extensions": {
            "bazaar": {
                "info": {
                    "name": "Base Token Parser",
                    "description": "Get fresh token data from Base network",
                    "category": "onchain-data",
                    "tags": ["base", "tokens", "memes", "dexscreener"],
                    "output": {
                        "description": "JSON with fresh tokens",
                        "contentType": "application/json",
                        "example": {
                            "tokens": [...],
                            "count": 10
                        }
                    }
                }
            }
        }
    }

    return Response(
        status_code=402,
        content=json.dumps(payment_required),
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
def get_tokens():
    # Проверка оплаты через заголовок (x402-client его добавляет)
    payment_header = None  # Здесь можно добавить проверку, если нужно
    # if not payment_header:   # пока закомментировано для теста
    #     return make_402_response()

    # === Основная логика парсера ===
    try:
        resp = requests.get(
            "https://api.dexscreener.com/latest/dex/search?q=base",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        data = resp.json()
        pairs = data.get("pairs", [])

        tokens = []
        for p in pairs:
            if p.get("chainId") != "base":
                continue
            tokens.append({
                "symbol": p.get("baseToken", {}).get("symbol", "???"),
                "name": p.get("baseToken", {}).get("name", "???"),
                "address": p.get("baseToken", {}).get("address", ""),
                "price_usd": p.get("priceUsd", "0"),
                "volume_24h": p.get("volume", {}).get("h24", 0),
                "liquidity_usd": p.get("liquidity", {}).get("usd", 0),
                "url": f"https://dexscreener.com/base/{p.get('pairAddress', '')}"
            })
            if len(tokens) >= 15:
                break

        return {
            "agent": "Base Token Parser",
            "wallet": WALLET_ADDRESS,
            "tokens": tokens,
            "count": len(tokens),
            "timestamp": "2026-05-18"
        }
    except Exception as e:
        return {"error": str(e)}, 500
