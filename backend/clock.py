from datetime import datetime, timezone, timedelta


def today():
    # Windows does not require tzdata for fixed CST; China has no DST.
    return datetime.now(timezone(timedelta(hours=8))).date()
