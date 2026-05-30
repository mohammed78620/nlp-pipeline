import pytest

from nlp_pipeline.lib.common.text import contains_mostly_numbers


class TestContainsMostlyNumbers:
    @pytest.mark.parametrize(
        "test_input, expected",
        [
            ("Between the 12/05/2022 and 25/06/2022", True),
            ("Samsung reports 2.2 billion revenue in Q4, a 22% more than last quarter", False),
            ("Apple will be announcing their new in-house chip next week, reportedly", False),
        ],
    )
    def test_pass(self, test_input, expected):
        assert contains_mostly_numbers(test_input) == expected

    def test_raises_type_error(self):
        with pytest.raises(TypeError):
            contains_mostly_numbers(1)

    def test_raises_value_error(self):
        with pytest.raises(ValueError):
            contains_mostly_numbers("")
