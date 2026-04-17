from polybot.backtest.runner import BacktestReport


def render_backtest_report(report: BacktestReport) -> str:
    return "\n".join(
        [
            f"trade_count: {report.trade_count}",
            f"win_rate: {report.win_rate}",
            f"average_edge: {report.average_edge}",
            f"realized_pnl: {report.realized_pnl}",
            f"max_drawdown: {report.max_drawdown}",
            f"max_exposure: {report.max_exposure}",
            f"rejected_signal_count: {report.rejected_signal_count}",
        ]
    )
