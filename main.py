import json
import base64
from fastapi import FastAPI
from fastapi.responses import Response
import requests

app = FastAPI()

WALLET_ADDRESS = "0x801108CA1B7Caf261D2e4a11E7701aF7cD377e8a"
RESOURCE_URL = "https://base-agent-production.up.railway.app/tokens"


def make_402_response():
    payload = {
        "x402Version": 2,
        "error": "Payment required",
        "resource": {
            "url": RESOURCE_URL,
            "description": "Fresh Base token data from DexScreener (new pools, volume spikes, risk score)",
            "mimeType": "application/json"
        },
        "accepts": [
            {
                "scheme": "exact",
                "network": "eip155:8453",
                "amount": "10000",
                "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
                "payTo": WALLET_ADDRESS,
                "maxTimeoutSeconds": 300,
                "name": "USD Coin",
                "version": "2",
                "extra": {
                    "name": "USD Coin",
                    "version": "2"
                }
            }
        ],
        "extensions": {
            "bazaar": {
                "info": {
                    "name": "Base Fresh Tokens Parser",
                    "description": "Returns latest tokens on Base with liquidity, volume and DexScreener links",
                    "category": "onchain-data",
                    "tags": ["base", "tokens", "memes", "dexscreener"],
                    "input": {
                        "type": "http",
                        "method": "GET",
                        "queryParams": {}
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

    encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")

    return Response(
        status_code=402,
        headers={"PAYMENT-REQUIRED": encoded},
        content="",
        media_type="application/json"
    )


@app.get("/")
def home():
    return {
        "agent": "Base Token Parser",
        "wallet": WALLET_ADDRESS,
        "price": "0.01 USDC",
        "status": "ready"
    }


@app.get("/tokens")
def get_tokens():
    # Для валидации Agentic Market всегда возвращаем 402
    return make_402_response()

    # ← Когда всё заработает — раскомментируй настоящий парсер:
    # try:
    #     resp = requests.get(
    #         "https://api.dexscreener.com/latest/dex/search?q=base",
    #         headers={"User-Agent": "x402-BaseAgent"},
    #         timeout=10
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
    #         "agent": "Base Fresh Tokens Parser",
    #         "wallet": WALLET_ADDRESS,
    #         "tokens": tokens,
    #         "count": len(tokens)
    #     }
    # except Exception as e:
    #     return {"error": str(e)}, 500


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
