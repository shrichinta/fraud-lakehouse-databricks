import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fraud_lib.synthetic_data import (  # noqa: E402
    HOT_MERCHANT,
    generate_transactions,
    inject_bad_records,
)


def test_row_count_and_schema():
    rows = generate_transactions(n=2_000, seed=1)
    assert len(rows) == 2_000
    expected = {"txn_id", "card_id", "merchant_id", "mcc", "amount", "currency",
                "city", "channel", "txn_time", "is_fraud"}
    assert set(rows[0]) == expected


def test_same_seed_is_reproducible():
    assert generate_transactions(n=500, seed=3) == generate_transactions(n=500, seed=3)


def test_fraud_rate_is_roughly_as_configured():
    rows = generate_transactions(n=20_000, fraud_rate=0.02, seed=5)
    share = sum(r["is_fraud"] for r in rows) / len(rows)
    # fraud arrives in bursts of 2-5, so labelled share is higher than the trigger rate
    assert 0.03 < share < 0.10


def test_hot_merchant_creates_skew():
    rows = generate_transactions(n=20_000, hot_merchant_share=0.4, seed=9)
    share = sum(r["merchant_id"] == HOT_MERCHANT for r in rows) / len(rows)
    assert share > 0.30


def test_txn_ids_unique():
    rows = generate_transactions(n=5_000, seed=11)
    assert len({r["txn_id"] for r in rows}) == len(rows)


def test_bad_records_are_injected():
    rows = generate_transactions(n=1_000, seed=2)
    out = inject_bad_records(rows, n_bad=30)
    assert len(out) == 1_030
    assert any(r["amount"] < 0 for r in out)
    assert any(r["card_id"] is None for r in out)


@pytest.mark.parametrize("bad", [-0.1, 1.0])
def test_invalid_fraud_rate_raises(bad):
    with pytest.raises(ValueError):
        generate_transactions(n=10, fraud_rate=bad)
