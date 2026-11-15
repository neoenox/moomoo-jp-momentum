from __future__ import annotations

import sys
from pathlib import Path

import paper_order
import pytest

from src.paper_trade import PaperTradeManager


class _EnabledConfig:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.opend_host = "127.0.0.1"
        self.opend_port = 11111

    def get(self, key: str, default=None):
        if key == "paper_trade":
            return {"enabled": True, "allow_market_order": True}
        return default


def test_place_order_is_disabled_even_when_config_enables_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager = PaperTradeManager(_EnabledConfig(tmp_path / "paper.db"))

    def unexpected_trade_context(*args, **kwargs):
        pytest.fail("disabled OpenAPI order path must not create a trade context")

    monkeypatch.setattr(manager, "_get_trade_context", unexpected_trade_context)

    result = manager.place_order(
        code="US.AAPL",
        side="BUY",
        quantity=1,
        price=100.0,
        market="US",
    )

    assert result is None


def test_cancel_order_is_disabled_without_opening_trade_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager = PaperTradeManager(_EnabledConfig(tmp_path / "paper.db"))

    def unexpected_trade_context(*args, **kwargs):
        pytest.fail("disabled OpenAPI cancel path must not create a trade context")

    monkeypatch.setattr(manager, "_get_trade_context", unexpected_trade_context)

    assert manager.cancel_order("simulated-order-id", market="US") is False


def test_paper_order_cli_exits_before_loading_config_or_connecting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "paper_order.py",
            "--market",
            "US",
            "--experimental",
            "--code",
            "US.AAPL",
            "--side",
            "BUY",
            "--quantity",
            "1",
            "--price",
            "100",
        ],
    )

    assert paper_order.main() == 1
