from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Agent is alive", "wallet": "0x801108CA1B7Caf261D2e4a11E7701aF7cD377e8a"}

@app.get("/tokens")
def get_tokens():
    url = "https://api.dexscreener.com/token-profiles/latest/v1"
    response = requests.get(url)
    data = response.json()

    base_tokens = []
    for t in data:
        if not isinstance(t, dict):
            continue
        if t.get("chainId") != "base":
            continue
        base_tokens.append({
            "symbol": t.get("header", t.get("description", "unknown"))[:20],
            "address": t.get("tokenAddress", ""),
            "links": [l.get("url","") for l in t.get("links", [])[:2]],
            "url": t.get("url", "")
        })
        if len(base_tokens) >= 10:
            break

    return {
        "agent": "Base Token Parser",
        "wallet": "0x801108CA1B7Caf261D2e4a11E7701aF7cD377e8a",
        "tokens": base_tokens,
        "count": len(base_tokens)
    }
