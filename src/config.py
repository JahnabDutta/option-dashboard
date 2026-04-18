"""App configuration: curated Upstox underlyings and chart presets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Literal

# Display name -> Upstox instrument_key for the underlying (index or equity).
# Equity keys use NSE_EQ|<ISIN> per Upstox instrument master.
UNDERLYINGS: dict[str, str] = {
    "Nifty 50": "NSE_INDEX|Nifty 50",
    "Nifty Bank": "NSE_INDEX|Nifty Bank",
    "Reliance": "NSE_EQ|INE002A01018",
    "TCS": "NSE_EQ|INE467B01029",
    "INFY": "NSE_EQ|INE009A01021",
}

Unit = Literal["minutes", "hours", "days", "weeks", "months"]


@dataclass(frozen=True)
class TimescalePreset:
    """Maps UI label to Historical Candle V3 parameters."""

    label: str
    unit: Unit
    interval: str
    span: timedelta
    description: str


# Presets tuned to Upstox V3 limits (e.g. minute data capped ~1 month for small intervals).
TIMESCALE_PRESETS: list[TimescalePreset] = [
    TimescalePreset(
        label="1D (15m)",
        unit="minutes",
        interval="15",
        span=timedelta(days=1),
        description="Intraday — 15-minute candles (same calendar day window)",
    ),
    TimescalePreset(
        label="5D (1h)",
        unit="hours",
        interval="1",
        span=timedelta(days=5),
        description="Last ~5 days — hourly candles",
    ),
    TimescalePreset(
        label="1M (D)",
        unit="days",
        interval="1",
        span=timedelta(days=31),
        description="About 1 month — daily candles",
    ),
    TimescalePreset(
        label="3M (D)",
        unit="days",
        interval="1",
        span=timedelta(days=93),
        description="About 3 months — daily candles",
    ),
    TimescalePreset(
        label="6M (D)",
        unit="days",
        interval="1",
        span=timedelta(days=186),
        description="About 6 months — daily candles",
    ),
    TimescalePreset(
        label="1Y (D)",
        unit="days",
        interval="1",
        span=timedelta(days=365),
        description="About 1 year — daily candles",
    ),
]

DEFAULT_STRIKE_WINDOW = 8

CACHE_TTL_CHAIN_SEC = 90
CACHE_TTL_HISTORY_SEC = 120
