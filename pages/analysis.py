"""
pages/analysis.py
Strona analizy technicznej — wykresy OHLCV, wskaźniki, order book
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from core.binance_client import get_klines, get_orderbook, get_price, POPULAR_PAIRS
from core.indicators import compute_all_indicators


CHART_THEME = dict(
    paper_bgcolor="#0d0f14",
    plot_bgcolor="#111318",
    font_color="#9ca3af",
)


def candlestick_chart(df: pd.DataFrame, symbol: str, show_bb: bool = True, show_ema: bool = True) -> go.Figure:
    df = compute_all_indicators(df.copy())

    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.55, 0.15, 0.15, 0.15],
        subplot_titles=["", "RSI", "MACD", "Volume"]
    )

    # Candles
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["open"], high=df["high"],
        low=df["low"], close=df["close"],
        increasing_line_color="#10b981", decreasing_line_color="#ef4444",
        increasing_fillcolor="#10b981", decreasing_fillcolor="#ef4444",
        name="OHLCV", showlegend=False
    ), row=1, col=1)

    # Bollinger Bands
    if show_bb and "bb_upper" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["bb_upper"], line=dict(color="#6366f1", width=0.8, dash="dot"), name="BB Upper", showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["bb_lower"], line=dict(color="#6366f1", width=0.8, dash="dot"), name="BB Lower",
                                  fill="tonexty", fillcolor="rgba(99,102,241,0.05)", showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["bb_middle"], line=dict(color="#818cf8", width=0.6), name="BB Mid", showlegend=False), row=1, col=1)

    # EMAs
    if show_ema:
        for period, color in [(9, "#f59e0b"), (21, "#3b82f6"), (50, "#a78bfa")]:
            col = f"ema_{period}"
            if col in df.columns:
                fig.add_trace(go.Scatter(x=df.index, y=df[col], line=dict(color=color, width=1.2),
                                          name=f"EMA{period}", showlegend=True), row=1, col=1)

    # VWAP
    if "vwap" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["vwap"], line=dict(color="#f472b6", width=1.2, dash="dash"),
                                  name="VWAP", showlegend=True), row=1, col=1)

    # RSI
    if "rsi_14" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["rsi_14"], line=dict(color="#818cf8", width=1.5), name="RSI(14)", showlegend=False), row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="#ef4444", line_width=0.8, row=2, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="#10b981", line_width=0.8, row=2, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="#374151", line_width=0.8, row=2, col=1)
        fig.add_hrect(y0=70, y1=100, fillcolor="rgba(239,68,68,0.05)", row=2, col=1)
        fig.add_hrect(y0=0, y1=30, fillcolor="rgba(16,185,129,0.05)", row=2, col=1)

    # MACD
    if "macd_line" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["macd_line"], line=dict(color="#3b82f6", width=1.5), name="MACD", showlegend=False), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["macd_signal"], line=dict(color="#f59e0b", width=1.2), name="Signal", showlegend=False), row=3, col=1)
        colors = ["#10b981" if v >= 0 else "#ef4444" for v in df["macd_hist"]]
        fig.add_trace(go.Bar(x=df.index, y=df["macd_hist"], marker_color=colors, name="Histogram", showlegend=False), row=3, col=1)

    # Volume
    vol_colors = ["#10b981" if df["close"].iloc[i] >= df["open"].iloc[i] else "#ef4444" for i in range(len(df))]
    fig.add_trace(go.Bar(x=df.index, y=df["volume"], marker_color=vol_colors, name="Volume", showlegend=False), row=4, col=1)
    if "volume_sma" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["volume_sma"], line=dict(color="#818cf8", width=1.2), name="Vol SMA", showlegend=False), row=4, col=1)

    fig.update_layout(
        **CHART_THEME,
        height=750,
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis_rangeslider_visible=False,
        legend=dict(
            bgcolor="rgba(17,19,24,0.8)",
            bordercolor="#252a3a", borderwidth=1,
            font=dict(color="#9ca3af", size=11)
        ),
        hovermode="x unified"
    )

    for i in range(1, 5):
        fig.update_yaxes(
            gridcolor="#1e2130", gridwidth=0.5,
            zerolinecolor="#252a3a",
            tickfont=dict(color="#6b7280", size=10),
            row=i, col=1
        )
    fig.update_xaxes(gridcolor="#1e2130", tickfont=dict(color="#6b7280", size=10))

    return fig


def orderbook_chart(symbol: str) -> go.Figure:
    ob = get_orderbook(symbol, 20)
    if "error" in ob:
        return None

    bid_prices = [b[0] for b in ob["bids"]]
    bid_sizes = [b[1] for b in ob["bids"]]
    ask_prices = [a[0] for a in ob["asks"]]
    ask_sizes = [a[1] for a in ob["asks"]]

    bid_cumulative = []
    total = 0
    for s in bid_sizes:
        total += s
        bid_cumulative.append(total)

    ask_cumulative = []
    total = 0
    for s in ask_sizes:
        total += s
        ask_cumulative.append(total)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=bid_prices, y=bid_cumulative, mode="lines", fill="tozeroy",
                              fillcolor="rgba(16,185,129,0.15)", line=dict(color="#10b981", width=1.5), name="Bids"))
    fig.add_trace(go.Scatter(x=ask_prices, y=ask_cumulative, mode="lines", fill="tozeroy",
                              fillcolor="rgba(239,68,68,0.15)", line=dict(color="#ef4444", width=1.5), name="Asks"))

    fig.update_layout(
        **CHART_THEME, height=250,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=True,
        xaxis=dict(gridcolor="#1e2130"),
        yaxis=dict(gridcolor="#1e2130", title="Kumulatywny wolumen")
    )
    return fig


def show_analysis():
    st.markdown('<div style="font-size:28px; font-weight:800; color:#f1f5f9; margin-bottom:4px;">🔬 Analiza Techniczna</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#4b5563; font-size:13px; margin-bottom:24px;">Wykresy OHLCV, wskaźniki, order book</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    with col1:
        symbol = st.selectbox("Para", POPULAR_PAIRS, key="anal_symbol")
    with col2:
        tf = st.selectbox("Timeframe", ["1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d"], index=4, key="anal_tf")
    with col3:
        show_bb = st.checkbox("Bollinger", value=True)
    with col4:
        show_ema = st.checkbox("EMA", value=True)

    df = get_klines(symbol, tf, 200)
    if not df.empty:
        fig = candlestick_chart(df, symbol, show_bb, show_ema)
        st.plotly_chart(fig, use_container_width=True)

    # Order book
    st.markdown('<div class="section-header">📖 ORDER BOOK DEPTH</div>', unsafe_allow_html=True)

    col_ob, col_stats = st.columns([2, 1])
    with col_ob:
        ob_fig = orderbook_chart(symbol)
        if ob_fig:
            st.plotly_chart(ob_fig, use_container_width=True)

    with col_stats:
        ob = get_orderbook(symbol, 20)
        if "error" not in ob:
            total_bids = sum(b[1] for b in ob["bids"])
            total_asks = sum(a[1] for a in ob["asks"])
            bid_ratio = total_bids / (total_bids + total_asks) * 100
            ask_ratio = 100 - bid_ratio

            sentiment = "BYCZE 🟢" if bid_ratio > 55 else "NIEDŹWIEDZIE 🔴" if ask_ratio > 55 else "NEUTRALNE ⚪"

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">SENTYMENT ORDERBOOK</div>
                <div class="metric-value" style="font-size:18px; margin:8px 0;">{sentiment}</div>
                <div style="background:#1e2130; border-radius:4px; height:8px; margin:8px 0; overflow:hidden;">
                    <div style="background:#10b981; width:{bid_ratio:.0f}%; height:8px; float:left;"></div>
                    <div style="background:#ef4444; width:{ask_ratio:.0f}%; height:8px; float:left;"></div>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:12px;">
                    <span style="color:#10b981;">Bids {bid_ratio:.1f}%</span>
                    <span style="color:#ef4444;">Asks {ask_ratio:.1f}%</span>
                </div>
            </div>
            <div class="metric-card" style="margin-top:8px;">
                <div class="metric-label">BEST BID</div>
                <div style="color:#10b981; font-family:'JetBrains Mono'; font-size:16px;">${ob['bids'][0][0]:,.4f}</div>
                <div style="color:#6b7280; font-size:12px;">Qty: {ob['bids'][0][1]:.4f}</div>
            </div>
            <div class="metric-card" style="margin-top:8px;">
                <div class="metric-label">BEST ASK</div>
                <div style="color:#ef4444; font-family:'JetBrains Mono'; font-size:16px;">${ob['asks'][0][0]:,.4f}</div>
                <div style="color:#6b7280; font-size:12px;">Qty: {ob['asks'][0][1]:.4f}</div>
            </div>
            <div class="metric-card" style="margin-top:8px;">
                <div class="metric-label">SPREAD</div>
                <div style="color:#818cf8; font-family:'JetBrains Mono'; font-size:16px;">
                    ${ob['asks'][0][0] - ob['bids'][0][0]:.6f}
                </div>
            </div>
            """, unsafe_allow_html=True)
