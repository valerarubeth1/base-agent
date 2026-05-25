from typing import Any
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.http import HTTPFacilitatorClient, FacilitatorConfig, PaymentOption
from x402.http.types import RouteConfig
from x402.server import x402ResourceServer
from x402.mechanisms.evm.exact import ExactEvmServerScheme
from x402.extensions.bazaar import declare_discovery_extension, OutputConfig
import requests
import os

app = FastAPI()

PAY_TO = "0x801108CA1B7Caf261D2e4a11E7701aF7cD377e8a"
RESOURCE_URL = "https://base-agent-production.up.railway.app/tokens"
FACILITATOR_URL = "https://facilitator.xpay.sh"

server = x402ResourceServer(HTTPFacilitatorClient(FacilitatorConfig(url=FACILITATOR_URL)))
server.register("eip155:8453", ExactEvmServerScheme())

routes = {
    "GET /tokens": RouteConfig(
        accepts=[
            PaymentOption(
                scheme="exact",
                price="$0.001",
                network="eip155:8453",
                pay_to=PAY_TO,
                resource_url=RESOURCE_URL,
            )
        ],
        mime_type="application/json",
        description="Top Base tokens by 24h volume with liquidity > $5000",
        extensions=declare_discovery_extension(
            output=OutputConfig(
                example={
                    "agent": "Base Token Parser",
                    "count": 10,
                    "tokens": [{"symbol": "TOKEN", "price_usd": "0.001", "volume_24h": 100000}],
                    "wallet": PAY_TO
                },
                schema={
                    "type": "object",
                    "properties": {
                        "agent": {"type": "string"},
                        "count": {"type": "number"},
                        "tokens": {"type": "array"},
                        "wallet": {"type": "string"}
                    }
                }
            )
        )
    )
}

app.add_middleware(PaymentMiddlewareASGI, routes=routes, server=server)

def fetch_hot_tokens():
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
                    tokens_list = []
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
                    return sorted(tokens_list, key=lambda x: x['volume_24h'], reverse=True)[:10]
    except Exception as e:
        print(f"DexScreener error: {e}")
    return []

@app.get("/", response_class=HTMLResponse)
def home():
    return """<!DOCTYPE html>
<html><head>
<meta name="base:app_id" content="6a0c3af81c1db8c69c491b11" />
</head><body>Base Token Parser — x402 agent on Base</body></html>"""

@app.get("/tokens")
async def handler() -> dict[str, Any]:
    tokens = fetch_hot_tokens()
    return {"agent": "Base Token Parser", "count": len(tokens), "tokens": tokens, "wallet": PAY_TO}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
