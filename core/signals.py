"""
core/signals.py
Silnik sygnałów tradingowych - scalping + swing
Każdy sygnał ma score od -100 do +100 i confidence level
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional
from core.indicators import compute_all_indicators, support_resistance


@dataclass
class TradingSignal:
    action: str          # BUY / SELL / NEUTRAL
    score: int           # -100 do +100
    confidence: str      # LOW / MEDIUM / HIGH / VERY HIGH
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    risk_reward: float
    reasons: list[str]
    warnings: list[str]
    timeframe: str
    strategy: str


def score_to_signal(score: int) -> str:
    if score >= 30:
        return "BUY"
    elif score <= -30:
        return "SELL"
    return "NEUTRAL"


def score_to_confidence(score: int, num_reasons: int) -> str:
    abs_score = abs(score)
    if abs_score >= 70 and num_reasons >= 4:
        return "VERY HIGH"
    elif abs_score >= 50 and num_reasons >= 3:
        return "HIGH"
    elif abs_score >= 30 and num_reasons >= 2:
        return "MEDIUM"
    return "LOW"


def scalping_signal(df: pd.DataFrame, timeframe: str = "5m") -> TradingSignal:
    """
    Sygnał scalpingowy - krótkoterminowy, szybkie wejście/wyjście
    Timeframes: 1m, 3m, 5m
    """
    df = compute_all_indicators(df.copy())
    last = df.iloc[-1]
    prev = df.iloc[-2]

    score = 0
    reasons = []
    warnings = []

    price = last["close"]
    atr_val = last["atr"] if not pd.isna(last["atr"]) else price * 0.002

    # === RSI 7 (szybki dla scalpingu) ===
    rsi7 = last["rsi_7"]
    rsi14 = last["rsi_14"]
    if not pd.isna(rsi7):
        if rsi7 < 25:
            score += 25
            reasons.append(f"RSI(7)={rsi7:.1f} — głęboka wyprzedanie")
        elif rsi7 < 35:
            score += 15
            reasons.append(f"RSI(7)={rsi7:.1f} — wyprzedanie")
        elif rsi7 > 75:
            score -= 25
            reasons.append(f"RSI(7)={rsi7:.1f} — głębokie wykupienie")
        elif rsi7 > 65:
            score -= 15
            reasons.append(f"RSI(7)={rsi7:.1f} — wykupienie")

    # === MACD Crossover ===
    if not pd.isna(last["macd_hist"]) and not pd.isna(prev["macd_hist"]):
        if prev["macd_hist"] < 0 and last["macd_hist"] > 0:
            score += 20
            reasons.append("MACD crossover BYCZE (histogram zmienił znak)")
        elif prev["macd_hist"] > 0 and last["macd_hist"] < 0:
            score -= 20
            reasons.append("MACD crossover NIEDŹWIEDZIE (histogram zmienił znak)")
        elif last["macd_hist"] > 0 and last["macd_hist"] > prev["macd_hist"]:
            score += 8
            reasons.append("MACD histogram rośnie (momentum bycze)")
        elif last["macd_hist"] < 0 and last["macd_hist"] < prev["macd_hist"]:
            score -= 8
            reasons.append("MACD histogram spada (momentum niedźwiedzie)")

    # === Bollinger Bands ===
    if not pd.isna(last["bb_pct_b"]):
        pct_b = last["bb_pct_b"]
        if pct_b < 0.05:
            score += 20
            reasons.append(f"Cena przy dolnym BB ({pct_b:.2f}) — potencjalne odbicie")
        elif pct_b < 0.2:
            score += 10
            reasons.append(f"Cena blisko dolnego BB ({pct_b:.2f})")
        elif pct_b > 0.95:
            score -= 20
            reasons.append(f"Cena przy górnym BB ({pct_b:.2f}) — potencjalny opór")
        elif pct_b > 0.8:
            score -= 10
            reasons.append(f"Cena blisko górnego BB ({pct_b:.2f})")

    # === Stochastic ===
    if not pd.isna(last["stoch_k"]) and not pd.isna(last["stoch_d"]):
        k, d = last["stoch_k"], last["stoch_d"]
        pk, pd_prev = prev["stoch_k"], prev["stoch_d"]
        if k < 20 and d < 20:
            score += 15
            reasons.append(f"Stochastic wyprzedany K={k:.1f}, D={d:.1f}")
        elif k > 80 and d > 80:
            score -= 15
            reasons.append(f"Stochastic wykupiony K={k:.1f}, D={d:.1f}")
        # Crossover
        if pk < pd_prev and k > d:
            score += 10
            reasons.append("Stochastic bycze przecięcie K>D")
        elif pk > pd_prev and k < d:
            score -= 10
            reasons.append("Stochastic niedźwiedzie przecięcie K<D")

    # === EMA Trend ===
    if not pd.isna(last["ema_9"]) and not pd.isna(last["ema_21"]):
        if last["ema_9"] > last["ema_21"]:
            score += 10
            reasons.append("EMA9 > EMA21 — trend wzrostowy krótkoterminowy")
        else:
            score -= 10
            reasons.append("EMA9 < EMA21 — trend spadkowy krótkoterminowy")

    # === Volume ===
    if not pd.isna(last["volume_ratio"]):
        vol_ratio = last["volume_ratio"]
        if vol_ratio > 2.0:
            if score > 0:
                score += 10
                reasons.append(f"Wysoki wolumen ({vol_ratio:.1f}x śr.) potwierdza ruch")
            else:
                score -= 10
                reasons.append(f"Wysoki wolumen ({vol_ratio:.1f}x śr.) potwierdza spadek")
        elif vol_ratio < 0.5:
            warnings.append(f"Niski wolumen ({vol_ratio:.1f}x śr.) — słabe potwierdzenie")

    # === VWAP ===
    if not pd.isna(last["vwap"]):
        if price > last["vwap"]:
            score += 5
            reasons.append(f"Cena powyżej VWAP ({last['vwap']:.4f}) — bycze")
        else:
            score -= 5
            reasons.append(f"Cena poniżej VWAP ({last['vwap']:.4f}) — niedźwiedzie")

    # === Williams %R ===
    if not pd.isna(last["williams_r"]):
        wr = last["williams_r"]
        if wr < -80:
            score += 8
            reasons.append(f"Williams %R={wr:.1f} — wyprzedanie")
        elif wr > -20:
            score -= 8
            reasons.append(f"Williams %R={wr:.1f} — wykupienie")

    # === Warnings ===
    if not pd.isna(last["atr_pct"]) and last["atr_pct"] > 3.0:
        warnings.append(f"Wysoka zmienność ATR={last['atr_pct']:.2f}% — zwiększone ryzyko")
    if not pd.isna(last["bb_bandwidth"]) and last["bb_bandwidth"] < 1.0:
        warnings.append("Wąskie Bollinger Bands — możliwy wkrótce gwałtowny ruch (breakout)")

    # Clamp
    score = max(-100, min(100, score))
    action = score_to_signal(score)
    confidence = score_to_confidence(score, len(reasons))

    # === Poziomy SL/TP dla scalpingu (ciaśniejsze) ===
    sl_multiplier = 1.2
    tp1_multiplier = 1.0
    tp2_multiplier = 2.0
    tp3_multiplier = 3.0

    if action == "BUY":
        sl = price - (atr_val * sl_multiplier)
        tp1 = price + (atr_val * tp1_multiplier)
        tp2 = price + (atr_val * tp2_multiplier)
        tp3 = price + (atr_val * tp3_multiplier)
    elif action == "SELL":
        sl = price + (atr_val * sl_multiplier)
        tp1 = price - (atr_val * tp1_multiplier)
        tp2 = price - (atr_val * tp2_multiplier)
        tp3 = price - (atr_val * tp3_multiplier)
    else:
        sl = price - (atr_val * sl_multiplier)
        tp1 = price + (atr_val * tp1_multiplier)
        tp2 = price + (atr_val * tp2_multiplier)
        tp3 = price + (atr_val * tp3_multiplier)

    risk = abs(price - sl)
    reward = abs(tp2 - price)
    rr = reward / risk if risk > 0 else 0

    return TradingSignal(
        action=action, score=score, confidence=confidence,
        entry_price=price, stop_loss=sl,
        take_profit_1=tp1, take_profit_2=tp2, take_profit_3=tp3,
        risk_reward=rr, reasons=reasons, warnings=warnings,
        timeframe=timeframe, strategy="SCALPING"
    )


def swing_signal(df: pd.DataFrame, timeframe: str = "4h") -> TradingSignal:
    """
    Sygnał swingowy - średnioterminowy
    Timeframes: 1h, 4h, 1d
    """
    df = compute_all_indicators(df.copy())
    last = df.iloc[-1]
    prev = df.iloc[-2]

    score = 0
    reasons = []
    warnings = []

    price = last["close"]
    atr_val = last["atr"] if not pd.isna(last["atr"]) else price * 0.01

    # RSI 14
    rsi14 = last["rsi_14"]
    if not pd.isna(rsi14):
        if rsi14 < 30:
            score += 25
            reasons.append(f"RSI(14)={rsi14:.1f} — klasyczna strefa wyprzedania")
        elif rsi14 < 45:
            score += 10
            reasons.append(f"RSI(14)={rsi14:.1f} — lekko bycze")
        elif rsi14 > 70:
            score -= 25
            reasons.append(f"RSI(14)={rsi14:.1f} — klasyczna strefa wykupienia")
        elif rsi14 > 55:
            score -= 10
            reasons.append(f"RSI(14)={rsi14:.1f} — lekko niedźwiedzie")

    # MACD
    if not pd.isna(last["macd_line"]) and not pd.isna(last["macd_signal"]):
        if last["macd_line"] > last["macd_signal"] and prev["macd_line"] <= prev["macd_signal"]:
            score += 25
            reasons.append("MACD bycze przecięcie linii sygnału")
        elif last["macd_line"] < last["macd_signal"] and prev["macd_line"] >= prev["macd_signal"]:
            score -= 25
            reasons.append("MACD niedźwiedzie przecięcie linii sygnału")
        elif last["macd_line"] > last["macd_signal"]:
            score += 10
            reasons.append("MACD powyżej linii sygnału (trend bycze)")
        else:
            score -= 10
            reasons.append("MACD poniżej linii sygnału (trend niedźwiedzie)")

    # EMA trend - dłuższe okresy dla swingu
    if not pd.isna(last["ema_50"]) and not pd.isna(last["ema_200"]):
        if last["ema_50"] > last["ema_200"]:
            score += 15
            reasons.append("Golden Cross: EMA50 > EMA200 — silny trend wzrostowy")
        else:
            score -= 15
            reasons.append("Death Cross: EMA50 < EMA200 — silny trend spadkowy")

    if not pd.isna(last["ema_21"]):
        if price > last["ema_21"]:
            score += 10
            reasons.append(f"Cena powyżej EMA21 ({last['ema_21']:.4f})")
        else:
            score -= 10
            reasons.append(f"Cena poniżej EMA21 ({last['ema_21']:.4f})")

    # Bollinger + CCI
    if not pd.isna(last["cci"]):
        cci_val = last["cci"]
        if cci_val < -100:
            score += 15
            reasons.append(f"CCI={cci_val:.0f} — wyprzedanie (swing entry)")
        elif cci_val > 100:
            score -= 15
            reasons.append(f"CCI={cci_val:.0f} — wykupienie (swing exit)")

    # Volume confirmation
    if not pd.isna(last["volume_ratio"]) and last["volume_ratio"] > 1.5:
        if score > 0:
            score += 12
            reasons.append(f"Wolumen {last['volume_ratio']:.1f}x powyżej średniej — silne potwierdzenie")
        else:
            score -= 12
            reasons.append(f"Wolumen {last['volume_ratio']:.1f}x powyżej średniej — potwierdza spadek")

    if not pd.isna(last["atr_pct"]) and last["atr_pct"] < 0.5:
        warnings.append("Niska zmienność — mały potencjał zysku przy swingu")

    score = max(-100, min(100, score))
    action = score_to_signal(score)
    confidence = score_to_confidence(score, len(reasons))

    # Szersze TP/SL dla swingu
    if action == "BUY":
        sl = price - (atr_val * 2.0)
        tp1 = price + (atr_val * 1.5)
        tp2 = price + (atr_val * 3.0)
        tp3 = price + (atr_val * 5.0)
    elif action == "SELL":
        sl = price + (atr_val * 2.0)
        tp1 = price - (atr_val * 1.5)
        tp2 = price - (atr_val * 3.0)
        tp3 = price - (atr_val * 5.0)
    else:
        sl = price - (atr_val * 2.0)
        tp1 = price + (atr_val * 1.5)
        tp2 = price + (atr_val * 3.0)
        tp3 = price + (atr_val * 5.0)

    risk = abs(price - sl)
    reward = abs(tp2 - price)
    rr = reward / risk if risk > 0 else 0

    return TradingSignal(
        action=action, score=score, confidence=confidence,
        entry_price=price, stop_loss=sl,
        take_profit_1=tp1, take_profit_2=tp2, take_profit_3=tp3,
        risk_reward=rr, reasons=reasons, warnings=warnings,
        timeframe=timeframe, strategy="SWING"
    )


def get_signal_for_timeframe(df: pd.DataFrame, timeframe: str) -> TradingSignal:
    """Router — dobiera strategię na podstawie timeframe"""
    scalping_tfs = ["1m", "3m", "5m"]
    swing_tfs = ["1h", "4h", "1d"]

    if timeframe in scalping_tfs:
        return scalping_signal(df, timeframe)
    else:
        return swing_signal(df, timeframe)


def multi_timeframe_analysis(symbol: str, get_klines_func) -> dict:
    """Analiza Multi-Timeframe (MTF) dla danego symbolu"""
    timeframes = ["5m", "15m", "1h", "4h"]
    results = {}

    for tf in timeframes:
        df = get_klines_func(symbol, tf, 200)
        if not df.empty:
            results[tf] = get_signal_for_timeframe(df, tf)

    return results
