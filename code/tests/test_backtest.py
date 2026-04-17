from decimal import Decimal

import pandas as pd

from polybot.backtest.runner import BacktestRunner


def test_backtest_reports_deterministic_metrics(tmp_path):
    data = pd.DataFrame(
        [
            {
                "timestamp": "2026-01-01T00:00:00Z",
                "market_id": "m1",
                "token_id": "t1",
                "best_bid": "0.49",
                "best_ask": "0.50",
                "midpoint": "0.495",
                "fair_probability": "0.60",
                "resolved_value": "1",
            },
            {
                "timestamp": "2026-01-01T01:00:00Z",
                "market_id": "m2",
                "token_id": "t2",
                "best_bid": "0.70",
                "best_ask": "0.71",
                "midpoint": "0.705",
                "fair_probability": "0.72",
                "resolved_value": "0",
            },
        ]
    )
    path = tmp_path / "history.csv"
    data.to_csv(path, index=False)

    report = BacktestRunner(min_edge=Decimal("0.05"), base_size=Decimal("10")).run_csv(path)

    assert report.trade_count == 1
    assert report.realized_pnl == Decimal("5.00")
    assert report.rejected_signal_count == 1
