"""
core/ai_advisor.py
Integracja z Claude AI — analiza sygnałów tradingowych
"""

import os
import streamlit as st
import anthropic
from core.signals import TradingSignal

try:
    from langfuse import get_client as _langfuse_get_client
    _LANGFUSE_AVAILABLE = True
except ImportError:
    _LANGFUSE_AVAILABLE = False


def _get_langfuse():
    if not _LANGFUSE_AVAILABLE:
        return None
    try:
        # v3 czyta LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_HOST z env
        # Obsługujemy też LANGFUSE_BASE_URL jako alias dla LANGFUSE_HOST
        if not os.environ.get("LANGFUSE_HOST") and os.environ.get("LANGFUSE_BASE_URL"):
            os.environ["LANGFUSE_HOST"] = os.environ["LANGFUSE_BASE_URL"]
        return _langfuse_get_client()
    except Exception:
        return None


def get_anthropic_client() -> anthropic.Anthropic | None:
    """Pobiera klienta Anthropic: session_state → st.secrets → brak."""
    api_key = st.session_state.get("anthropic_api_key")
    if not api_key:
        try:
            api_key = st.secrets.get("ANTHROPIC_API_KEY")
        except Exception:
            api_key = None
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)


def _build_context(symbol: str, timeframe: str, signal: TradingSignal,
                   indicators: dict, mtf_signals: dict) -> str:
    reasons_text = "\n".join(f"  - {r}" for r in signal.reasons) or "  Brak"
    warnings_text = "\n".join(f"  - {w}" for w in signal.warnings) or "  Brak"
    mtf_text = "".join(f"  {tf}: {s.action} (Score: {s.score:+d})\n" for tf, s in mtf_signals.items())

    ind_lines = []
    for k, v in indicators.items():
        if v is not None and v == v:  # skip NaN
            ind_lines.append(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")
    indicators_text = "\n".join(ind_lines[:15])

    return f"""Para: {symbol} | Timeframe: {timeframe} | Strategia: {signal.strategy}

SYGNAŁ ALGORYTMICZNY:
  Akcja: {signal.action} | Score: {signal.score:+d}/100 | Pewność: {signal.confidence}
  Entry: ${signal.entry_price:,.4f}
  Stop Loss: ${signal.stop_loss:,.4f}
  TP1: ${signal.take_profit_1:,.4f} | TP2: ${signal.take_profit_2:,.4f} | TP3: ${signal.take_profit_3:,.4f}
  Risk:Reward: 1:{signal.risk_reward:.1f}

POWODY SYGNAŁU:
{reasons_text}

OSTRZEŻENIA:
{warnings_text}

ANALIZA MULTI-TIMEFRAME:
{mtf_text}
KLUCZOWE WSKAŹNIKI:
{indicators_text}"""


def analyze_with_claude(symbol: str, timeframe: str, signal: TradingSignal,
                        indicators: dict, mtf_signals: dict) -> bool:
    """
    Streamuje analizę Claude AI bezpośrednio do widżetu Streamlit.
    Loguje trace do Langfuse jeśli skonfigurowany.
    Zwraca True jeśli sukces, False jeśli brak klucza lub błąd.
    """
    client = get_anthropic_client()
    if not client:
        st.warning("Brak klucza API Anthropic. Dodaj go w ⚙️ Ustawienia → Claude AI.")
        return False

    context = _build_context(symbol, timeframe, signal, indicators, mtf_signals)

    system_prompt = """Jesteś doświadczonym analitykiem rynku kryptowalut i traderem z 10-letnim stażem.
Analizujesz dane techniczne i sygnały tradingowe, dając przemyślane, konkretne porady.
Twoje odpowiedzi są zwięzłe (max 300 słów), praktyczne i po polsku.
WAŻNE: Twoja analiza to wsparcie edukacyjne, nie doradztwo inwestycyjne."""

    user_message = f"""Przeanalizuj poniższy sygnał tradingowy i oceń jego jakość:

{context}

Odpowiedz w 4 punktach:
1. **Siła sygnału** — czy wskaźniki są spójne i przekonujące?
2. **Analiza MTF** — czy wyższe timeframe'y potwierdzają kierunek?
3. **Kluczowe ryzyka** — co może unieważnić ten sygnał?
4. **Rekomendacja** — wejść teraz / poczekać na potwierdzenie / unikać (i dlaczego)"""

    messages = [{"role": "user", "content": user_message}]
    placeholder = st.empty()
    langfuse = _get_langfuse()

    placeholder.markdown(
        '<div class="alert-neutral" style="border-left-color:#818cf8;">'
        '<div style="color:#818cf8;font-size:11px;font-weight:700;margin-bottom:8px;letter-spacing:1px;">🤖 ANALIZA CLAUDE AI</div>'
        '<div style="color:#d1d5db;font-size:13px;">⏳ Analizuję sygnał...</div>'
        '</div>',
        unsafe_allow_html=True
    )

    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=600,
            system=system_prompt,
            messages=messages
        )

        full_text = response.content[0].text

        placeholder.markdown(
            f'<div class="alert-neutral" style="border-left-color:#818cf8;">'
            f'<div style="color:#818cf8;font-size:11px;font-weight:700;margin-bottom:8px;letter-spacing:1px;">🤖 ANALIZA CLAUDE AI</div>'
            f'<div style="color:#d1d5db;font-size:13px;line-height:1.7;">{full_text}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        if langfuse:
            try:
                usage = response.usage
                with langfuse.start_as_current_span(name="crypto-signal-analysis"):
                    langfuse.update_current_observation(
                        input={"symbol": symbol, "timeframe": timeframe,
                               "signal": signal.action, "context": context},
                        output=full_text,
                        model="claude-opus-4-6",
                        usage={"input": usage.input_tokens, "output": usage.output_tokens},
                        metadata={"score": signal.score, "confidence": signal.confidence},
                    )
                langfuse.flush()
            except Exception:
                pass

        return True

    except anthropic.AuthenticationError:
        st.error("Nieprawidłowy klucz API Anthropic. Sprawdź ustawienia.")
    except anthropic.RateLimitError:
        st.error("Przekroczono limit zapytań API. Spróbuj za chwilę.")
    except Exception as e:
        st.error(f"Błąd Claude API: {e}")

    return False
