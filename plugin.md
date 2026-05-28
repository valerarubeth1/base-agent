# Base Token Parser Plugin

> [!IMPORTANT]
> ## STOP — COMPLETE ONBOARDING BEFORE USING THIS PLUGIN
>
> Before calling any Base Token Parser endpoint, you MUST complete the Base MCP onboarding flow:
> 1. Call `get_wallets` (Detection)
> 2. Present wallet status and disclaimer (Onboarding)

Base Token Parser returns the top 10 trending tokens on Base network by 24h volume with liquidity > $5000. Data is sourced from DexScreener in real time.

**Supported chain:** Base mainnet (8453).

---

## Read endpoint

GET https://base-agent-production.up.railway.app/tokens

Returns top 10 Base tokens sorted by 24h volume. No parameters needed.

Response shape:

{
  "agent": "Base Token Parser",
  "count": 10,
  "tokens": [
    {
      "symbol": "TOKEN",
      "address": "0x...",
      "price_usd": "0.001",
      "volume_24h": 500000,
      "liquidity_usd": 50000,
      "url": "https://dexscreener.com/base/..."
    }
  ],
  "wallet": "0x801108CA1B7Caf261D2e4a11E7701aF7cD377e8a"
}

## Orchestration pattern

1. get_wallets -> address
2. GET https://base-agent-production.up.railway.app/tokens -> top tokens list
3. Present tokens to user with price, volume and DexScreener links

## Note on payment

This endpoint requires 0.001 USDC payment via x402 protocol on Base.
