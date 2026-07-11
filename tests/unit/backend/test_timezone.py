"""
时区工具单元测试
--------------------------------------------------------------------------
覆盖上海时区常量、now_shanghai、today_shanghai
"""
from datetime import datetime, timezone, timedelta

import pytest

from app.utils.timezone import SHANGHAI_TZ, now_shanghai, today_shanghai


class TestTimezone:
    """时区工具"""

    @pytest.mark.unit
    def test_shanghai_tz_is_utc_plus_8(self):
        assert SHANGHAI_TZ == timezone(timedelta(hours=8))

    @pytest.mark.unit
    def test_now_shanghai_returns_naive_datetime(self):
        result = now_shanghai()
        assert isinstance(result, datetime)
        assert result.tzinfo is None

    @pytest.mark.unit
    def test_now_shanghai_close_to_utc_plus_8(self):
        # now_shanghai 应比 UTC 时间快 8 小时左右
        result = now_shanghai()
        utc_now = datetime.utcnow()
        diff = result - utc_now
        # 允许几秒误差
        assert timedelta(hours=7, minutes=59) < diff < timedelta(hours=8, minutes=1)

    @pytest.mark.unit
    def test_today_shanghai_returns_date(self):
        result = today_shanghai()
        assert result == now_shanghai().date()

    @pytest.mark.unit
    def test_today_shanghai_is_today(self):
        result = today_shanghai()
        utc_today = datetime.utcnow().date()
        # 上海日期应该等于或晚一天于 UTC 日期（取决于当前时间）
        assert result == utc_today or result == utc_today + timedelta(days=1)
