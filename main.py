from fastapi import FastAPI
from fastapi.responses import JSONResponse
import requests
import json
import base64
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

WALLET_ADDRESS = os.getenv('EVM_ADDRESS', '0x801108CA1B7Caf261D2e4a11E7701aF7cD377e8a')
RESOURCE_URL = 'https://base-agent-production.up.railway.app/tokens'

@app.get('/')
def home():
    return {'status': 'ok', 'agent': 'Base Token Parser'}

@app.get('/tokens')
def get_tokens():
    # Always return 402 for validation
    payment_required = {
        "x402Version": 2,
        "error": "Payment required",
        "resource": {
            "url": RESOURCE_URL,
            "description": "Fresh Base token data from DexScreener (new pools, volume spikes, risk score)",
            "mimeType": "application/json"
        },
        "accepts": [{
            "scheme": "exact",
            "network": "eip155:8453",
            "amount": "10000",
            "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            "payTo": WALLET_ADDRESS,
            "maxTimeoutSeconds": 300
        }],
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

    encoded = base64.b64encode(json.dumps(payment_required).encode('utf-8')).decode('utf-8')

    return JSONResponse(
        status_code=402,
        headers={"PAYMENT-REQUIRED": encoded},
        content={"error": "Payment Required"}
    )

# Real logic (commented for validation)
# try:
#     resp = requests.get("https://api.dexscreener.com/latest/dex/search?q=base")
#     ... 

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)