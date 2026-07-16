from backend.agents.analyst_node import run_analyst
from backend.schemas import AnalystLLMOutput, ReviewExample

FORBIDDEN_WORDS = ["comprar", "vender", "buy", "sell", "compra ahora", "venta inmediata"]

NEWS = {
    "id": "n999",
    "headline": "Test company reports strong earnings beat",
    "summary": "Revenue and margins both exceeded consensus estimates.",
    "source": "Test Wire",
    "published_at": "2026-07-10T10:00:00Z",
    "instruments": ["TST"],
    "sector": "Technology",
    "topic": "Earnings",
}


def _price_comparison(change_pct: float) -> dict:
    return {
        "instrument": "TST",
        "change_pct": change_pct,
        "window_days": 2,
        "note": f"TST movio {change_pct}% en la ventana.",
    }


def test_positive_price_move_yields_positive_impact():
    signal = run_analyst(NEWS, _price_comparison(6.5))
    assert signal["impact"] == "positive"
    assert 0.0 <= signal["confidence"] <= 1.0


def test_negative_price_move_yields_negative_impact():
    signal = run_analyst(NEWS, _price_comparison(-7.2))
    assert signal["impact"] == "negative"


def test_flat_price_move_yields_neutral_impact():
    signal = run_analyst(NEWS, _price_comparison(0.1))
    assert signal["impact"] == "neutral"


def test_signal_never_suggests_trade_execution():
    signal = run_analyst(NEWS, _price_comparison(5.0))
    action = signal["suggested_action"].lower()
    for word in FORBIDDEN_WORDS:
        assert word not in action, f"suggested_action no debe sugerir '{word}': {action}"


def test_signal_includes_disclaimer_and_sources():
    signal = run_analyst(NEWS, _price_comparison(3.0))
    assert signal["disclaimer"]
    assert signal["sources"] == ["Test Wire"]
    assert len(signal["evidence"]) >= 2


class _CapturingLLM:
    """Captura el user_prompt recibido para inspeccionar el bloque de feedback."""

    def __init__(self):
        self.last_user_prompt = None

    def generate_structured(self, system_prompt, user_prompt, schema):
        self.last_user_prompt = user_prompt
        return AnalystLLMOutput(
            impact="neutral",
            confidence=0.6,
            evidence=["Evidencia de prueba.", "Segunda evidencia."],
            reasoning="Razonamiento de prueba.",
            suggested_action="Monitorear el instrumento antes de cualquier decision.",
        )


def test_review_examples_are_injected_as_feedback_block():
    fake = _CapturingLLM()
    review_examples = [
        ReviewExample(
            instrument="TST",
            impact="positive",
            confidence=0.8,
            evidence=["Evidencia previa."],
            review_status="descartada",
            review_justification="El Comite considero que era ruido de corto plazo.",
        )
    ]

    run_analyst(NEWS, _price_comparison(1.0), llm=fake, review_examples=review_examples)

    assert "Retroalimentacion del Comite" in fake.last_user_prompt
    assert "ruido de corto plazo" in fake.last_user_prompt


def test_no_feedback_block_without_review_examples():
    fake = _CapturingLLM()

    run_analyst(NEWS, _price_comparison(1.0), llm=fake, review_examples=None)

    assert "Retroalimentacion del Comite" not in fake.last_user_prompt
