import pytest

from nlp_pipeline.utils.common import remove_urls


@pytest.mark.parametrize(
    "input, expected",
    [
        ("", ""),
        ("this text contains a url https://website.com", "this text contains a url"),
        ("this text contains a url http://website.com", "this text contains a url"),
        ("this text contains urls http://website.com, https://website.com", "this text contains urls"),
        ("this text contains a url www.website.com", "this text contains a url"),
        ("this text does not contain a url", "this text does not contain a url"),
    ],
)
def test_remove_urls(input, expected):
    assert remove_urls(input) == expected
