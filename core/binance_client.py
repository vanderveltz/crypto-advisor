"""
core/binance_client.py
Dane rynkowe: CoinGecko (ceny/movers) + yfinance (świece OHLCV)
Binance używany tylko do order book (z fallbackiem)
"""

import requests
import pandas as pd
import numpy as np
import streamlit as st
import yfinance as yf

BINANCE_BASE = "https://api.binance.com/api/v3"
BINANCE_FUTURES = "https://fapi.binance.com/fapi/v1"
COINGECKO_BASE = "https://api.coingecko.com/api/v3"

POPULAR_PAIRS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT",
    "LINKUSDT", "UNIUSDT", "LTCUSDT", "ATOMUSDT", "NEARUSDT",
    "APTUSDT", "ARBUSDT", "OPUSDT", "INJUSDT", "SUIUSDT"
]

COINGECKO_IDS = {
    "BTCUSDT": "bitcoin", "ETHUSDT": "ethereum", "BNBUSDT": "binancecoin",
    "SOLUSDT": "solana", "XRPUSDT": "ripple", "ADAUSDT": "cardano",
    "DOGEUSDT": "dogecoin", "AVAXUSDT": "avalanche-2", "DOTUSDT": "polkadot",
    "MATICUSDT": "matic-network", "LINKUSDT": "chainlink", "UNIUSDT": "uniswap",
    "LTCUSDT": "litecoin", "ATOMUSDT": "cosmos", "NEARUSDT": "near",
    "APTUSDT": "aptos", "ARBUSDT": "arbitrum", "OPUSDT": "optimism",
    "INJUSDT": "injective-protocol", "SUIUSDT": "sui",
}

YAHOO_SYMBOLS = {
    "BTCUSDT": "BTC-USD", "ETHUSDT": "ETH-USD", "BNBUSDT": "BNB-USD",
    "SOLUSDT": "SOL-USD", "XRPUSDT": "XRP-USD", "ADAUSDT": "ADA-USD",
    "DOGEUSDT": "DOGE-USD", "AVAXUSDT": "AVAX-USD", "DOTUSDT": "DOT-USD",
    "MATICUSDT": "MATIC-USD", "LINKUSDT": "LINK-USD", "UNIUSDT": "UNI7874-USD",
    "LTCUSDT": "LTC-USD", "ATOMUSDT": "ATOM-USD", "NEARUSDT": "NEAR-USD",
    "APTUSDT": "APT-USD", "ARBUSDT": "ARB-USD", "OPUSDT": "OP-USD",
    "INJUSDT": "INJ-USD", "SUIUSDT": "SUI-USD",
}

# yfinance: (interval, period)
YF_CONFIG = {
    "1m":  ("1m",  "1d"),
    "3m":  ("5m",  "5d"),   # brak 3m w yfinance → 5m
    "5m":  ("5m",  "5d"),
    "15m": ("15m", "5d"),
    "30m": ("30m", "1mo"),
    "1h":  ("1h",  "1mo"),
    "4h":  ("1h",  "3mo"),  # 4h przez resample z 1h
    "1d":  ("1d",  "1y"),
}


@st.cache_data(ttl=20)
def get_price(symbol: str) -> dict:
    """Aktualna cena i 24h stats — CoinGecko."""
    try:
        cg_id = COINGECKO_IDS.get(symbol)
        if not cg_id:
            return {"error": f"Nieznana para: {symbol}"}

        r = requests.get(
            f"{COINGECKO_BASE}/coins/markets",
            params={
                "vs_currency": "usd",
                "ids": cg_id,
                "order": "market_cap_desc",
                "per_page": 1,
                "page": 1,
                "sparkline": "false",
                "price_change_percentage": "24h",
            },
            timeout=10
        )
        data = r.json()
        if not isinstance(data, list) or not data:
            return {"error": "Brak danych CoinGecko"}

        c = data[0]
        return {
            "price":        float(c.get("current_price") or 0),
            "change_pct":   float(c.get("price_change_percentage_24h") or 0),
            "change_abs":   float(c.get("price_change_24h") or 0),
            "high":         float(c.get("high_24h") or c.get("current_price") or 0),
            "low":          float(c.get("low_24h") or c.get("current_price") or 0),
            "volume":       float(c.get("total_volume") or 0),
            "quote_volume": float(c.get("total_volume") or 0),
            "trades":       0,
        }
    except Exception as e:
        return {"error": str(e)}


