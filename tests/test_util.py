import pytest

from secrets_management.util import bool_converter


TRUTHY_VALUES = [True, 1, "y", "Y", "yes", "YES", "t", "T", "true", "TRUE", "1", "on", "ON"]
FALSY_VALUES = [False, 0, "n", "N", "no", "NO", "f", "F", "false", "FALSE", "0", "off", "OFF"]


class TestBoolConverter:
    @pytest.mark.parametrize("value", TRUTHY_VALUES)
    def test_truthy_values_return_true(self, value):
        assert bool_converter(value) is True

    @pytest.mark.parametrize("value", FALSY_VALUES)
    def test_falsy_values_return_false(self, value):
        assert bool_converter(value) is False

    @pytest.mark.parametrize("value", ["maybe", "2", "yep", "nope", "", "tru", "fals"])
    def test_invalid_values_raise_value_error(self, value):
        with pytest.raises(ValueError):
            bool_converter(value)
