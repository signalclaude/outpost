"""Tests for outpost date parsing utilities."""

from datetime import date, datetime, time

import pytest

from outpost.utils.dates import (
    parse_natural_date,
    parse_natural_datetime,
    parse_time_string,
    to_graph_date,
    to_graph_datetime,
    today_range,
)


class TestParseNaturalDate:
    def test_iso_date(self):
        result = parse_natural_date("2026-03-15")
        assert result == date(2026, 3, 15)

    def test_tomorrow(self):
        result = parse_natural_date("tomorrow")
        today = date.today()
        assert result > today

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Could not parse date"):
            parse_natural_date("xyzzy nonsense gibberish")


class TestParseNaturalDatetime:
    def test_iso_datetime(self):
        result = parse_natural_datetime("2026-03-15T09:00:00")
        assert result == datetime(2026, 3, 15, 9, 0, 0)

    def test_natural_language(self):
        result = parse_natural_datetime("tomorrow 9am")
        assert isinstance(result, datetime)
        assert result > datetime.now()

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Could not parse datetime"):
            parse_natural_datetime("xyzzy nonsense gibberish")


class TestParseTimeString:
    def test_24h_format(self):
        result = parse_time_string("14:00")
        assert result.hour == 14
        assert result.minute == 0

    def test_12h_format(self):
        result = parse_time_string("9am")
        assert result.hour == 9

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Could not parse time"):
            parse_time_string("xyzzy nonsense gibberish")


class TestGraphFormatters:
    def test_to_graph_datetime(self):
        dt = datetime(2026, 3, 15, 9, 30, 0)
        result = to_graph_datetime(dt)
        assert result["dateTime"] == "2026-03-15T09:30:00"
        assert result["timeZone"] == "UTC"

    def test_to_graph_date(self):
        d = date(2026, 3, 15)
        assert to_graph_date(d) == "2026-03-15"


class TestTodayRange:
    def test_returns_start_end(self):
        start, end = today_range()
        assert start.hour == 0 and start.minute == 0 and start.second == 0
        assert end.date() > start.date() or (end - start).total_seconds() == 86400
        assert start.date() == date.today()
