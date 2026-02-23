import pytest
from agent.tools import calculator


def test_calculator_basic_arithmetic():
    assert calculator.invoke({"expression": "2 + 2"}) == "4"


def test_calculator_power():
    assert calculator.invoke({"expression": "2 ** 10"}) == "1024"


def test_calculator_sqrt():
    assert calculator.invoke({"expression": "sqrt(16)"}) == "4.0"


def test_calculator_blocks_import():
    with pytest.raises(Exception):
        calculator.invoke({"expression": "__import__('os').getcwd()"})
