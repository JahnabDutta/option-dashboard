# The Kinetic Ledger — Indian options dashboard

Minimal **Streamlit** UI over the official **Upstox** API: NSE option chain (Greeks, IV, OI, bid/ask, PCR) and **Historical Candle v3** charts for a selected call or put across several timescales.

Visual direction follows [DESIGN.md](DESIGN.md) (Tactical Obsidian).

## Prerequisites

- Python 3.10+
- An [Upstox](https://upstox.com/) account and a **developer app** with `client_id`, `client_secret`, and a registered **redirect URI** ([developer docs](https://upstox.com/developer/api-documentation/))

## Setup

```bash
cd "option dashboard"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Access token

Upstox uses **OAuth2**. For a local dashboard, the usual pattern is:

1. Complete the browser login flow and obtain a **short-lived authorization `code`** (see [Authentication](https://upstox.com/developer/api-documentation/authentication)).
2. Exchange the code for an `access_token` (POST `https://api.upstox.com/v2/login/authorization/token`).

This repo includes a small helper:

```bash
set UPSTOX_CLIENT_ID=...
set UPSTOX_CLIENT_SECRET=...
set UPSTOX_REDIRECT_URI=...
python scripts/upstox_exchange_token.py --code PASTE_CODE_FROM_REDIRECT
```

Copy the printed token into `.streamlit/secrets.toml`:

```toml
upstox_access_token = "your_token_here"
```

Use `.streamlit/secrets.toml.example` as a reference. **Never commit** `secrets.toml` (it is gitignored).

When the token expires, repeat the OAuth steps or implement refresh using Upstox’s refresh-token flow outside Streamlit.

## Run

```bash
streamlit run app.py
```

## Data notes

- **Put/call option chain** and **option contracts** require a valid **Bearer** token ([Option contracts](https://upstox.com/developer/api-documentation/get-option-contracts), [Put/Call chain](https://upstox.com/developer/api-documentation/get-pc-option-chain)).
- **Historical candles** use [Historical Candle Data v3](https://upstox.com/developer/api-documentation/v3/get-historical-candle-data) with the option’s `instrument_key` from the chain response.
- Upstox documents that the **put/call chain is not available for MCX**; this app targets **NSE** underlyings only.
- Underlying `instrument_key` values are curated in `src/config.py` (`NSE_INDEX|…`, `NSE_EQ|<ISIN>`). Add rows from the official [instruments](https://upstox.com/developer/api-documentation/instruments) dump if you need more names.

## Sandbox

Upstox supports a **sandbox** environment for testing ([sandbox guide](https://upstox.com/developer/api-documentation/build-using-sandbox/)). Point the API base URL and tokens at sandbox if you are not using production keys.

## Project layout

| File | Purpose |
|------|---------|
| `app.py` | Streamlit entry, layout, CSS, caching |
| `src/config.py` | Underlyings and timescale presets |
| `src/upstox_api.py` | REST client for contracts, chain, history |
| `src/charts.py` | Plotly styling |
| `scripts/upstox_exchange_token.py` | Optional OAuth code → access token |
