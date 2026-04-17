import sqlite3
from decimal import Decimal
from pathlib import Path
from typing import Literal


class StateStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    market_id TEXT NOT NULL,
                    token_id TEXT NOT NULL,
                    side TEXT NOT NULL,
                    price TEXT NOT NULL,
                    size TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS fills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL,
                    market_id TEXT NOT NULL,
                    token_id TEXT NOT NULL,
                    side TEXT NOT NULL,
                    price TEXT NOT NULL,
                    size TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS positions (
                    market_id TEXT NOT NULL,
                    token_id TEXT NOT NULL,
                    size TEXT NOT NULL,
                    average_cost TEXT NOT NULL,
                    PRIMARY KEY (market_id, token_id)
                );
                CREATE TABLE IF NOT EXISTS strategy_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS risk_rejections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    market_id TEXT NOT NULL,
                    token_id TEXT NOT NULL,
                    reasons TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def record_order(
        self,
        order_id: str,
        market_id: str,
        token_id: str,
        side: Literal["BUY", "SELL"],
        price: Decimal,
        size: Decimal,
        status: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO orders
                (id, market_id, token_id, side, price, size, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (order_id, market_id, token_id, side, str(price), str(size), status),
            )

    def record_fill(
        self,
        order_id: str,
        market_id: str,
        token_id: str,
        side: Literal["BUY", "SELL"],
        price: Decimal,
        size: Decimal,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO fills (order_id, market_id, token_id, side, price, size)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (order_id, market_id, token_id, side, str(price), str(size)),
            )
            current = connection.execute(
                "SELECT size, average_cost FROM positions WHERE market_id = ? AND token_id = ?",
                (market_id, token_id),
            ).fetchone()
            signed_size = size if side == "BUY" else -size
            if current is None:
                new_size = signed_size
                average_cost = price
            else:
                old_size = Decimal(current["size"])
                old_cost = Decimal(current["average_cost"])
                new_size = old_size + signed_size
                if new_size == 0:
                    average_cost = Decimal("0")
                elif side == "BUY":
                    average_cost = ((old_size * old_cost) + (size * price)) / new_size
                else:
                    average_cost = old_cost
            connection.execute(
                """
                INSERT OR REPLACE INTO positions (market_id, token_id, size, average_cost)
                VALUES (?, ?, ?, ?)
                """,
                (market_id, token_id, str(new_size), str(average_cost)),
            )

    def get_position(self, market_id: str, token_id: str) -> dict[str, Decimal]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT size, average_cost FROM positions WHERE market_id = ? AND token_id = ?",
                (market_id, token_id),
            ).fetchone()
        if row is None:
            return {"size": Decimal("0"), "average_cost": Decimal("0")}
        return {"size": Decimal(row["size"]), "average_cost": Decimal(row["average_cost"])}
