"""
pages/signals.py
Strona sygnałów — Multi-timeframe, szczegółowe sygnały, skaner
"""

import streamlit as st
import pandas as pd
from core.binance_client import get_klines, get_price, POPULAR_PAIRS
from core.signals import get_signal_for_timeframe, multi_timeframe_analysis
from core.indicators import compute_all_indicators
from core.ai_advisor import analyze_with_claude
import time


def _html(s: str) -> None:
    """Remove per-line leading whitespace so Markdown doesn't treat indented HTML as code blocks."""
    cleaned = "\n".join(line.lstrip() for line in s.split("\n"))
    st.markdown(cleaned, unsafe_allow_html=True)


def signal_badge(action: str) -> str:
    if action == "BUY":
        return '<span class="signal-buy">▲ KUPNO</span>'
    elif action == "SELL":
        return '<span class="signal-sell">▼ SPRZEDAŻ</span>'
    return '<span class="signal-neutral">◆ NEUTRAL</span>'


def confidence_bar(confidence: str) -> str:
    vals = {"LOW": 25, "MEDIUM": 50, "HIGH": 75, "VERY HIGH": 100}
    colors = {"LOW": "#6b7280", "MEDIUM": "#f59e0b", "HIGH": "#10b981", "VERY HIGH": "#6366f1"}
    pct = vals.get(confidence, 25)
    color = colors.get(confidence, "#6b7280")
    return f"""
    <div style="background:#1e2130; border-radius:4px; height:6px; width:100%; margin-top:4px;">
        <div style="background:{color}; width:{pct}%; height:6px; border-radius:4px;"></div>
    </div>
    <div style="color:{color}; font-size:11px; margin-top:3px;">{confidence}</div>
    """