@st.cache_data(ttl=30)
def get_klines(symbol: str, interval: str = "5m", limit: int = 200) -> pd.DataFrame:
    """Pobiera świece OHLCV — yfinance."""
    try:
        yf_symbol = YAHOO_SYMBOLS.get(symbol)
        if not yf_symbol:
            return pd.DataFrame()

        yf_interval, period = YF_CONFIG.get(interval, ("5m", "5d"))

        ticker = yf.Ticker(yf_symbol)
        df = ticker.history(period=period, interval=yf_interval, auto_adjust=True)

        if df.empty:
            return pd.DataFrame()

        df = df.rename(columns={
            "Open": "open", "High": "high", "Low": "low",
            "Close": "close", "Volume": "volume"
        })
        df = df[["open", "high", "low", "close", "volume"]].copy()

        # Resample 1h → 4h jeśli potrzeba
        if interval == "4h":
            df = df.resample("4h").agg({
                "open": "first", "high": "max",
                "low": "min", "close": "last", "volume": "sum"
            }).dropna()

        df.index = pd.to_datetime(df.index)
        df.index.name = "open_time"
        # Usuń timezone info żeby uniknąć problemów
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        df["close_time"] = df.index
        df["quote_volume"] = df["volume"]
        df["trades"] = 0
        df["taker_buy_base"] = 0
        df["taker_buy_quote"] = 0
        df["ignore"] = 0

        return df.tail(limit)
    except Exception as e:
        st.error(f"Błąd pobierania świec: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=60)
def get_orderbook(symbol: str, limit: int = 20) -> dict:
    """Order book — Binance (może być niedostępny z Streamlit Cloud)."""
    try:
        r = requests.get(
            f"{BINANCE_BASE}/depth",
            params={"symbol": symbol, "limit": limit},
            timeout=5
        )
        d = r.json()
        if "bids" not in d:
            return {"error": "Order book niedostępny"}
        bids = [(float(p), float(q)) for p, q in d["bids"]]
        asks = [(float(p), float(q)) for p, q in d["asks"]]
        return {"bids": bids, "asks": asks}
    except Exception as e:
        return {"error": str(e)}


@st.cache_data(ttl=60)
def get_top_gainers(limit: int = 10):
    """Top movers 24h — CoinGecko."""
    try:
        r = requests.get(
            f"{COINGECKO_BASE}/coins/markets",
            params={
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": 100,
                "page": 1,
                "sparkline": "false",
                "price_change_percentage": "24h",
            },
            timeout=10
        )
        data = r.json()
        if not isinstance(data, list) or not data:
            return pd.DataFrame(), pd.DataFrame()
        df = pd.DataFrame(data)
        df = df.dropna(subset=["price_change_percentage_24h"])
        df["priceChangePercent"] = df["price_change_percentage_24h"].astype(float)
        df["lastPrice"] = df["current_price"].astype(float)
        df["quoteVolume"] = df["total_volume"].astype(float)
        df["symbol"] = df["symbol"].str.upper() + "USDT"

        gainers = df.nlargest(limit, "priceChangePercent")[
            ["symbol", "lastPrice", "priceChangePercent", "quoteVolume"]
        ]
        losers = df.nsmallest(limit, "priceChangePercent")[
            ["symbol", "lastPrice", "priceChangePercent", "quoteVolume"]
        ]
        return gainers, losers
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame()


@st.cache_data(ttl=60)
def get_funding_rate(symbol: str) -> float:
    try:
        r = requests.get(
            f"{BINANCE_FUTURES}/fundingRate",
            params={"symbol": symbol, "limit": 1},
            timeout=5
        )
        data = r.json()
        if data and isinstance(data, list):
            return float(data[-1]["fundingRate"]) * 100
        return 0.0
    except Exception:
        return 0.0


@st.cache_data(ttl=30)
def get_open_interest(symbol: str) -> float:
    try:
        r = requests.get(
            f"{BINANCE_FUTURES}/openInterest",
            params={"symbol": symbol},
            timeout=5
        )
        d = r.json()
        return float(d.get("openInterest", 0))
    except Exception:
        return 0.0
