"""
The Kinetic Ledger — minimal Indian options dashboard (Upstox + Streamlit).
"""

from __future__ import annotations

import streamlit as st
import json

from src.charts import price_oi_figure
from src.config import (
    CACHE_TTL_CHAIN_SEC,
    CACHE_TTL_HISTORY_SEC,
    DEFAULT_STRIKE_WINDOW,
    TIMESCALE_PRESETS,
    UNDERLYINGS,
)
from src.upstox_api import (
    UpstoxAPIError,
    default_history_range,
    get_historical_candles_v3,
    get_put_call_option_chain,
    list_expiries,
)


def inject_global_css() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Manrope:wght@500;600;700&display=swap');

html, body, [class*="css"]  {
  font-family: 'Inter', system-ui, sans-serif;
  color: #e5e2e1;
}
h1, h2, h3, .kl-headline {
  font-family: 'Manrope', 'Inter', sans-serif !important;
  letter-spacing: -0.02em;
  color: #e5e2e1 !important;
}
.stApp {
  background-color: #131313;
}
section[data-testid="stSidebar"] {
  background-color: #1c1b1b;
}
.block-container {
  padding-top: 1.25rem;
  padding-bottom: 2rem;
  max-width: 1200px;
}
.kl-surface-low {
  background: #1c1b1b;
  border-radius: 0.5rem;
  padding: 1rem 1.1rem;
  margin-bottom: 0.75rem;
}
.kl-surface-high {
  background: #2a2a2a;
  border-radius: 0.375rem;
  padding: 0.75rem 1rem;
}
.kl-label {
  font-size: 0.6875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: rgba(229, 226, 225, 0.55);
  margin-bottom: 0.15rem;
}
.kl-chip-bull {
  display: inline-block;
  padding: 0.2rem 0.55rem;
  border-radius: 0.375rem;
  background: rgba(64, 229, 108, 0.1);
  color: #40e56c;
  font-size: 0.8rem;
  font-weight: 600;
}
.kl-chip-tag {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 0.375rem;
  background: rgba(41, 98, 255, 0.15);
  color: #b6c4ff;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.kl-btn-primary button {
  background: linear-gradient(135deg, #b6c4ff 0%, #2962ff 100%) !important;
  color: #0e0e0e !important;
  border: none !important;
  border-radius: 0.375rem !important;
  font-weight: 600 !important;
}
div[data-testid="stMetricValue"] {
  color: #e5e2e1;
}
div[data-testid="stMetricLabel"] {
  font-size: 0.6875rem !important;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.stTabs [data-baseweb="tab-list"] {
  gap: 6px;
  background-color: #1c1b1b;
  padding: 6px;
  border-radius: 0.5rem;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 0.375rem !important;
  color: #e5e2e1;
}
.stTabs [aria-selected="true"] {
  background-color: #2a2a2a !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=CACHE_TTL_CHAIN_SEC, show_spinner=False)
def cached_expiries(access_token: str, instrument_key: str) -> list[str]:
    return list_expiries(access_token, instrument_key)


@st.cache_data(ttl=CACHE_TTL_CHAIN_SEC, show_spinner=False)
def cached_chain(access_token: str, instrument_key: str, expiry: str):
    return get_put_call_option_chain(access_token, instrument_key, expiry)


@st.cache_data(ttl=CACHE_TTL_HISTORY_SEC, show_spinner=False)
def cached_history(
    access_token: str,
    option_key: str,
    unit: str,
    interval: str,
    to_iso: str,
    from_iso: str,
):
    from datetime import date

    return get_historical_candles_v3(
        access_token,
        option_key,
        unit,
        interval,
        date.fromisoformat(to_iso),
        date.fromisoformat(from_iso),
    )


def filter_strikes_around_atm(df, window: int):
    if df.empty or "strike" not in df.columns:
        return df
    strikes = df["strike"].dropna().astype(float).sort_values().unique()
    if len(strikes) == 0:
        return df
    if df["spot"].notna().any():
        spot = float(df["spot"].dropna().iloc[0])
    else:
        spot = float(strikes[len(strikes) // 2])
    atm_idx = int((abs(strikes - spot)).argmin())
    start = max(0, atm_idx - window)
    end = min(len(strikes), atm_idx + window + 1)
    allowed = set(strikes[start:end])
    return df[df["strike"].isin(allowed)].reset_index(drop=True)


def main() -> None:
    st.set_page_config(
        page_title="The Kinetic Ledger",
        page_icon="◆",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_global_css()

    token = ""
    try:
        token = json.load(open('credentials.json','r',encoding='utf-8'))['upstox_access_token']
    except (KeyError, FileNotFoundError):
        token = ""
    except Exception:
        token = ""

    with st.sidebar:
        st.markdown("### Session")
        if not token:
            st.warning(
                "Add `upstox_access_token` to `.streamlit/secrets.toml`. "
                "See README for OAuth steps."
            )
        else:
            st.caption("Token loaded from secrets.")

    st.markdown(
        '<p class="kl-label" style="margin:0">The Kinetic Ledger</p>',
        unsafe_allow_html=True,
    )
    st.markdown("## Indian options · Upstox")

    if not token:
        st.error(
            "Missing Upstox access token. Create `.streamlit/secrets.toml` with:\n\n"
            "`upstox_access_token = \"...\"`"
        )
        st.stop()

    underlying_label = st.selectbox("Underlying", list(UNDERLYINGS.keys()))
    instrument_key = UNDERLYINGS[underlying_label]

    expiries = None
    try:
        expiries = cached_expiries(token, instrument_key)
    except UpstoxAPIError as e:
        if e.status_code == 401:
            st.error(str(e))
        else:
            st.error(str(e))
            if e.body is not None:
                st.json(e.body) if isinstance(e.body, dict) else st.code(str(e.body))
        st.stop()

    if not expiries:
        st.warning("No expiries returned for this underlying. Check the instrument key.")
        st.stop()
    if expiries is None:
        st.warning("No expiries returned for this underlying. Check the instrument key.")
        st.stop()

    expiry = st.selectbox("Expiry", expiries, index=min(len(expiries) - 1, 0))

    try:
        chain = cached_chain(token, instrument_key, expiry)
    except UpstoxAPIError as e:
        st.error(str(e))
        if e.body is not None and isinstance(e.body, dict):
            st.json(e.body)
        st.stop()

    if chain.empty:
        st.warning("Empty option chain for this expiry.")
        st.stop()

    spot = chain["spot"].dropna().iloc[0] if chain["spot"].notna().any() else None

    col_a, col_b, col_c = st.columns([2, 1, 1])
    with col_a:
        st.markdown(f"### {underlying_label}")
        if spot is not None:
            st.markdown(
                f'<span style="font-size:2rem;font-weight:600">{spot:,.2f}</span>',
                unsafe_allow_html=True,
            )
    with col_b:
        st.markdown('<p class="kl-label">Expiry</p>', unsafe_allow_html=True)
        st.markdown(f"**{expiry}**")
    with col_c:
        st.markdown('<p class="kl-label">Venue</p>', unsafe_allow_html=True)
        st.markdown("NSE (F&O)")

    strike_window = st.slider("Strikes around ATM (each side)", 3, 20, DEFAULT_STRIKE_WINDOW)
    view = filter_strikes_around_atm(chain, strike_window)

    tab_chain, tab_trends = st.tabs(["Option chain", "Trends"])

    with tab_chain:
        st.markdown('<div class="kl-surface-low">', unsafe_allow_html=True)
        display_cols = [
            "strike",
            "ce_bid",
            "ce_ask",
            "ce_delta",
            "ce_theta",
            "ce_iv",
            "ce_oi",
            "pe_bid",
            "pe_ask",
            "pe_delta",
            "pe_theta",
            "pe_iv",
            "pe_oi",
        ]
        cols = [c for c in display_cols if c in view.columns]
        st.dataframe(
            view[cols],
            width="stretch",
            hide_index=True,
            column_config={
                "strike": st.column_config.NumberColumn("Strike", format="%.2f"),
                "ce_bid": st.column_config.NumberColumn("C Bid", format="%.2f"),
                "ce_ask": st.column_config.NumberColumn("C Ask", format="%.2f"),
                "ce_delta": st.column_config.NumberColumn("C Δ", format="%.4f"),
                "ce_theta": st.column_config.NumberColumn("C Θ", format="%.4f"),
                "ce_iv": st.column_config.NumberColumn("C IV", format="%.2f"),
                "ce_oi": st.column_config.NumberColumn("C OI", format="%d"),
                "pe_bid": st.column_config.NumberColumn("P Bid", format="%.2f"),
                "pe_ask": st.column_config.NumberColumn("P Ask", format="%.2f"),
                "pe_delta": st.column_config.NumberColumn("P Δ", format="%.4f"),
                "pe_theta": st.column_config.NumberColumn("P Θ", format="%.4f"),
                "pe_iv": st.column_config.NumberColumn("P IV", format="%.2f"),
                "pe_oi": st.column_config.NumberColumn("P OI", format="%d"),
            },
        )
        st.markdown("</div>", unsafe_allow_html=True)

        strikes_list = view["strike"].dropna().tolist()
        strike_sel = st.selectbox("Strike (detail card)", strikes_list)
        side = st.radio("Side", ["Call (CE)", "Put (PE)"], horizontal=True)

        row = view.loc[view["strike"] == strike_sel].iloc[0]
        iv = row["ce_iv"] if side.startswith("Call") else row["pe_iv"]
        oi = row["ce_oi"] if side.startswith("Call") else row["pe_oi"]
        vol = row["ce_vol"] if side.startswith("Call") else row["pe_vol"]
        ltp = row["ce_ltp"] if side.startswith("Call") else row["pe_ltp"]
        pcr = row.get("pcr")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("IV", f"{iv:.2f}" if iv == iv else "—")
        with c2:
            st.metric("Open interest", f"{int(oi):,}" if oi == oi else "—")
        with c3:
            st.metric("Volume", f"{int(vol):,}" if vol == vol else "—")
        with c4:
            st.metric("PCR (row)", f"{pcr:.4f}" if pcr == pcr else "—")

        st.markdown(
            f"""
<div class="kl-surface-low">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <div>
      <p class="kl-label">Quick view</p>
      <strong>{underlying_label} {expiry} {strike_sel} {'Call' if side.startswith('Call') else 'Put'}</strong>
    </div>
    <span class="kl-chip-bull">{'BULLISH' if side.startswith('Call') else 'BEARISH'}</span>
  </div>
  <p style="margin-top:0.75rem;font-size:1.4rem;font-weight:600;">LTP: {ltp if ltp == ltp else '—'}</p>
</div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<span class="kl-chip-tag">Insight</span>', unsafe_allow_html=True)
        st.caption(
            "Implied volatility and Greeks come from Upstox option chain snapshot. "
            "Historical IV percentile requires a stored time series (not in this MVP)."
        )

    with tab_trends:
        st.markdown('<div class="kl-surface-low">', unsafe_allow_html=True)
        trend_strikes = view["strike"].dropna().tolist()
        t_strike = st.selectbox("Strike (chart)", trend_strikes, key="trend_strike")
        t_side = st.radio("Contract", ["Call (CE)", "Put (PE)"], horizontal=True, key="trend_side")
        preset = st.selectbox(
            "Timescale",
            TIMESCALE_PRESETS,
            format_func=lambda p: p.label,
        )
        st.caption(preset.description)
        st.markdown("</div>", unsafe_allow_html=True)

        row_t = view.loc[view["strike"] == t_strike].iloc[0]
        opt_key = row_t["ce_key"] if t_side.startswith("Call") else row_t["pe_key"]
        if not opt_key or not isinstance(opt_key, str):
            st.error("Missing instrument key for this contract.")
        else:
            from_d, to_d = default_history_range(preset.span)
            try:
                hist = cached_history(
                    token,
                    opt_key,
                    preset.unit,
                    preset.interval,
                    to_d.isoformat(),
                    from_d.isoformat(),
                )
            except UpstoxAPIError as e:
                st.error(str(e))
                if e.body is not None and isinstance(e.body, dict):
                    st.json(e.body)
                hist = None

            if hist is not None:
                title = f"{underlying_label} · {t_strike} · {'CE' if t_side.startswith('Call') else 'PE'} · {preset.label}"
                fig = price_oi_figure(hist, title)
                st.plotly_chart(fig, width="stretch")


if __name__ == "__main__":
    main()