def show_signals():
    st.markdown('<div style="font-size:28px; font-weight:800; color:#f1f5f9; margin-bottom:4px;">🎯 Sygnały Tradingowe</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#4b5563; font-size:13px; margin-bottom:24px;">Analiza Multi-Timeframe + szczegółowe sygnały</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📍 Szczegółowy Sygnał", "🔍 Skaner Rynku"])

    # === TAB 1: Detailed Signal ===
    with tab1:
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            symbol = st.selectbox("Para handlowa", POPULAR_PAIRS, key="sig_symbol")
        with col2:
            timeframe = st.selectbox("Timeframe", ["1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d"], index=2, key="sig_tf")
        with col3:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            analyze = st.button("🎯 Analizuj")

        if symbol:
            df = get_klines(symbol, timeframe, 200)
            price_data = get_price(symbol)

            if not df.empty:
                signal = get_signal_for_timeframe(df, timeframe)

                # Main signal display
                if signal.action == "BUY":
                    css = "alert-buy"
                elif signal.action == "SELL":
                    css = "alert-sell"
                else:
                    css = "alert-neutral"

                _html(f"""
                <div class="{css}" style="margin-bottom:20px;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:16px;">
                        <div>
                            <div style="color:#9ca3af; font-size:11px; letter-spacing:2px; margin-bottom:8px;">{signal.strategy} · {timeframe} · {symbol}</div>
                            <div style="margin-bottom:8px;">{signal_badge(signal.action)}</div>
                            <div style="color:#9ca3af; font-size:13px;">Score: <span style="color:#f1f5f9; font-weight:600;">{signal.score:+d}/100</span></div>
                            {confidence_bar(signal.confidence)}
                        </div>
                        <div style="display:grid; grid-template-columns: repeat(4, auto); gap:20px;">
                            <div>
                                <div style="color:#6b7280; font-size:10px; letter-spacing:1px;">ENTRY</div>
                                <div style="color:#f1f5f9; font-family:'JetBrains Mono'; font-size:18px; font-weight:700;">${signal.entry_price:,.4f}</div>
                            </div>
                            <div>
                                <div style="color:#6b7280; font-size:10px; letter-spacing:1px;">STOP LOSS</div>
                                <div style="color:#ef4444; font-family:'JetBrains Mono'; font-size:18px; font-weight:700;">${signal.stop_loss:,.4f}</div>
                                <div style="color:#6b7280; font-size:11px;">{abs(signal.entry_price-signal.stop_loss)/signal.entry_price*100:.2f}%</div>
                            </div>
                            <div>
                                <div style="color:#6b7280; font-size:10px; letter-spacing:1px;">TP1 / TP2 / TP3</div>
                                <div style="color:#10b981; font-family:'JetBrains Mono'; font-size:14px;">${signal.take_profit_1:,.4f}</div>
                                <div style="color:#10b981; font-family:'JetBrains Mono'; font-size:14px;">${signal.take_profit_2:,.4f}</div>
                                <div style="color:#6ee7b7; font-family:'JetBrains Mono'; font-size:14px;">${signal.take_profit_3:,.4f}</div>
                            </div>
                            <div>
                                <div style="color:#6b7280; font-size:10px; letter-spacing:1px;">RISK:REWARD</div>
                                <div style="color:#818cf8; font-family:'JetBrains Mono'; font-size:24px; font-weight:700;">1:{signal.risk_reward:.1f}</div>
                            </div>
                        </div>
                    </div>
                </div>
                """)

                # Reasons & Warnings
                col_r, col_w = st.columns(2)
                with col_r:
                    st.markdown('<div class="section-header">✅ SYGNAŁY WEJŚCIA</div>', unsafe_allow_html=True)
                    for reason in signal.reasons:
                        icon = "🟢" if signal.action == "BUY" else "🔴" if signal.action == "SELL" else "⚪"
                        _html(f"""
                        <div style="display:flex; align-items:flex-start; gap:8px; padding:8px 0; border-bottom:1px solid #1e2130;">
                            <span>{icon}</span>
                            <span style="color:#d1d5db; font-size:13px;">{reason}</span>
                        </div>
                        """)

                with col_w:
                    st.markdown('<div class="section-header">⚠️ OSTRZEŻENIA</div>', unsafe_allow_html=True)
                    if signal.warnings:
                        for warning in signal.warnings:
                            _html(f"""
                            <div style="display:flex; align-items:flex-start; gap:8px; padding:8px 0; border-bottom:1px solid #1e2130;">
                                <span>⚠️</span>
                                <span style="color:#f59e0b; font-size:13px;">{warning}</span>
                            </div>
                            """)
                    else:
                        st.markdown('<div style="color:#10b981; font-size:13px; padding:8px 0;">✓ Brak ostrzeżeń</div>', unsafe_allow_html=True)

                # Multi-timeframe table
                st.markdown('<div class="section-header" style="margin-top:24px;">🌐 ANALIZA MULTI-TIMEFRAME</div>', unsafe_allow_html=True)

                mtf_tfs = ["1m", "5m", "15m", "1h", "4h"]
                mtf_cols = st.columns(len(mtf_tfs))

                for i, tf in enumerate(mtf_tfs):
                    df_tf = get_klines(symbol, tf, 100)
                    if not df_tf.empty:
                        s = get_signal_for_timeframe(df_tf, tf)
                        with mtf_cols[i]:
                            color = "#10b981" if s.action == "BUY" else "#ef4444" if s.action == "SELL" else "#6b7280"
                            icon = "▲" if s.action == "BUY" else "▼" if s.action == "SELL" else "◆"
                            _html(f"""
                            <div class="metric-card" style="text-align:center;">
                                <div style="color:#9ca3af; font-size:11px; margin-bottom:8px;">{tf}</div>
                                <div style="color:{color}; font-size:20px; font-weight:800;">{icon}</div>
                                <div style="color:{color}; font-size:12px; font-weight:600;">{s.action}</div>
                                <div style="color:#4b5563; font-size:11px; margin-top:4px;">{s.score:+d}/100</div>
                            </div>
                            """)

                # Indicators snapshot
                df_ind = compute_all_indicators(df.copy())
                last = df_ind.iloc[-1]

                st.markdown('<div class="section-header" style="margin-top:24px;">📏 WSKAŹNIKI TECHNICZNE</div>', unsafe_allow_html=True)

                col_a, col_b, col_c = st.columns(3)

                def ind_row(name, val, unit="", bullish_above=None, bullish_below=None):
                    if pd.isna(val):
                        return f'<div class="indicator-row"><span class="indicator-name">{name}</span><span class="indicator-val">N/A</span></div>'
                    formatted = f"{val:.4f}{unit}" if abs(val) < 10000 else f"{val:,.0f}{unit}"
                    color = "#f1f5f9"
                    if bullish_above is not None:
                        color = "#10b981" if val > bullish_above else "#ef4444"
                    elif bullish_below is not None:
                        color = "#10b981" if val < bullish_below else "#ef4444"
                    return f'<div class="indicator-row"><span class="indicator-name">{name}</span><span class="indicator-val" style="color:{color};">{formatted}</span></div>'

                with col_a:
                    st.markdown("**Momentum**", unsafe_allow_html=False)
                    st.markdown(
                        ind_row("RSI(14)", last.get("rsi_14"), bullish_below=50) +
                        ind_row("RSI(7)", last.get("rsi_7"), bullish_below=50) +
                        ind_row("MACD Line", last.get("macd_line"), bullish_above=0) +
                        ind_row("MACD Signal", last.get("macd_signal")) +
                        ind_row("MACD Hist", last.get("macd_hist"), bullish_above=0),
                        unsafe_allow_html=True
                    )

                with col_b:
                    st.markdown("**Trend**", unsafe_allow_html=False)
                    price_now = last["close"]
                    st.markdown(
                        ind_row("EMA 9", last.get("ema_9"), bullish_below=price_now) +
                        ind_row("EMA 21", last.get("ema_21"), bullish_below=price_now) +
                        ind_row("EMA 50", last.get("ema_50"), bullish_below=price_now) +
                        ind_row("Stoch K", last.get("stoch_k"), bullish_below=50) +
                        ind_row("Stoch D", last.get("stoch_d"), bullish_below=50),
                        unsafe_allow_html=True
                    )

                with col_c:
                    st.markdown("**Zmienność / Wolumen**", unsafe_allow_html=False)
                    st.markdown(
                        ind_row("BB Upper", last.get("bb_upper")) +
                        ind_row("BB Lower", last.get("bb_lower")) +
                        ind_row("BB %B", last.get("bb_pct_b")) +
                        ind_row("ATR%", last.get("atr_pct")) +
                        ind_row("Vol Ratio", last.get("volume_ratio"), bullish_above=1.0),
                        unsafe_allow_html=True
                    )

                # === Claude AI Analysis ===
                st.markdown('<div class="section-header" style="margin-top:28px;">🤖 ANALIZA CLAUDE AI</div>', unsafe_allow_html=True)

                if st.button("🤖 Zapytaj Claude AI o ten sygnał", key="claude_analyze"):
                    # Zbuduj MTF dict dla Claude
                    mtf_for_claude = {}
                    for tf in ["1m", "5m", "15m", "1h", "4h"]:
                        df_mtf = get_klines(symbol, tf, 100)
                        if not df_mtf.empty:
                            mtf_for_claude[tf] = get_signal_for_timeframe(df_mtf, tf)

                    # Kluczowe wskaźniki jako dict
                    indicators_for_claude = {
                        "RSI(14)": last.get("rsi_14"),
                        "RSI(7)": last.get("rsi_7"),
                        "MACD Line": last.get("macd_line"),
                        "MACD Hist": last.get("macd_hist"),
                        "Stoch K": last.get("stoch_k"),
                        "Stoch D": last.get("stoch_d"),
                        "BB %B": last.get("bb_pct_b"),
                        "BB Bandwidth": last.get("bb_bandwidth"),
                        "ATR%": last.get("atr_pct"),
                        "Vol Ratio": last.get("volume_ratio"),
                        "Williams %R": last.get("williams_r"),
                        "CCI": last.get("cci"),
                        "EMA9": last.get("ema_9"),
                        "EMA21": last.get("ema_21"),
                        "EMA50": last.get("ema_50"),
                    }

                    with st.spinner("Claude analizuje sygnał..."):
                        analyze_with_claude(symbol, timeframe, signal, indicators_for_claude, mtf_for_claude)

    # === TAB 2: Market Scanner ===
    with tab2:
        st.markdown('<div style="color:#9ca3af; font-size:13px; margin-bottom:16px;">Skanuje rynek w poszukiwaniu aktywnych sygnałów</div>', unsafe_allow_html=True)

        scan_tf = st.selectbox("Timeframe skanowania", ["5m", "15m", "1h", "4h"], index=0, key="scan_tf")
        scan_pairs = st.multiselect("Pary do skanowania", POPULAR_PAIRS, default=POPULAR_PAIRS[:10], key="scan_pairs")

        if st.button("🔍 Uruchom Skaner"):
            results = []
            progress = st.progress(0, text="Skanowanie...")

            for i, sym in enumerate(scan_pairs):
                df_s = get_klines(sym, scan_tf, 100)
                if not df_s.empty:
                    s = get_signal_for_timeframe(df_s, scan_tf)
                    if s.action != "NEUTRAL":
                        results.append({
                            "Para": sym,
                            "Sygnał": s.action,
                            "Score": s.score,
                            "Pewność": s.confidence,
                            "Entry": f"${s.entry_price:,.4f}",
                            "SL": f"${s.stop_loss:,.4f}",
                            "TP2": f"${s.take_profit_2:,.4f}",
                            "R:R": f"1:{s.risk_reward:.1f}",
                            "Powody": len(s.reasons),
                        })
                progress.progress((i + 1) / len(scan_pairs), text=f"Skanowanie {sym}...")

            progress.empty()

            if results:
                df_results = pd.DataFrame(results)
                df_results = df_results.sort_values("Score", key=abs, ascending=False)

                st.markdown(f'<div style="color:#10b981; font-size:14px; margin-bottom:12px;">✓ Znaleziono {len(results)} aktywnych sygnałów</div>', unsafe_allow_html=True)

                for _, row in df_results.iterrows():
                    is_buy = row["Sygnał"] == "BUY"
                    css = "alert-buy" if is_buy else "alert-sell"
                    badge_html = f'<span class="signal-buy">▲ KUPNO</span>' if is_buy else f'<span class="signal-sell">▼ SPRZEDAŻ</span>'

                    _html(f"""
                    <div class="{css}" style="margin-bottom:8px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                            <div style="display:flex; align-items:center; gap:12px;">
                                <span style="color:#f1f5f9; font-weight:700; font-size:15px;">{row['Para']}</span>
                                {badge_html}
                                <span style="color:#9ca3af; font-size:12px;">Score: {row['Score']:+d} · {row['Pewność']}</span>
                            </div>
                            <div style="display:flex; gap:20px; font-family:'JetBrains Mono'; font-size:13px;">
                                <span style="color:#9ca3af;">Entry: <span style="color:#f1f5f9;">{row['Entry']}</span></span>
                                <span style="color:#9ca3af;">SL: <span style="color:#ef4444;">{row['SL']}</span></span>
                                <span style="color:#9ca3af;">TP: <span style="color:#10b981;">{row['TP2']}</span></span>
                                <span style="color:#9ca3af;">R:R: <span style="color:#818cf8;">{row['R:R']}</span></span>
                            </div>
                        </div>
                    </div>
                    """)
            else:
                st.markdown('<div class="alert-neutral">Brak aktywnych sygnałów na wybranych parach dla tego timeframe\'u</div>', unsafe_allow_html=True)
