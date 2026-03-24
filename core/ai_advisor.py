"""
core/ai_advisor.py
Integracja z Claude AI — analiza sygnałów tradingowych
"""

import os
import streamlit as st
import anthropic
from langfuse import Langfuse
from core.signals import TradingSignal


def _get_langfuse() -> Langfuse | None:
    """Inicjalizuje klienta Langfuse z env vars lub st.secrets."""
    try:
        secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
        public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
        host = os.environ.get("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")

        if not secret_key or not public_key:
            try:
                secret_key = st.secrets.get("LANGFUSE_SECRET_KEY")
                public_key = st.secrets.get("LANGFUSE_PUBLIC_KEY")
                host = st.secrets.get("LANGFUSE_BASE_URL", host)
            except Exception:
                pass

        if not secret_key or not public_key:
            return None

        return Langfuse(secret_key=secret_key, public_key=public_key, host=host)
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
    full_text = ""

    langfuse = _get_langfuse()
    trace = langfuse.trace(
        name="crypto-signal-analysis",
        metadata={"symbol": symbol, "timeframe": timeframe, "signal": signal.action}
    ) if langfuse else None

    generation = trace.generation(
        name="claude-analysis",
        model="claude-opus-4-6",
        input=messages,
        system=system_prompt,
    ) if trace else None

    try:
        with client.messages.stream(
            model="claude-opus-4-6",
            max_tokens=600,
            thinking={"type": "adaptive"},
            system=system_prompt,
            messages=messages
        ) as stream:
            for chunk in stream.text_stream:
                full_text += chunk
                placeholder.markdown(
                    f'<div class="alert-neutral" style="border-left-color:#818cf8;">'
                    f'<div style="color:#818cf8;font-size:11px;font-weight:700;margin-bottom:8px;letter-spacing:1px;">🤖 ANALIZA CLAUDE AI</div>'
                    f'<div style="color:#d1d5db;font-size:13px;line-height:1.7;">{full_text}▌</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            final_message = stream.get_final_message()

        # Końcowy render bez kursora
        placeholder.markdown(
            f'<div class="alert-neutral" style="border-left-color:#818cf8;">'
            f'<div style="color:#818cf8;font-size:11px;font-weight:700;margin-bottom:8px;letter-spacing:1px;">🤖 ANALIZA CLAUDE AI</div>'
            f'<div style="color:#d1d5db;font-size:13px;line-height:1.7;">{full_text}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        if generation:
            usage = final_message.usage
            generation.end(
                output=full_text,
                usage={
                    "input": usage.input_tokens,
                    "output": usage.output_tokens,
                },
            )
            langfuse.flush()

        return True

    except anthropic.AuthenticationError:
        st.error("Nieprawidłowy klucz API Anthropic. Sprawdź ustawienia.")
    except anthropic.RateLimitError:
        st.error("Przekroczono limit zapytań API. Spróbuj za chwilę.")
    except Exception as e:
        st.error(f"Błąd Claude API: {e}")

    if generation:
        generation.end(output=None)
        langfuse.flush()

    return False
