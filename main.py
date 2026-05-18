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
                "amount": "10000",                    # 0.01 USDC (6 decimals)
                "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
                "payTo": WALLET_ADDRESS,
                "maxTimeoutSeconds": 300
            }
        ],
        "extensions": {
            "bazaar": {
                "info": {
                    "name": "Base Fresh Tokens Parser",
                    "description": "Returns latest tokens on Base with liquidity, volume and DexScreener links",
                    "category": "onchain-data",
                    "tags": ["base", "tokens", "memes", "dexscreener"],
                    "output": {
                        "description": "JSON with fresh tokens",
                        "contentType": "application/json",
                        "example": {
                            "tokens": [
                                {
                                    "symbol": "EXAMPLE",
                                    "address": "0x...",
                                    "price_usd": "0.0123",
                                    "volume_24h": 450000,
                                    "liquidity_usd": 125000,
                                    "url": "https://dexscreener.com/base/..."
                                }
                            ],
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
        "endpoint": "/tokens"
    }


@app.get("/tokens")
def get_tokens():
    # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←
    # Для Agentic Market всегда возвращаем 402, пока не оплатил
    return make_402_response()

    # ← Раскомментируй ниже, когда будешь тестировать оплату
    # try:
    #     resp = requests.get(
    #         "https://api.dexscreener.com/latest/dex/search?q=base",
    #         headers={"User-Agent": "x402-BaseAgent"},
    #         timeout=8
    #     )
    #     data = resp.json()
    #     pairs = data.get("pairs", [])[:15]

    #     tokens = []
    #     for p in pairs:
    #         if p.get("chainId") != "base":
    #             continue
    #         tokens.append({
    #             "symbol": p.get("baseToken", {}).get("symbol", "???"),
    #             "address": p.get("baseToken", {}).get("address", ""),
    #             "price_usd": p.get("priceUsd", "0"),
    #             "volume_24h": p.get("volume", {}).get("h24", 0),
    #             "liquidity_usd": p.get("liquidity", {}).get("usd", 0),
    #             "url": f"https://dexscreener.com/base/{p.get('pairAddress','')}"
    #         })

    #     return {
    #         "agent": "Base Token Parser",
    #         "wallet": WALLET_ADDRESS,
    #         "tokens": tokens,
    #         "count": len(tokens),
    #         "timestamp": "2026-05-18"
    #     }
    # except Exception as e:
    #     return {"error": str(e)}, 500
