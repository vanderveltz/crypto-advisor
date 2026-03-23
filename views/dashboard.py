"""
pages/dashboard.py
Główny dashboard — przegląd rynku, ceny, movers
"""

import streamlit as st
import pandas as pd
from core.binance_client import get_price, get_top_gainers, POPULAR_PAIRS
from core.signals import get_signal_for_timeframe
from core.binance_client import get_klines


def _html(s: str) -> None:
    cleaned = "\n".join(line.lstrip() for line in s.split("\n"))
    st.markdown(cleaned, unsafe_allow_html=True)


def show_dashboard():
    st.markdown('<div style="font-size:28px; font-weight:800; color:#f1f5f9; margin-bottom:4px;">📊 Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#4b5563; font-size:13px; margin-bottom:24px;">Przegląd rynku kryptowalut w czasie rzeczywistym</div>', unsafe_allow_html=True)

    # Quick signal for selected pair
    col_pair, col_tf, col_btn = st.columns([2, 2, 1])
    with col_pair:
        selected = st.selectbox("Para", POPULAR_PAIRS, index=0, key="dash_pair")
    with col_tf:
        tf = st.selectbox("Timeframe", ["1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d"], index=2, key="dash_tf")
    with col_btn:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        refresh = st.button("🔄 Odśwież")

    # Price metrics
    data = get_price(selected)
    if "error" in data:
        st.error(f"Błąd połączenia z Binance API: {data['error']}")
    if "error" not in data:
        price = data["price"]
        change = data["change_pct"]
        change_class = "metric-change-pos" if change >= 0 else "metric-change-neg"
        change_arrow = "▲" if change >= 0 else "▼"

        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:
            _html(f"""
            <div class="metric-card">
                <div class="metric-label">CENA</div>
                <div class="metric-value">${price:,.4f}</div>
                <div class="{change_class}">{change_arrow} {abs(change):.2f}% (24h)</div>
            </div>""")
        with c2:
            _html(f"""
            <div class="metric-card">
                <div class="metric-label">24H HIGH</div>
                <div class="metric-value" style="font-size:20px; color:#10b981">${data['high']:,.4f}</div>
            </div>""")
        with c3:
            _html(f"""
            <div class="metric-card">
                <div class="metric-label">24H LOW</div>
                <div class="metric-value" style="font-size:20px; color:#ef4444">${data['low']:,.4f}</div>
            </div>""")
        with c4:
            vol_m = data["quote_volume"] / 1_000_000
            _html(f"""
            <div class="metric-card">
                <div class="metric-label">WOLUMEN 24H</div>
                <div class="metric-value" style="font-size:20px">${vol_m:.1f}M</div>
            </div>""")
        with c5:
            _html(f"""
            <div class="metric-card">
                <div class="metric-label">TRANSAKCJE 24H</div>
                <div class="metric-value" style="font-size:20px">{data['trades']:,}</div>
            </div>""")

    # Quick Signal Box
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    df = get_klines(selected, tf, 200)
    if not df.empty:
        signal = get_signal_for_timeframe(df, tf)

        if signal.action == "BUY":
            css_class = "alert-buy"
            icon = "🟢"
            badge = '<span class="signal-buy">▲ KUPNO</span>'
        elif signal.action == "SELL":
            css_class = "alert-sell"
            icon = "🔴"
            badge = '<span class="signal-sell">▼ SPRZEDAŻ</span>'
        else:
            css_class = "alert-neutral"
            icon = "⚪"
            badge = '<span class="signal-neutral">◆ NEUTRALNY</span>'

        _html(f"""
        <div class="{css_class}">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                <div>
                    <div style="color:#9ca3af; font-size:11px; margin-bottom:6px; letter-spacing:1px;">SYGNAŁ {signal.strategy} · {tf}</div>
                    {badge}
                    <span style="margin-left:12px; color:#9ca3af; font-size:13px;">Score: {signal.score:+d}/100 · Pewność: {signal.confidence}</span>
                </div>
                <div style="display:flex; gap:24px;">
                    <div style="text-align:center;">
                        <div style="color:#6b7280; font-size:10px;">ENTRY</div>
                        <div style="color:#f1f5f9; font-family:'JetBrains Mono'; font-size:15px;">${signal.entry_price:,.4f}</div>
                    </div>
                    <div style="text-align:center;">
                        <div style="color:#6b7280; font-size:10px;">STOP LOSS</div>
                        <div style="color:#ef4444; font-family:'JetBrains Mono'; font-size:15px;">${signal.stop_loss:,.4f}</div>
                    </div>
                    <div style="text-align:center;">
                        <div style="color:#6b7280; font-size:10px;">TP1 / TP2</div>
                        <div style="color:#10b981; font-family:'JetBrains Mono'; font-size:15px;">${signal.take_profit_1:,.4f} / ${signal.take_profit_2:,.4f}</div>
                    </div>
                    <div style="text-align:center;">
                        <div style="color:#6b7280; font-size:10px;">R:R</div>
                        <div style="color:#818cf8; font-family:'JetBrains Mono'; font-size:15px;">1:{signal.risk_reward:.1f}</div>
                    </div>
                </div>
            </div>
            {'<div style="margin-top:10px;">' + ' · '.join([f'<span style="color:#9ca3af; font-size:12px;">{r}</span>' for r in signal.reasons[:3]]) + '</div>' if signal.reasons else ''}
        </div>
        """)

    # Market movers
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    col_g, col_l = st.columns(2)

    gainers, losers = get_top_gainers(8)

    if gainers.empty and losers.empty:
        st.warning("Brak danych Top Movers — Binance API niedostępne lub rate limit.")

    with col_g:
        st.markdown('<div class="section-header">🚀 TOP WZROSTY (24H)</div>', unsafe_allow_html=True)
        if not gainers.empty:
            for _, row in gainers.iterrows():
                vol_m = row["quoteVolume"] / 1_000_000
                _html(f"""
                <div class="indicator-row">
                    <span class="indicator-name">{row['symbol']}</span>
                    <span style="color:#10b981; font-family:'JetBrains Mono'; font-size:13px;">
                        +{row['priceChangePercent']:.2f}%
                        <span style="color:#4b5563; font-size:11px; margin-left:8px;">${vol_m:.0f}M</span>
                    </span>
                </div>
                """)

    with col_l:
        st.markdown('<div class="section-header">📉 TOP SPADKI (24H)</div>', unsafe_allow_html=True)
        if not losers.empty:
            for _, row in losers.iterrows():
                vol_m = row["quoteVolume"] / 1_000_000
                _html(f"""
                <div class="indicator-row">
                    <span class="indicator-name">{row['symbol']}</span>
                    <span style="color:#ef4444; font-family:'JetBrains Mono'; font-size:13px;">
                        {row['priceChangePercent']:.2f}%
                        <span style="color:#4b5563; font-size:11px; margin-left:8px;">${vol_m:.0f}M</span>
                    </span>
                </div>
                """)

    # Watchlist
    st.markdown('<div class="section-header" style="margin-top:20px;">👁️ WATCHLIST — SZYBKI PRZEGLĄD</div>', unsafe_allow_html=True)

    watchlist = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT"]
    cols = st.columns(len(watchlist))

    for i, sym in enumerate(watchlist):
        d = get_price(sym)
        if "error" not in d:
            chg = d["change_pct"]
            color = "#10b981" if chg >= 0 else "#ef4444"
            arrow = "▲" if chg >= 0 else "▼"
            with cols[i]:
                _html(f"""
                <div class="metric-card" style="text-align:center; padding:14px;">
                    <div style="color:#9ca3af; font-size:11px; margin-bottom:4px;">{sym.replace('USDT','')}</div>
                    <div style="color:#f1f5f9; font-family:'JetBrains Mono'; font-size:14px; font-weight:600;">${d['price']:,.3f}</div>
                    <div style="color:{color}; font-size:12px;">{arrow} {abs(chg):.2f}%</div>
                </div>
                """)
