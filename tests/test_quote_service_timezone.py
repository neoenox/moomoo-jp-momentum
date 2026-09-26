from datetime import datetime, timezone

from src.market_calendar import JST
from src.quote_service import _is_jpx_cash_trading_hours, _jpx_now


def test_jpx_now_converts_utc_reference_to_jst():
    reference = datetime(2026, 9, 25, 6, 0, tzinfo=timezone.utc)

    result = _jpx_now(reference)

    assert result.tzinfo == JST
    assert result.strftime("%Y-%m-%d %H:%M") == "2026-09-25 15:00"


def test_jpx_trading_hours_are_evaluated_in_jst_from_utc():
    assert _is_jpx_cash_trading_hours(
        datetime(2026, 9, 25, 0, 0, tzinfo=timezone.utc)
    )
    assert _is_jpx_cash_trading_hours(
        datetime(2026, 9, 25, 6, 29, tzinfo=timezone.utc)
    )
    assert not _is_jpx_cash_trading_hours(
        datetime(2026, 9, 25, 6, 30, tzinfo=timezone.utc)
    )


def test_jpx_now_treats_naive_reference_as_jst():
    reference = datetime(2026, 9, 25, 9, 0)

    result = _jpx_now(reference)

    assert result.tzinfo == JST
    assert result.hour == 9
