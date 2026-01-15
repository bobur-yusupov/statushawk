from datetime import datetime, timezone


def generate_timestamp_iso() -> str:
    now = datetime.now(timezone.utc)
    return now.isoformat()
