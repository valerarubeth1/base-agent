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
                "amount": "10000",
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
    return make_402_response()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
