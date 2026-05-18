import json
import base64
from fastapi import FastAPI
from fastapi.responses import Response

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
                "amount": "10000",                  # 0.01 USDC
                "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
                "payTo": WALLET_ADDRESS,
                "maxTimeoutSeconds": 300,
                "name": "USD Coin",                 # ← обязательно
                "version": "2",                     # ← обязательно
                "extra": {                          # ← обязательно для клиента
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
    return {"status": "ok", "price": "0.01 USDC"}


@app.get("/tokens")
def get_tokens():
    return make_402_response()   # пока только 402 для теста


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
