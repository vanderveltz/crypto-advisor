"""
core/indicators.py
Silnik wskaźników technicznych - RSI, MACD, Bollinger Bands, EMA, Stochastic, ATR itd.
"""

import pandas as pd
import numpy as np


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period).mean()


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2.0):
    middle = sma(series, period)
    std = series.rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    bandwidth = (upper - lower) / middle * 100
    pct_b = (series - lower) / (upper - lower)
    return upper, middle, lower, bandwidth, pct_b


def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3):
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    d = k.rolling(window=d_period).mean()
    return k, d


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    typical_price = (high + low + close) / 3
    cumulative_tp_vol = (typical_price * volume).cumsum()
    cumulative_vol = volume.cumsum()
    return cumulative_tp_vol / cumulative_vol


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = np.sign(close.diff())
    return (direction * volume).cumsum()


def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    highest_high = high.rolling(window=period).max()
    lowest_low = low.rolling(window=period).min()
    return -100 * (highest_high - close) / (highest_high - lowest_low)


def cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
    typical_price = (high + low + close) / 3
    mean_tp = typical_price.rolling(window=period).mean()
    mean_deviation = typical_price.rolling(window=period).apply(
        lambda x: np.abs(x - x.mean()).mean()
    )
    return (typical_price - mean_tp) / (0.015 * mean_deviation)


def support_resistance(df: pd.DataFrame, window: int = 10, num_levels: int = 3):
    """Wykrywa poziomy wsparcia i oporu"""
    highs = df["high"].rolling(window=window, center=True).max()
    lows = df["low"].rolling(window=window, center=True).min()

    resistance_levels = []
    support_levels = []

    for i in range(window, len(df) - window):
        if df["high"].iloc[i] == highs.iloc[i]:
            resistance_levels.append(df["high"].iloc[i])
        if df["low"].iloc[i] == lows.iloc[i]:
            support_levels.append(df["low"].iloc[i])

    # Grupuj bliskie poziomy
    def cluster_levels(levels, threshold_pct=0.005):
        if not levels:
            return []
        levels = sorted(set(levels))
        clusters = []
        current_cluster = [levels[0]]
        for level in levels[1:]:
            if (level - current_cluster[-1]) / current_cluster[-1] < threshold_pct:
                current_cluster.append(level)
            else:
                clusters.append(np.mean(current_cluster))
                current_cluster = [level]
        clusters.append(np.mean(current_cluster))
        return clusters

    support = cluster_levels(support_levels)[-num_levels:]
    resistance = cluster_levels(resistance_levels)[:num_levels]

    return support, resistance


def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Oblicza wszystkie wskaźniki dla DataFrame ze świecami"""
    if df.empty or len(df) < 30:
        return df

    c = df["close"]
    h = df["high"]
    l = df["low"]
    v = df["volume"]

    # Trend
    df["ema_9"] = ema(c, 9)
    df["ema_21"] = ema(c, 21)
    df["ema_50"] = ema(c, 50)
    df["ema_200"] = ema(c, 200)
    df["sma_20"] = sma(c, 20)

    # Momentum
    df["rsi_14"] = rsi(c, 14)
    df["rsi_7"] = rsi(c, 7)
    df["macd_line"], df["macd_signal"], df["macd_hist"] = macd(c)
    df["stoch_k"], df["stoch_d"] = stochastic(h, l, c)
    df["williams_r"] = williams_r(h, l, c)
    df["cci"] = cci(h, l, c)

    # Volatility
    df["bb_upper"], df["bb_middle"], df["bb_lower"], df["bb_bandwidth"], df["bb_pct_b"] = bollinger_bands(c)
    df["atr"] = atr(h, l, c)
    df["atr_pct"] = df["atr"] / c * 100

    # Volume
    df["vwap"] = vwap(h, l, c, v)
    df["obv"] = obv(c, v)
    df["volume_sma"] = sma(v, 20)
    df["volume_ratio"] = v / df["volume_sma"]

    return df
