from datetime import datetime, timezone

from src.market_calendar import JST


def test_jst_conversion_is_host_timezone_independent() -> None:
    during_market_utc = datetime(2026, 9, 25, 6, 0, tzinfo=timezone.utc)
    after_market_utc = datetime(2026, 9, 25, 6, 30, tzinfo=timezone.utc)

    during_market = during_market_utc.astimezone(JST)
    after_market = after_market_utc.astimezone(JST)

    assert during_market.hour == 15
    assert during_market.minute == 0
    assert after_market.hour == 15
    assert after_market.minute == 30
