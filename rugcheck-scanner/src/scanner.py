import os
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

RUGCHECK_API_KEY = os.getenv("RUGCHECK_API_KEY", "YOUR_RUGCHECK_API_KEY_HERE")
MIN_5M_VOLUME_USD = float(os.getenv("MIN_5M_VOLUME_USD", "200000"))
POLL_INTERVAL_SEC = int(os.getenv("POLL_INTERVAL_SEC", "35"))

AI_KEYWORDS = {
    "ai",
    "agent",
    "grok",
    "llm",
    "autonomous",
    "virtuals",
    "aix",
    "sentient",
    "cognition",
    "neural",
    "swarm",
    "dasha",
    "eliza",
    "terminal",
    "multiagent",
    "intelligent",
    "bot",
    "agency",
    "robo",
    "smart",
}


def check_rugcheck(ca: str) -> tuple[bool, str, float]:
    try:
        url = f"https://api.rugcheck.xyz/v1/tokens/{ca}/report"
        headers: dict[str, str] = {}
        if RUGCHECK_API_KEY != "YOUR_RUGCHECK_API_KEY_HERE":
            headers["X-API-KEY"] = RUGCHECK_API_KEY

        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return False, f"RugCheck HTTP {resp.status_code}", 0.0

        data = resp.json()
        score = data.get("score", 9999)
        risks = [r.get("name", "") for r in data.get("risks", [])]

        top_holders = data.get("topHolders", [])
        non_lp = [h for h in top_holders if not h.get("isLp", False)]
        max_holder_pct = max((h.get("pct", 0) for h in non_lp), default=0.0) * 100

        passed = (
            score < 500
            and max_holder_pct <= 20.0
            and "Freeze Authority" not in risks
            and "Mint Authority" not in risks
        )

        summary = (
            f"Score={score} | Top non-LP={max_holder_pct:.1f}% | "
            f"Risks={', '.join(risks) or 'None'} | {'✅ PASS' if passed else '❌ FAIL'}"
        )
        return passed, summary, max_holder_pct
    except Exception as exc:
        return False, f"Error: {str(exc)[:80]}", 0.0


def fetch_high_volume_tokens(min_vol: float = 200_000) -> list[dict]:
    try:
        url = "https://api.dexscreener.com/latest/dex/search?q=SOL"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        pairs = resp.json().get("pairs", [])
    except Exception as exc:
        print(f"[ERROR] DexScreener: {exc}")
        return []

    tokens: list[dict] = []
    seen = set()

    for pair in pairs:
        if pair.get("chainId") != "solana":
            continue

        ca = pair.get("baseToken", {}).get("address", "")
        if not ca or ca in seen:
            continue
        seen.add(ca)

        vol_5m = float(pair.get("volume", {}).get("m5", 0) or 0)
        if vol_5m < min_vol:
            continue

        base = pair.get("baseToken", {})
        info = pair.get("info", {})
        socials = info.get("socials", [])
        websites = info.get("websites", [])

        x_handle = next((s.get("url") for s in socials if s.get("type") == "twitter"), None)
        website = websites[0].get("url") if websites else None

        tokens.append(
            {
                "ca": ca,
                "name": base.get("name", ""),
                "ticker": base.get("symbol", ""),
                "volume_5m_usd": vol_5m,
                "liquidity_usd": float(pair.get("liquidity", {}).get("usd", 0) or 0),
                "fdv": float(pair.get("fdv", 0) or 0),
                "dex_url": pair.get("url", f"https://dexscreener.com/solana/{ca}"),
                "x_handle": x_handle,
                "website": website,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            }
        )

    return tokens


def main() -> None:
    print("🚀 Solana AI Agent Tracker")
    print(f"   5m Vol > ${MIN_5M_VOLUME_USD:,.0f} + RugCheck + AI keyword filter")
    print("=" * 100)

    seen_cas = set()

    while True:
        tokens = fetch_high_volume_tokens(MIN_5M_VOLUME_USD)

        for token in tokens:
            ca = token["ca"]
            if ca in seen_cas:
                continue
            seen_cas.add(ca)

            combined = (token["name"] + token["ticker"]).lower()
            if not any(kw in combined for kw in AI_KEYWORDS):
                continue

            passed, summary, _ = check_rugcheck(ca)

            print("\n" + "─" * 80)
            print(f"{token['timestamp']} | ${token['ticker']} | {token['name']}")
            print(f"CA:     {ca}")
            print(f"X:      {token['x_handle'] or 'N/A'}")
            print(f"Web:    {token['website'] or 'N/A'}")
            print(
                f"5m Vol: ${token['volume_5m_usd']:,.0f}  "
                f"Liq: ${token['liquidity_usd']:,.0f}  FDV: ${token['fdv']:,.0f}"
            )
            print(f"DexS:   {token['dex_url']}")
            print(f"Rug:    {summary}")
            print("─" * 80)

            if passed:
                print(f"QUICK BUY: https://jup.ag/swap?outputMint={ca}")
                print("Paste CA to Grok for deeper check.\n")

        if len(seen_cas) > 800:
            seen_cas = set(list(seen_cas)[-600:])

        time.sleep(POLL_INTERVAL_SEC)


if __name__ == "__main__":
    if RUGCHECK_API_KEY == "YOUR_RUGCHECK_API_KEY_HERE":
        print("⚠️ Add real RugCheck API key or checks may be limited/failed.")
    main()
