from src.data import load_history
from src.strategy import generate_signals


def test_generate_signals_runs():
    # Smoke test to ensure pipeline executes on small sample
    df = load_history(["TQQQ", "SQQQ"], period="1y")
    sig = generate_signals(df)
    assert sig.index.equals(df.index)
