"""
core/binance_client.py
Pobiera dane z Binance Public API (bez klucza API dla danych rynkowych)
Dla danych portfela wymagany read-only API key
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st

BINANCE_BASE = "https://api.binance.com/api/v3"
BINANCE_FUTURES = "https://fapi.binance.com/fapi/v1"

INTERVALS = {
    "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m",
    "30m": "30m", "1h": "1h", "4h": "4h", "1d": "1d"
}

@st.cache_data(ttl=15)
def get_price(symbol: str) -> dict:
    """Aktualna cena i 24h stats"""
    try:
        r = requests.get(f"{BINANCE_BASE}/ticker/24hr", params={"symbol": symbol}, timeout=5)
        d = r.json()
        return {
            "price": float(d["lastPrice"]),
            "change_pct": float(d["priceChangePercent"]),
            "change_abs": float(d["priceChange"]),
            "high": float(d["highPrice"]),
            "low": float(d["lowPrice"]),
            "volume": float(d["volume"]),
            "quote_volume": float(d["quoteVolume"]),
            "trades": int(d["count"]),
        }
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=30)
def get_klines(symbol: str, interval: str = "5m", limit: int = 200) -> pd.DataFrame:
    """Pobiera świece OHLCV"""
    try:
        r = requests.get(f"{BINANCE_BASE}/klines", params={
            "symbol": symbol, "interval": interval, "limit": limit
        }, timeout=8)
        data = r.json()
        df = pd.DataFrame(data, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", "taker_buy_base",
            "taker_buy_quote", "ignore"
        ])
        for col in ["open", "high", "low", "close", "volume", "quote_volume"]:
            df[col] = df[col].astype(float)
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
        df = df.set_index("open_time")
        return df
    except Exception as e:
        st.error(f"Błąd pobierania danych: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_orderbook(symbol: str, limit: int = 20) -> dict:
    """Order book depth"""
    try:
        r = requests.get(f"{BINANCE_BASE}/depth", params={"symbol": symbol, "limit": limit}, timeout=5)
        d = r.json()
        bids = [(float(p), float(q)) for p, q in d["bids"]]
        asks = [(float(p), float(q)) for p, q in d["asks"]]
        return {"bids": bids, "asks": asks}
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=30)
def get_top_gainers(limit: int = 10) -> pd.DataFrame:
    """Top movers 24h"""
    try:
        r = requests.get(f"{BINANCE_BASE}/ticker/24hr", timeout=8)
        data = r.json()
        df = pd.DataFrame(data)
        df = df[df["symbol"].str.endswith("USDT")]
        df["priceChangePercent"] = df["priceChangePercent"].astype(float)
        df["lastPrice"] = df["lastPrice"].astype(float)
        df["quoteVolume"] = df["quoteVolume"].astype(float)
        df = df[df["quoteVolume"] > 1_000_000]  # min 1M USDT volume
        gainers = df.nlargest(limit, "priceChangePercent")[["symbol", "lastPrice", "priceChangePercent", "quoteVolume"]]
        losers = df.nsmallest(limit, "priceChangePercent")[["symbol", "lastPrice", "priceChangePercent", "quoteVolume"]]
        return gainers, losers
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=60)
def get_funding_rate(symbol: str) -> float:
    """Futures funding rate"""
    try:
        r = requests.get(f"{BINANCE_FUTURES}/fundingRate", params={"symbol": symbol, "limit": 1}, timeout=5)
        data = r.json()
        if data:
            return float(data[-1]["fundingRate"]) * 100
        return 0.0
    except Exception:
        return 0.0

@st.cache_data(ttl=30)
def get_open_interest(symbol: str) -> float:
    """Open Interest dla futures"""
    try:
        r = requests.get(f"{BINANCE_FUTURES}/openInterest", params={"symbol": symbol}, timeout=5)
        d = r.json()
        return float(d.get("openInterest", 0))
    except Exception:
        return 0.0

POPULAR_PAIRS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT",
    "LINKUSDT", "UNIUSDT", "LTCUSDT", "ATOMUSDT", "NEARUSDT",
    "APTUSDT", "ARBUSDT", "OPUSDT", "INJUSDT", "SUIUSDT"
]
