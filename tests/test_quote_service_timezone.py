from datetime import datetime, timezone

from src.market_calendar import JST
from src.quote_service import _jpx_trading_clock


def test_jpx_trading_clock_normalizes_utc_host_time_to_jst() -> None:
    now, active = _jpx_trading_clock(datetime(2026, 9, 25, 6, 0, tzinfo=timezone.utc))

    assert now.tzinfo == JST
    assert (now.hour, now.minute) == (15, 0)
    assert active is True


def test_jpx_trading_clock_stops_at_1530_jst() -> None:
    now, active = _jpx_trading_clock(datetime(2026, 9, 25, 6, 30, tzinfo=timezone.utc))

    assert (now.hour, now.minute) == (15, 30)
    assert active is False


def test_jpx_trading_clock_uses_jst_date_across_utc_boundary() -> None:
    now, _ = _jpx_trading_clock(datetime(2026, 9, 25, 15, 5, tzinfo=timezone.utc))

    assert now.strftime("%Y-%m-%d %H:%M") == "2026-09-26 00:05"
