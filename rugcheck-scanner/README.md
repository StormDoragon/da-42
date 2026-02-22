# RugCheck Solana Scanner

A small Python scanner that:

1. Pulls Solana pairs from DexScreener.
2. Filters by 5m volume.
3. Filters for AI-related token names/tickers.
4. Calls RugCheck API and prints pass/fail details.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# set RUGCHECK_API_KEY in .env
python src/scanner.py
```

## Config

Set values in `.env`:

- `RUGCHECK_API_KEY`
- `MIN_5M_VOLUME_USD` (default `200000`)
- `POLL_INTERVAL_SEC` (default `35`)

## Add this folder to your existing git repo

From your repo root:

```bash
mkdir -p tools
cp -R rugcheck-scanner tools/rugcheck-scanner
git add tools/rugcheck-scanner
git commit -m "Add RugCheck Solana scanner tool"
```
