import pytest


@pytest.fixture
def input_value() -> int:
    input = 39
    return input


def test_divisible_by_3(input_value: int) -> None:
    assert input_value % 3 == 0
