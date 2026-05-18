from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import os

app = FastAPI()

WALLET_ADDRESS = "0x801108CA1B7Caf261D2e4a11E7701aF7cD377e8a"
PRICE_USDC = 0.01  # цена за запрос

@app.get("/")
def home():
    return {
        "agent": "Base Token Parser",
        "wallet": WALLET_ADDRESS,
        "price_per_request": f"{PRICE_USDC} USDC",
        "endpoint": "/tokens",
        "instructions": f"Send {PRICE_USDC} USDC on Base to {WALLET_ADDRESS}, then call /tokens?tx=YOUR_TX_HASH"
    }

@app.get("/tokens")
def get_tokens(tx: str = None):
    # Проверяем что транзакция передана
    if not tx:
        return JSONResponse(
            status_code=402,
            content={
                "error": "Payment Required",
                "price": f"{PRICE_USDC} USDC",
                "send_to": WALLET_ADDRESS,
                "network": "Base",
                "then_call": f"/tokens?tx=YOUR_TX_HASH"
            }
        )

    # Проверяем транзакцию через BaseScan
    api_url = f"https://api.basescan.org/api?module=transaction&action=gettxreceiptstatus&txhash={tx}&apikey=YourApiKeyToken"
    try:
        check = requests.get(api_url, timeout=5)
        result = check.json()
        if result.get("status") != "1":
            return JSONResponse(status_code=402, content={"error": "Transaction not found or failed"})
    except:
        pass  # если BaseScan не ответил — пропускаем проверку

    # Отдаём данные
    response = requests.get(
        "https://api.dexscreener.com/latest/dex/search?q=base",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    data = response.json()
    pairs = data.get("pairs", [])
    base_tokens = []

    for p in pairs:
        if p.get("chainId") != "base":
            continue
        base_tokens.append({
            "symbol": p.get("baseToken", {}).get("symbol", "???"),
            "name": p.get("baseToken", {}).get("name", "???"),
            "address": p.get("baseToken", {}).get("address", ""),
            "price_usd": p.get("priceUsd", "0"),
            "volume_24h": p.get("volume", {}).get("h24", 0),
            "liquidity_usd": p.get("liquidity", {}).get("usd", 0),
            "url": f"https://dexscreener.com/base/{p.get('pairAddress','')}"
        })
        if len(base_tokens) >= 10:
            break

    return {
        "agent": "Base Token Parser",
        "wallet": WALLET_ADDRESS,
        "paid_with_tx": tx,
        "tokens": base_tokens,
        "count": len(base_tokens)
    }
