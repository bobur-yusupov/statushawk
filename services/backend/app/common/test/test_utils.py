from datetime import datetime
from common.utils import generate_timestamp_iso


class TestCommonUtils:
    def test_generate_timestamp_iso(self) -> None:
        timestamp = generate_timestamp_iso()
        assert isinstance(timestamp, str)
        assert "T" in timestamp
        parsed = datetime.fromisoformat(timestamp)
        assert parsed.tzinfo is not None

    def test_generate_timestamp_iso_format(self) -> None:
        timestamp = generate_timestamp_iso()
        assert timestamp.endswith("+00:00") or timestamp.endswith("Z")

    def test_generate_timestamp_iso_unique(self) -> None:
        ts1 = generate_timestamp_iso()
        ts2 = generate_timestamp_iso()
        assert ts1 <= ts2
