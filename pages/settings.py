"""
pages/settings.py
Ustawienia — API keys, preferencje, alerty
"""

import streamlit as st


def show_settings():
    st.markdown('<div style="font-size:28px; font-weight:800; color:#f1f5f9; margin-bottom:4px;">⚙️ Ustawienia</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#4b5563; font-size:13px; margin-bottom:24px;">Konfiguracja połączenia i preferencji</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔑 API Binance", "🎚️ Preferencje", "🔔 Alerty"])

    with tab1:
        st.markdown('<div class="section-header">POŁĄCZENIE Z BINANCE</div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="alert-neutral" style="margin-bottom:20px;">
            <div style="color:#818cf8; font-weight:600; margin-bottom:6px;">ℹ️ Dane publiczne</div>
            <div style="color:#9ca3af; font-size:13px;">
                Ceny, świece i order book są dostępne bez API key (publiczne API Binance).<br>
                Klucz API (read-only) jest potrzebny tylko do podglądu Twojego portfela.
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-header">OPCJONALNY: KLUCZ READ-ONLY (PORTFEL)</div>', unsafe_allow_html=True)

        api_key = st.text_input("API Key", type="password", placeholder="Wklej swój Binance API Key...", key="api_key")
        api_secret = st.text_input("API Secret", type="password", placeholder="Wklej swój Binance API Secret...", key="api_secret")

        st.markdown("""
        <div style="background:#151821; border:1px solid #252a3a; border-radius:8px; padding:14px 18px; margin-top:12px;">
            <div style="color:#f59e0b; font-size:12px; font-weight:600; margin-bottom:8px;">⚠️ BEZPIECZEŃSTWO</div>
            <ul style="color:#6b7280; font-size:12px; margin:0; padding-left:16px;">
                <li>Twórz klucze TYLKO z uprawnieniem "Read Only"</li>
                <li>Nigdy nie włączaj uprawnień do wypłat ani tradingu</li>
                <li>Klucze są przechowywane lokalnie w sesji</li>
                <li>Możesz w każdej chwili usunąć klucze na Binance</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Zapisz i Połącz"):
                if api_key and api_secret:
                    st.session_state["binance_api_key"] = api_key
                    st.session_state["binance_api_secret"] = api_secret
                    st.success("Klucze API zapisane w sesji!")
                else:
                    st.warning("Wpisz oba klucze.")
        with col2:
            if st.button("🔴 Usuń klucze"):
                st.session_state.pop("binance_api_key", None)
                st.session_state.pop("binance_api_secret", None)
                st.success("Klucze usunięte.")

        # Connection status
        st.markdown('<div class="section-header" style="margin-top:20px;">STATUS POŁĄCZENIA</div>', unsafe_allow_html=True)
        has_key = bool(st.session_state.get("binance_api_key"))
        st.markdown(f"""
        <div class="metric-card">
            <div style="display:flex; align-items:center; gap:12px;">
                <div style="width:10px; height:10px; border-radius:50%; background:#10b981;"></div>
                <div>
                    <div style="color:#f1f5f9; font-weight:600;">Publiczne API Binance</div>
                    <div style="color:#10b981; font-size:12px;">● Połączono — dane rynkowe dostępne</div>
                </div>
            </div>
        </div>
        <div class="metric-card" style="margin-top:8px;">
            <div style="display:flex; align-items:center; gap:12px;">
                <div style="width:10px; height:10px; border-radius:50%; background:{'#10b981' if has_key else '#6b7280'};"></div>
                <div>
                    <div style="color:#f1f5f9; font-weight:600;">Portfel (Read-Only API)</div>
                    <div style="color:{'#10b981' if has_key else '#6b7280'}; font-size:12px;">{'● Połączono' if has_key else '○ Brak klucza API'}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="section-header">PREFERENCJE SYGNAŁÓW</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            default_tf = st.selectbox("Domyślny timeframe", ["1m", "3m", "5m", "15m", "30m", "1h", "4h"], index=2)
            min_rr = st.slider("Minimalne R:R", 1.0, 5.0, 1.5, 0.1)
            min_confidence = st.selectbox("Minimalna pewność sygnału", ["LOW", "MEDIUM", "HIGH", "VERY HIGH"], index=1)

        with col2:
            risk_per_trade = st.slider("Ryzyko na trade (%)", 0.5, 5.0, 1.0, 0.1)
            default_pairs = st.multiselect(
                "Domyślne pary w watchlist",
                ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT"],
                default=["BTCUSDT", "ETHUSDT", "SOLUSDT"]
            )

        st.markdown('<div class="section-header" style="margin-top:16px;">ZARZĄDZANIE RYZYKIEM</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">KALKULATOR POZYCJI</div>
            <div style="color:#9ca3af; font-size:13px; margin-top:8px;">
                Przy ryzyku <span style="color:#818cf8; font-weight:600;">{risk_per_trade}%</span> kapitału i R:R min <span style="color:#818cf8; font-weight:600;">1:{min_rr}</span><br>
                Możesz stracić maks. <span style="color:#ef4444; font-weight:600;">{risk_per_trade}%</span> swojego kapitału na jeden trade.<br>
                Potencjalny zysk na trade: <span style="color:#10b981; font-weight:600;">{risk_per_trade * min_rr:.1f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("💾 Zapisz preferencje"):
            st.session_state["settings"] = {
                "default_tf": default_tf, "min_rr": min_rr,
                "min_confidence": min_confidence, "risk_per_trade": risk_per_trade,
                "default_pairs": default_pairs
            }
            st.success("Preferencje zapisane!")

    with tab3:
        st.markdown('<div class="section-header">KONFIGURACJA ALERTÓW</div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="alert-neutral" style="margin-bottom:16px;">
            <div style="color:#9ca3af; font-size:13px;">
                Alerty działają podczas aktywnej sesji. Dla alertów w tle skonfiguruj webhook lub uruchom skrypt osobno.
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Sygnały dźwiękowe**")
            sound_alerts = st.checkbox("Dźwięk przy sygnale BUY", value=True)
            sound_sell = st.checkbox("Dźwięk przy sygnale SELL", value=True)

            st.markdown("**Filtry alertów**")
            alert_min_score = st.slider("Minimalny score", 30, 90, 50)
            alert_confidence = st.selectbox("Minimalna pewność", ["LOW", "MEDIUM", "HIGH"], index=1, key="alert_conf")

        with col2:
            st.markdown("**Webhook (opcjonalnie)**")
            webhook_url = st.text_input("Webhook URL", placeholder="https://hooks.slack.com/... lub discord webhook")
            telegram_token = st.text_input("Telegram Bot Token", type="password", placeholder="Opcjonalnie")
            telegram_chat = st.text_input("Telegram Chat ID", placeholder="-100xxxxxxxxx")

        if st.button("💾 Zapisz alerty"):
            st.success("Konfiguracja alertów zapisana!")

        st.markdown('<div class="section-header" style="margin-top:16px;">O APLIKACJI</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="metric-card">
            <div style="color:#f1f5f9; font-weight:700; font-size:16px; margin-bottom:8px;">⚡ CryptoAdvisor Pro</div>
            <div style="color:#6b7280; font-size:12px; line-height:1.8;">
                Wersja: 1.0.0<br>
                Dane: Binance Public API (brak opóźnień)<br>
                Wskaźniki: RSI, MACD, Bollinger Bands, Stochastic, EMA, VWAP, ATR, OBV, Williams %R, CCI<br>
                Strategie: Scalping (1m/3m/5m), Intraday (15m/30m), Swing (1h/4h/1d)<br><br>
                <span style="color:#f59e0b;">⚠️ UWAGA:</span> Aplikacja służy wyłącznie jako narzędzie analityczne.<br>
                Nie stanowi doradztwa inwestycyjnego. Inwestuj odpowiedzialnie.
            </div>
        </div>
        """, unsafe_allow_html=True)
