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
    
    base_tokens = [
        {
            "symbol": t.get("symbol", "???"),
            "address": t.get("tokenAddress", ""),
            "url": t.get("url", "")
        }
        for t in data
        if isinstance(t, dict) and t.get("chainId") == "base"
    ][:10]
    
    return {
        "agent": "Base Token Parser",
        "wallet": "0x801108CA1B7Caf261D2e4a11E7701aF7cD377e8a",
        "tokens": base_tokens,
        "count": len(base_tokens)
    }
