from typing import Any
from fastapi import FastAPI
import requests

from x402.http import FacilitatorConfig, HTTPFacilitatorClient, PaymentOption
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.http.types import RouteConfig
from x402.mechanisms.evm.exact import ExactEvmServerScheme
from x402.server import x402ResourceServer

app = FastAPI()

# Базовые константы
PAY_TO = "0x801108CA1B7Caf261D2e4a11E7701aF7cD377e8a"
USDC_ASSET = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

# Функция для динамического сбора токенов с DexScreener
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
    
    # Дефолтный фолбек, если DexScreener лежит, чтобы не отдавать пустоту
    return [{
        "address": "0x099880c1676FF3035Ab1E952E5E83b5A81eecB07",
        "liquidity_usd": 77934.83,
        "price_usd": "0.0000009813",
        "symbol": "GNULL",
        "url": "https://dexscreener.com/base/0x3676a19715f72f7a7730cc44b26fc515464642f8634dc7f9e6df2f3d7a2d7b79",
        "volume_24h": 399443.06
    }]

# Подключаем официальный фасилитатор от Coinbase
facilitator = HTTPFacilitatorClient(
    FacilitatorConfig(url="https://api.cdp.coinbase.com/platform/v2/x402/facilitator")
)

server = x402ResourceServer(facilitator)
server.register("eip155:8453", ExactEvmServerScheme())

# Генерируем пример для блока инициализации метаданных Bazaar
default_tokens = fetch_hot_tokens()

# Конфигурация защищенных роутов с метаданными Bazaar Discovery
routes: dict[str, RouteConfig] = {
    "GET /tokens": RouteConfig(
        accepts=[
            PaymentOption(
                scheme="exact",
                pay_to=PAY_TO,
                amount="1000",             # Обязательно передаем строкой в атомных единицах ($0.001)
                asset=USDC_ASSET,          # Контракт USDC
                network="eip155:8453",     # Сеть Base
                max_timeout_seconds=300,   # ВОТ ОНО! Явно прокидываем таймаут в SDK, чтобы он попал в заголовок!
            ),
        ],
        mime_type="application/json",
        description="Returns top filtered tokens on Base with liquidity > $5000, sorted by 24h volume.",
        extensions={
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
        },
    ),
}

# Накатываем middleware, которое будет автоматически перехватывать запросы и слать 402, если нет оплаты
app.add_middleware(PaymentMiddlewareASGI, routes=routes, server=server)


@app.get("/tokens")
async def handler() -> dict[str, Any]:
    # Сюда клиент попадет ТОЛЬКО после успешной оплаты через x402 мидлварь
    hot_tokens = fetch_hot_tokens()
    return {
        "agent": "Base Token Parser",
        "count": len(hot_tokens),
        "tokens": hot_tokens,
        "wallet": PAY_TO
    }


if __name__ == "__main__":
    import uvicorn
    # Меняем порт на 8000 (или какой там у тебя прописан в настройках Railway Start Command)
    uvicorn.run(app, host="0.0.0.0", port=8000)
