from fastapi import FastAPI
from fastapi.responses import JSONResponse
import requests
import json
import base64
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# Жестко объявляем адреса строками
WALLET_ADDRESS = "0x801108CA1B7Caf261D2e4a11E7701aF7cD377e8a"
USDC_ASSET = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
RESOURCE_URL = "https://base-agent-production.up.railway.app/tokens"

@app.get('/')
def home():
    return {'status': 'ok', 'agent': 'Base Token Parser'}

@app.get('/tokens')
def get_tokens():
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
                                "symbol": pair.get('baseToken', {}).get('symbol', 'UNKNOWN'),
                                "address": pair.get('baseToken', {}).get('address', ''),
                                "price_usd": pair.get('priceUsd', '0'),
                                "volume_24h": float(pair.get('volume', {}).get('h24', 0)),
                                "liquidity_usd": float(liquidity),
                                "url": pair.get('url', '')
                            })
                    tokens_list = sorted(tokens_list, key=lambda x: x['volume_24h'], reverse=True)[:10]
    except Exception as e:
        print(f"Ошибка парсинга DexScreener: {e}")

    payment_required = {
        "x402Version": 2,
        "error": "Payment required",
        "resource": {
            "url": str(RESOURCE_URL),
            "description": f"Top {len(tokens_list)} sorted hot Base tokens with liquidity > $5k and high volume.",
            "mimeType": "application/json"
        },
        "accepts": [{
            "scheme": "exact",
            "network": "eip155:8453",
            "amount": "1000",  # ВЕРНУЛИ КОРРЕКТНЫЙ МИНИМУМ СУММЫ (0.001 USDC)
            "asset": str(USDC_ASSET),
            "payTo": str(0x801108CA1B7Caf261D2e4a11E7701aF7cD377e8a),
            "maxTimeoutSeconds": 300
        }],
        "extensions": {
            "bazaar": {
                "info": {
                    "name": "Base Ultra-Fresh Tokens Filter",
                    "description": "Returns top filtered tokens on Base with liquidity > $5000, sorted by 24h volume.",
                    "category": "onchain-data",
                    "tags": ["base", "tokens", "memes", "volume-filter", "safe-liquidity"],
                    "input": {
                        "type": "http",
                        "method": "GET",
                        "queryParams": {}
                    },
                    "output": {
                        "type": "object",
                        "properties": {
                            "agent": {"type": "string"},
                            "wallet": {"type": "string"},
                            "tokens": {"type": "array"},
                            "count": {"type": "number"}
                        },
                        "example": {
                            "agent": "Base Token Parser",
                            "wallet": str(WALLET_ADDRESS), # ТУТ ТОЖЕ СДЕЛАЛИ ЖЕСТКУЮ СТРОКУ
                            "tokens": tokens_list[:1] if tokens_list else [],
                            "count": len(tokens_list)
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
        headers={
            "PAYMENT-REQUIRED": encoded,
            "Content-Type": "application/json"
        },
        content=None
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
