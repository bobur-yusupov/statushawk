import pytest


@pytest.fixture
def input_value() -> int:
    input = 36
    return input


def test_divisible_by_3(input_value: int) -> None:
    assert input_value % 3 == 0

def test_divisible_by_6(input_value: int) -> None:
    assert input_value % 6 == 0
