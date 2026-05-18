from fastapi import FastAPI, Response
import requests
import json
import base64
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# Все адреса жестко строками
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
                                "address": pair.get('baseToken', {}).get('address', ''),
                                "liquidity_usd": float(liquidity),
                                "price_usd": pair.get('priceUsd', '0'),
                                "symbol": pair.get('baseToken', {}).get('symbol', 'UNKNOWN'),
                                "url": pair.get('url', ''),
                                "volume_24h": float(pair.get('volume', {}).get('h24', 0))
                            })
                    tokens_list = sorted(tokens_list, key=lambda x: x['volume_24h'], reverse=True)[:10]
    except Exception as e:
        print(f"Ошибка парсинга DexScreener: {e}")

    # ЭТАЛОННЫЙ JSON СТРОГО ПО КРИТЕРИЯМ ИЗ ТВОЕЙ ДОКУМЕНТАЦИИ BAZAAR
    payment_required = {
        "x402Version": 2,
        "error": "Payment required",
        "resource": {
            "url": str(RESOURCE_URL),
            "description": "Returns top filtered tokens on Base with liquidity > $5000, sorted by 24h volume.",
            "mimeType": "application/json"
        },
        "accepts": [
            {
                "scheme": "exact",
                "network": "eip155:8453",
                "amount": "1000",
                "asset": str(USDC_ASSET),
                "payTo": str(WALLET_ADDRESS),
                "maxTimeoutSeconds": 300,  # ВОТ ОН! На своем законном месте внутри accepts
                "maxAmountRequired": "1000",
                "resource": str(RESOURCE_URL),
                "description": "Access Base token feed",
                "mimeType": "application/json",
                "eip712": {
                    "domain": {
                        "chainId": 8453,
                        "name": "USD Coin",
                        "verifyingContract": str(USDC_ASSET),
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
                        "type": "json",  # Поменяли на "json", как требует новая спецификация
                        "example": {
                            "agent": "Base Token Parser",
                            "count": len(tokens_list),
                            "tokens": tokens_list if tokens_list else [
                                {
                                    "address": "0x099880c1676FF3035Ab1E952E5E83b5A81eecB07",
                                    "liquidity_usd": 77934.83,
                                    "price_usd": "0.0000009813",
                                    "symbol": "GNULL",
                                    "url": "https://dexscreener.com/base/... ",
                                    "volume_24h": 399443.06
                                }
                            ],
                            "wallet": str(WALLET_ADDRESS)
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

    # Кодируем в чистый стандартный Base64
    encoded = base64.b64encode(json.dumps(payment_required).encode('utf-8')).decode('utf-8')

    # Отдаем через каноничный Response c пустым телом
    return Response(
        status_code=402,
        headers={
            "PAYMENT-REQUIRED": encoded
        },
        content=""
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
