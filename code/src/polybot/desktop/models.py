from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class DesktopReportConfig(BaseModel):
    timezone: str = "Asia/Shanghai"
    report_title: str = "美股收盘日报"
    symbols: list[str] = Field(default_factory=list)
    mail: dict[str, Any] = Field(default_factory=dict)
    indicators: dict[str, Any] = Field(default_factory=dict)


class SymbolValidationResult(BaseModel):
    symbol: str
    last_close: Decimal | None = None
    last_close_date: str | None = None
    error: str | None = None


class SaveSymbolsResult(BaseModel):
    saved: bool
    symbols: list[str] = Field(default_factory=list)
    validations: list[SymbolValidationResult] = Field(default_factory=list)
    message: str


class ActionResult(BaseModel):
    ok: bool
    message: str
    details: list[str] = Field(default_factory=list)
