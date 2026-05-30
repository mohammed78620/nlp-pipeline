import pytest

from nlp_pipeline.utils.process_input_function import (
    is_en,
    is_latin_by_codepoint,
    is_raw_html_empty,
    process_crawled_html,
    unicode_avg,
)


@pytest.mark.parametrize(
    "input, expected",
    [("this text is in english", True), ("este texto esta en ingles", False), ("", False), (None, False)],
)
def test_is_en(input, expected):
    assert is_en(input) == expected


def test_is_raw_html_empty():
    assert is_raw_html_empty("this text is in english") is False
    assert is_raw_html_empty("") is True
    assert is_raw_html_empty(None) is True


def test_is_not_latin_by_codepoint():
    assert is_latin_by_codepoint("this text is in english") is True
    assert is_latin_by_codepoint("هذا النص باللغة العربية") is False
    assert is_latin_by_codepoint("") is None


@pytest.mark.parametrize(
    "input, expected",
    [
        ("this text is in english", 109.15789473684211),
        ("este texto esta en ingles", 108.52380952380952),
        ("", None),
        (None, None),
    ],
)
def test_unicode_avg(input, expected):
    assert unicode_avg(input) == expected


def test_process_crawled_html1(raw_html):
    res = process_crawled_html(raw_html)
    assert res["pre_segmented_text"][0] == "this is a sentence"
    assert res["pre_segmented_text"][1] == "this is another sentence"
    assert res["pre_segmented_text"][2] == "this is a sentence with a link"


@pytest.mark.parametrize(
    "input, expected",
    [
        ("", None),
        (None, None),
    ],
)
def test_process_crawled_html2(input, expected):
    assert process_crawled_html(input) is expected


@pytest.fixture
def raw_html_2():
    return '<!--{"timestamp": 1615413290, "url": "https://www.circuitnet.com/2017/10/13/", "wbm_id": "scrapy_ae250ac2-1278-40cf-8077-409e7273c58c", "access_epoch": 1615413290, "scraper_type": "scrapy", "extra_header_info": "{\\"checksum\\":\\"437bbe7ceccb3067c4be0acf783a50df\\", \\"ipaddress\\":\\"54.219.186.54\\", \\"host\\":\\"crawler-tf11.versed.ai\\"}", "host_name": "circuitnet.com", "redirected_from": null, "date_guess": "None", "date_acc": "Accuracy.NONE"}-->\n<!DOCTYPE html><html><head><!-- head definitions go here --></head><body><p>this is a sentence</p></body></html>'


def test_process_crawled_html3(raw_html_2):
    article = process_crawled_html(raw_html_2)
    assert article["metadata"]["meta_year"] == 2017
    assert article["metadata"]["meta_date"] == "2017-10-13"


@pytest.fixture
def raw_html_3():
    return '<!--{"timestamp" 1615413290, "url": "https://www.circuitnet.com/", "wbm_id": "scrapy_ae250ac2-1278-40cf-8077-409e7273c58c", "access_epoch": 1615413290, "scraper_type": "scrapy", "extra_header_info": "{\\"checksum\\":\\"437bbe7ceccb3067c4be0acf783a50df\\", \\"ipaddress\\":\\"54.219.186.54\\", \\"host\\":\\"crawler-tf11.versed.ai\\"}", "host_name": "circuitnet.com", "redirected_from": null, "date_guess": "None", "date_acc": "Accuracy.NONE"}-->\n<!DOCTYPE html><html><head><!-- head definitions go here --></head><body><p>this is a sentence</p></body></html>'


def test_process_crawled_html4(raw_html_3):
    article = process_crawled_html(raw_html_3)
    assert article["metadata"]["metajson_extraction_error"] == "No ':' found when decoding object value"
