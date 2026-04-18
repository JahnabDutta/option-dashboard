"""Upstox REST v2/v3 client: option contracts, put/call chain, historical candles."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any
from urllib.parse import quote
from zoneinfo import ZoneInfo

import pandas as pd

IST = ZoneInfo("Asia/Kolkata")
import requests

BASE_URL = "https://api.upstox.com"


class UpstoxAPIError(Exception):
    """Raised when Upstox returns an error or unexpected payload."""

    def __init__(self, message: str, status_code: int | None = None, body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


def _headers(access_token: str) -> dict[str, str]:
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }


def _raise_for_status(resp: requests.Response) -> None:
    if resp.status_code == 401:
        raise UpstoxAPIError(
            "Unauthorized (401). Check `upstox_access_token` in `.streamlit/secrets.toml` "
            "or re-run the token helper script.",
            status_code=401,
            body=_safe_json(resp),
        )
    if resp.status_code >= 400:
        raise UpstoxAPIError(
            f"Upstox API error: HTTP {resp.status_code}",
            status_code=resp.status_code,
            body=_safe_json(resp),
        )


def _safe_json(resp: requests.Response) -> Any:
    try:
        return resp.json()
    except Exception:
        return resp.text


def get_option_contracts(access_token: str, instrument_key: str) -> list[dict[str, Any]]:
    """Fetch option contracts for an underlying; used to list expiries."""
    url = f"{BASE_URL}/v2/option/contract"
    resp = requests.get(
        url,
        params={"instrument_key": instrument_key},
        headers=_headers(access_token),
        timeout=30,
    )
    _raise_for_status(resp)
    payload = resp.json()
    if payload.get("status") != "success":
        raise UpstoxAPIError("Unexpected option contract response", body=payload)
    data = payload.get("data")
    if not isinstance(data, list):
        raise UpstoxAPIError("Invalid option contract payload: missing data array", body=payload)
    return data


def list_expiries(access_token: str, instrument_key: str) -> list[str]:
    """Unique expiry dates (YYYY-MM-DD), sorted ascending."""
    rows = get_option_contracts(access_token, instrument_key)
    expiries: set[str] = set()
    for row in rows:
        exp = row.get("expiry")
        if isinstance(exp, str) and exp:
            expiries.add(exp[:10])
    return sorted(expiries)


def get_put_call_option_chain(
    access_token: str, instrument_key: str, expiry_date: str
) -> pd.DataFrame:
    """
    GET /v2/option/chain — strike-wise calls/puts with market data and greeks.
    expiry_date: YYYY-MM-DD
    """
    url = f"{BASE_URL}/v2/option/chain"
    resp = requests.get(
        url,
        params={"instrument_key": instrument_key, "expiry_date": expiry_date},
        headers=_headers(access_token),
        timeout=45,
    )
    _raise_for_status(resp)
    payload = resp.json()
    if payload.get("status") != "success":
        raise UpstoxAPIError("Unexpected option chain response", body=payload)
    rows = payload.get("data")
    if not isinstance(rows, list) or not rows:
        return pd.DataFrame()

    records: list[dict[str, Any]] = []
    for row in rows:
        strike = row.get("strike_price")
        spot = row.get("underlying_spot_price")
        pcr = row.get("pcr")
        call = row.get("call_options") or {}
        put = row.get("put_options") or {}
        cm = call.get("market_data") or {}
        cg = call.get("option_greeks") or {}
        pm = put.get("market_data") or {}
        pg = put.get("option_greeks") or {}

        records.append(
            {
                "strike": strike,
                "spot": spot,
                "pcr": pcr,
                "ce_key": call.get("instrument_key"),
                "ce_ltp": cm.get("ltp"),
                "ce_bid": cm.get("bid_price"),
                "ce_ask": cm.get("ask_price"),
                "ce_oi": cm.get("oi"),
                "ce_vol": cm.get("volume"),
                "ce_delta": cg.get("delta"),
                "ce_gamma": cg.get("gamma"),
                "ce_theta": cg.get("theta"),
                "ce_vega": cg.get("vega"),
                "ce_iv": cg.get("iv"),
                "ce_pop": cg.get("pop"),
                "pe_key": put.get("instrument_key"),
                "pe_ltp": pm.get("ltp"),
                "pe_bid": pm.get("bid_price"),
                "pe_ask": pm.get("ask_price"),
                "pe_oi": pm.get("oi"),
                "pe_vol": pm.get("volume"),
                "pe_delta": pg.get("delta"),
                "pe_gamma": pg.get("gamma"),
                "pe_theta": pg.get("theta"),
                "pe_vega": pg.get("vega"),
                "pe_iv": pg.get("iv"),
                "pe_pop": pg.get("pop"),
            }
        )

    df = pd.DataFrame.from_records(records)
    if "strike" in df.columns:
        df = df.sort_values("strike", ascending=True).reset_index(drop=True)
    return df


def get_historical_candles_v3(
    access_token: str,
    instrument_key: str,
    unit: str,
    interval: str,
    to_date: date,
    from_date: date,
) -> pd.DataFrame:
    """
    GET /v3/historical-candle/{instrument_key}/{unit}/{interval}/{to_date}/{from_date}
    Candle tuple: timestamp, open, high, low, close, volume, oi
    """
    if from_date > to_date:
        from_date, to_date = to_date, from_date

    ik = quote(instrument_key, safe="")
    path = (
        f"/v3/historical-candle/{ik}/{unit}/{interval}/"
        f"{to_date.isoformat()}/{from_date.isoformat()}"
    )
    url = f"{BASE_URL}{path}"
    resp = requests.get(url, headers=_headers(access_token), timeout=45)
    _raise_for_status(resp)
    payload = resp.json()
    if payload.get("status") != "success":
        raise UpstoxAPIError("Unexpected historical candle response", body=payload)

    data = payload.get("data") or {}
    candles = data.get("candles")
    if not candles:
        return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume", "oi"])

    parsed: list[dict[str, Any]] = []
    for c in candles:
        if not isinstance(c, (list, tuple)) or len(c) < 6:
            continue
        ts = c[0]
        o, h, low, cl = c[1], c[2], c[3], c[4]
        vol = c[5] if len(c) > 5 else None
        oi = c[6] if len(c) > 6 else None
        parsed.append(
            {
                "time": pd.to_datetime(ts, utc=True).tz_convert("Asia/Kolkata"),
                "open": o,
                "high": h,
                "low": low,
                "close": cl,
                "volume": vol,
                "oi": oi,
            }
        )

    return pd.DataFrame(parsed)


def default_history_range(preset_span: timedelta) -> tuple[date, date]:
    """End = today (IST calendar), start = end - span (clamped)."""
    to_d = datetime.now(IST).date()
    from_d = to_d - preset_span
    return from_d, to_d
