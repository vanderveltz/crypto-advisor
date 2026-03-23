# ⚡ CryptoAdvisor Pro

Profesjonalny doradca inwestycyjny do tradingu kryptowalut.
Zbudowany na Streamlit + Binance Public API.

---

## 🚀 Uruchomienie

```bash
# 1. Zainstaluj zależności
pip install -r requirements.txt

# 2. Uruchom aplikację
streamlit run app.py
```

Aplikacja otworzy się na `http://localhost:8501`

---

## 📦 Struktura projektu

```
crypto_advisor/
├── app.py                  # Główny plik Streamlit
├── requirements.txt
├── core/
│   ├── binance_client.py   # Pobieranie danych z Binance API
│   ├── indicators.py       # Silnik wskaźników technicznych
│   └── signals.py          # Generowanie sygnałów tradingowych
└── pages/
    ├── dashboard.py        # Strona główna — przegląd rynku
    ├── signals.py          # Sygnały + skaner rynku
    ├── analysis.py         # Wykresy techniczne
    └── settings.py         # Ustawienia i API keys
```

---

## 🎯 Funkcje

### Dashboard
- Aktualna cena wybranej pary z 24h statystykami
- Sygnał w czasie rzeczywistym dla wybranego timeframe'u
- Top gainers / losers 24h
- Watchlist 6 głównych par

### Sygnały
- Szczegółowy sygnał z entry, SL, TP1/TP2/TP3, R:R
- Analiza Multi-Timeframe (1m, 5m, 15m, 1h, 4h)
- Lista powodów i ostrzeżeń dla każdego sygnału
- **Skaner rynku** — skanuje wiele par jednocześnie

### Analiza Techniczna
- Interaktywny wykres świecowy (Plotly)
- Bollinger Bands, EMA 9/21/50, VWAP
- Panel RSI, MACD, Volume
- Order Book Depth z sentymentem

### Wskaźniki
- RSI (7, 14), MACD, Bollinger Bands
- Stochastic, Williams %R, CCI
- EMA (9, 21, 50, 200), SMA
- ATR, VWAP, OBV, Volume Ratio
- Wsparcia i Opory (automatyczna detekcja)

---

## 🔌 Binance API

**Dane publiczne (bez klucza):**
- Ceny, świece OHLCV, order book, ticker 24h

**Read-Only API Key (opcjonalny, dla portfela):**
1. Zaloguj się do Binance → Zarządzanie API
2. Utwórz klucz z uprawnieniem **TYLKO "Enable Reading"**
3. Wklej w aplikacji → Ustawienia → API Binance

---

## ⚠️ Disclaimer

Aplikacja jest narzędziem analitycznym i **nie stanowi doradztwa inwestycyjnego**.
Handel kryptowalutami wiąże się z ryzykiem utraty kapitału.
Inwestuj odpowiedzialnie.

---

## 🛠️ Deployment (SaaS)

Do sprzedaży na subskrypcję możesz wdrożyć na:
- **Streamlit Community Cloud** — darmowy hosting
- **Railway / Render** — prosty deploy z Dockerfile
- **VPS (DigitalOcean/Hetzner)** — pełna kontrola

Dodaj **autentykację użytkowników** używając:
- `streamlit-authenticator` (prosta)
- Auth0 / Supabase (zaawansowana, polecana dla SaaS)
