"""Synthetic card-transaction generator.

Produces realistic-looking (but entirely fake) card transactions with:
  * a small share of labelled fraud with typical fraud patterns
    (bursts of transactions, high amounts, risky merchant categories, far from home)
  * one deliberately "hot" merchant that receives a large share of traffic,
    so you can reproduce and fix data skew in Spark.

Pure Python: no Spark needed, so it can be unit-tested locally.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta

MCC_NORMAL = ["5411", "5812", "5541", "5912", "5311", "4121", "5999"]   # grocery, restaurants, fuel...
MCC_RISKY = ["7995", "5967", "4829", "6051"]                         # gambling, direct marketing, money transfer, crypto
CITIES = ["Bengaluru", "Mumbai", "Delhi", "Chennai", "Hyderabad", "Pune", "Kolkata"]
FOREIGN_CITIES = ["Lagos", "Bucharest", "Manila", "Kyiv"]
HOT_MERCHANT = "M00001"   # receives ~40% of all transactions -> skew demo


def _card_ids(n_cards: int) -> list[str]:
    return [f"C{i:06d}" for i in range(1, n_cards + 1)]


def generate_transactions(
    n: int = 10_000,
    n_cards: int = 1_000,
    n_merchants: int = 500,
    fraud_rate: float = 0.02,
    hot_merchant_share: float = 0.40,
    start: datetime | None = None,
    seed: int = 42,
) -> list[dict]:
    """Return a list of transaction dicts. Same seed -> same data."""
    if not 0 <= fraud_rate < 1:
        raise ValueError("fraud_rate must be in [0, 1)")
    if not 0 <= hot_merchant_share < 1:
        raise ValueError("hot_merchant_share must be in [0, 1)")

    rng = random.Random(seed)
    start = start or datetime(2026, 1, 1)
    cards = _card_ids(n_cards)
    home_city = {c: rng.choice(CITIES) for c in cards}
    merchants = [f"M{i:05d}" for i in range(1, n_merchants + 1)]

    rows: list[dict] = []
    while len(rows) < n:
        card = rng.choice(cards)
        ts = start + timedelta(seconds=rng.randint(0, 30 * 24 * 3600))
        is_fraud = rng.random() < fraud_rate

        if is_fraud:
            # Fraud pattern: a burst of 2-5 high-value transactions within minutes,
            # risky merchant category, often far from home.
            burst = rng.randint(2, 5)
            city = rng.choice(FOREIGN_CITIES) if rng.random() < 0.6 else rng.choice(CITIES)
            for i in range(burst):
                if len(rows) >= n:
                    break
                rows.append(_row(rng, card, ts + timedelta(minutes=rng.randint(0, 10) + i),
                                 rng.choice(merchants), rng.choice(MCC_RISKY),
                                 round(rng.uniform(15_000, 150_000), 2), city, 1))
        else:
            merchant = HOT_MERCHANT if rng.random() < hot_merchant_share else rng.choice(merchants)
            rows.append(_row(rng, card, ts, merchant, rng.choice(MCC_NORMAL),
                             round(rng.lognormvariate(6.5, 1.0), 2), home_city[card], 0))
    return rows


def _row(rng, card, ts, merchant, mcc, amount, city, is_fraud) -> dict:
    return {
        "txn_id": str(uuid.UUID(int=rng.getrandbits(128))),
        "card_id": card,
        "merchant_id": merchant,
        "mcc": mcc,
        "amount": amount,
        "currency": "INR",
        "city": city,
        "channel": rng.choice(["POS", "ECOM", "ATM"]),
        "txn_time": ts.strftime("%Y-%m-%dT%H:%M:%S"),
        "is_fraud": is_fraud,
    }


def inject_bad_records(rows: list[dict], n_bad: int = 50, seed: int = 7) -> list[dict]:
    """Add records that the Silver data-quality rules should drop
    (negative amount, missing card, duplicate txn_id)."""
    rng = random.Random(seed)
    bad = []
    for i in range(n_bad):
        r = dict(rng.choice(rows))
        kind = i % 3
        if kind == 0:
            r["amount"] = -abs(r["amount"])
        elif kind == 1:
            r["card_id"] = None
        # kind == 2: exact duplicate (same txn_id) -> removed by de-duplication
        bad.append(r)
    return rows + bad
