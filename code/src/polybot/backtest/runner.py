from decimal import Decimal
from pathlib import Path

import pandas as pd
from pydantic import BaseModel


class BacktestReport(BaseModel):
    trade_count: int
    win_rate: Decimal
    average_edge: Decimal
    realized_pnl: Decimal
    max_drawdown: Decimal
    max_exposure: Decimal
    rejected_signal_count: int


class BacktestRunner:
    def __init__(self, min_edge: Decimal, base_size: Decimal) -> None:
        self.min_edge = min_edge
        self.base_size = base_size

    def run_csv(self, path: str | Path) -> BacktestReport:
        frame = pd.read_csv(path, dtype=str)
        pnls: list[Decimal] = []
        edges: list[Decimal] = []
        rejected = 0
        equity = Decimal("0")
        peak = Decimal("0")
        max_drawdown = Decimal("0")
        max_exposure = Decimal("0")
        for row in frame.to_dict(orient="records"):
            ask = Decimal(row["best_ask"])
            fair = Decimal(row["fair_probability"])
            edge = fair - ask
            if edge < self.min_edge:
                rejected += 1
                continue
            resolved = Decimal(row["resolved_value"])
            pnl = (resolved - ask) * self.base_size
            pnls.append(pnl)
            edges.append(edge)
            equity += pnl
            peak = max(peak, equity)
            max_drawdown = max(max_drawdown, peak - equity)
            max_exposure = max(max_exposure, ask * self.base_size)
        wins = sum(1 for pnl in pnls if pnl > 0)
        trade_count = len(pnls)
        return BacktestReport(
            trade_count=trade_count,
            win_rate=Decimal(wins) / Decimal(trade_count) if trade_count else Decimal("0"),
            average_edge=sum(edges, Decimal("0")) / Decimal(trade_count)
            if trade_count
            else Decimal("0"),
            realized_pnl=sum(pnls, Decimal("0")),
            max_drawdown=max_drawdown,
            max_exposure=max_exposure,
            rejected_signal_count=rejected,
        )
