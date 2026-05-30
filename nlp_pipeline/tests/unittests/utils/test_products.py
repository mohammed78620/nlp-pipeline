import pytest

from nlp_pipeline.utils.products import Products


@pytest.mark.parametrize(
    "data, expected",
    [
        ("", ""),
        ("pen", "PEN"),
        ("PEN", "PEN"),
        (" test whitespace stripping  ", "TEST WHITESPACE STRIPPING"),
    ],
)
def test_normalise_product(data, expected):
    result = Products.normalise_product(data)
    assert result == expected


@pytest.mark.parametrize(
    "data, expected",
    [
        (["pen", "crayon"], ["PEN", "CRAYON"]),
        ([""], [""]),
    ],
)
def test_normalise(data, expected):
    result = Products.normalise(data)
    assert result == expected


@pytest.mark.parametrize(
    "data, expected",
    [
        ("", None),
        ("pen", None),
        ("crayon", "crayon"),
        ("1 2 3 4 5 6 7 8 9 10", None),
        ("Pen [Holder]", None),
        ("Household\n Plant", None),
    ],
)
def test_filter_product(data, expected):
    result = Products.filter_product(data)

    if expected is None:
        assert result is expected
    else:
        assert result == expected


@pytest.mark.parametrize(
    "data, expected",
    [
        ([], []),
        ([""], []),
        (["pen", "example", "pen"], ["example"]),
        (["example", "example"], ["example"]),
    ],
)
def test_filter(data, expected):
    result = Products.filter(data)
    assert result == expected


@pytest.mark.parametrize(
    "data, expected",
    [
        ([], []),
        ([""], []),
        (["pen", "example", "pen"], ["EXAMPLE"]),
        (["", "THIS IS A test "], ["THIS IS A TEST"]),
        (["banana", "apple"], ["APPLE", "BANANA"]),
    ],
)
def test_process(data, expected):
    result = Products.process(data)
    assert result == expected
