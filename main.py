from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Agent is alive", "wallet": "0x801108CA1B7Caf261D2e4a11E7701aF7cD377e8a"}

@app.get("/tokens")
def get_tokens():
    url = "https://api.dexscreener.com/latest/dex/tokens/base"
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
        "wallet": "0x801108CA1B7Caf261D2e4a11E7701aF7cD377e8a",
        "tokens": base_tokens,
        "count": len(base_tokens)
    }
