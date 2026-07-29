from datetime import UTC, datetime, timedelta

from app.schemas.common import GlobalFilters


def resolve_date_range(filters: GlobalFilters) -> tuple[datetime | None, datetime | None]:
    """Map frontend date_preset / custom range to UTC bounds for SQL filtering."""
    now = datetime.now(UTC)
    if filters.custom_date_from and filters.custom_date_to:
        start = _parse_date(filters.custom_date_from)
        end = _parse_date(filters.custom_date_to, end_of_day=True)
        if start and end:
            return start, end

    preset = (filters.date_preset or "7d").lower()
    if preset in ("all", "lifetime"):
        return None, None

    days_map = {"1d": 1, "7d": 7, "14d": 14, "30d": 30, "90d": 90, "180d": 180, "365d": 365}
    days = days_map.get(preset)
    if days is None and preset.endswith("d"):
        try:
            days = int(preset[:-1])
        except ValueError:
            days = 7
    if days is None:
        days = 7
    return now - timedelta(days=days), now


def _parse_date(value: str, end_of_day: bool = False) -> datetime | None:
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            dt = datetime.strptime(value.replace("Z", ""), fmt.replace("Z", ""))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            if end_of_day and fmt == "%Y-%m-%d":
                dt = dt.replace(hour=23, minute=59, second=59)
            return dt
        except ValueError:
            continue
    return None
