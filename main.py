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

def fetch_hot_tokens():
    tokens_list = []
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
                    for pair in pairs_data:
                        liquidity = pair.get('liquidity', {}).get('usd', 0)
                        if pair.get('chainId') == 'base' and liquidity >= 5000:
                            tokens_list.append({
                                "address": pair.get('baseToken', {}).get('address', ''),
                                "liquidity_usd": float(liquidity),
                                "price_usd": pair.get('priceUsd', '0'),
                                "symbol": pair.get('baseToken', {}).get('symbol', 'UNKNOWN'),
                                "url": pair.get('url', ''),
                                "volume_24h": float(pair.get('volume', {}).get('h24', 0))
                            })
                    return sorted(tokens_list, key=lambda x: x['volume_24h'], reverse=True)[:10]
    except Exception as e:
        print(f"Ошибка парсинга DexScreener: {e}")
    
    return [{
        "address": "0x099880c1676FF3035Ab1E952E5E83b5A81eecB07",
        "liquidity_usd": 77934.83,
        "price_usd": "0.0000009813",
        "symbol": "GNULL",
        "url": "https://dexscreener.com/base/0x3676a19715f72f7a7730cc44b26fc515464642f8634dc7f9e6df2f3d7a2d7b79",
        "volume_24h": 399443.06
    }]

@app.middleware("http")
async def x402_payment_middleware(request: Request, call_next):
    if request.url.path == "/tokens":
        if not request.headers.get("x-payment-proof") and not request.headers.get("X-Payment-Proof"):
            default_tokens = fetch_hot_tokens()
            
            payment_envelope = {
                "x402Version": 2,
                "error": "Payment required",
                "resource": {
                    "url": RESOURCE_URL,
                    "description": "Returns top filtered tokens on Base with liquidity > $5000, sorted by 24h volume.",
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
        "extra": {
            "name": "USD Coin",
            "version": "2"
        },
        "eip712": {
            "domain": {
                "chainId": 8453,
                "name": "USD Coin",
                "verifyingContract": USDC_ASSET,
                "version": "2"
            }
        }
    }
],
                "extensions": {
                    "bazaar": {
                        "info": {
                            "input": {
                                "type": "http",
                                "method": "GET",
                                "queryParams": {}
                            },
                            "output": {
                                "type": "json",
                                "example": {
                                    "agent": "Base Token Parser",
                                    "count": len(default_tokens),
                                    "tokens": default_tokens,
                                    "wallet": PAY_TO
                                }
                            }
                        },
                        "schema": {
                            "type": "object",
                            "properties": {
                                "agent": {"type": "string"},
                                "count": {"type": "number"},
                                "tokens": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "address": {"type": "string"},
                                            "liquidity_usd": {"type": "number"},
                                            "price_usd": {"type": "string"},
                                            "symbol": {"type": "string"},
                                            "url": {"type": "string"},
                                            "volume_24h": {"type": "number"}
                                        }
                                    }
                                },
                                "wallet": {"type": "string"}
                            }
                        }
                    }
                }
            }

            json_str = json.dumps(payment_envelope, separators=(',', ':'))
            encoded_payload = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')

            return Response(
                status_code=402,
                content="",
                headers={
                    "PAYMENT-REQUIRED": encoded_payload,
                    "Access-Control-Expose-Headers": "PAYMENT-REQUIRED"
                }
            )

    return await call_next(request)

@app.get("/tokens")
async def handler() -> dict[str, Any]:
    hot_tokens = fetch_hot_tokens()
    return {
        "agent": "Base Token Parser",
        "count": len(hot_tokens),
        "tokens": hot_tokens,
        "wallet": PAY_TO
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 4021))
    uvicorn.run(app, host="0.0.0.0", port=port)
