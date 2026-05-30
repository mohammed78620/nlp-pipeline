import pytest

from nlp_pipeline.utils.htmlutils import clean_html, find_meta_content, get_metajson, html_to_text, process


@pytest.mark.parametrize(
    "input, expected",
    [
        (
            '<!--{"timestamp": 1615413290, "url": "https://www.circuitnet.com/", "wbm_id": "scrapy_ae250ac2-1278-40cf-8077-409e7273c58c", "access_epoch": 1615413290, "scraper_type": "scrapy", "extra_header_info": "{\\"checksum\\":\\"437bbe7ceccb3067c4be0acf783a50df\\", \\"ipaddress\\":\\"54.219.186.54\\", \\"host\\":\\"crawler-tf11.versed.ai\\"}", "host_name": "circuitnet.com", "redirected_from": null, "date_guess": "None", "date_acc": "Accuracy.NONE"}-->',
            {
                "timestamp": 1615413290,
                "url": "https://www.circuitnet.com/",
                "wbm_id": "scrapy_ae250ac2-1278-40cf-8077-409e7273c58c",
                "access_epoch": 1615413290,
                "scraper_type": "scrapy",
                "extra_header_info": {
                    "checksum": "437bbe7ceccb3067c4be0acf783a50df",
                    "ipaddress": "54.219.186.54",
                    "host": "crawler-tf11.versed.ai",
                },
                "host_name": "circuitnet.com",
                "redirected_from": None,
                "date_guess": "None",
                "date_acc": "Accuracy.NONE",
            },
        ),
        (
            '<!--{"timestamp": 1615413290, "url": "https://www.circuitnet.com/", "wbm_id": "scrapy_ae250ac2-1278-40cf-8077-409e7273c58c", "access_epoch": 1615413290, "scraper_type": "scrapy", "extra_header_info": null, "host_name": "circuitnet.com", "redirected_from": null, "date_guess": "None", "date_acc": "Accuracy.NONE"}-->',
            {
                "timestamp": 1615413290,
                "url": "https://www.circuitnet.com/",
                "wbm_id": "scrapy_ae250ac2-1278-40cf-8077-409e7273c58c",
                "access_epoch": 1615413290,
                "scraper_type": "scrapy",
                "extra_header_info": None,
                "host_name": "circuitnet.com",
                "redirected_from": None,
                "date_guess": "None",
                "date_acc": "Accuracy.NONE",
            },
        ),
        (
            '<!--{"timestamp": 1615413290, "url": "https://www.circuitnet.com/", "wbm_id": "scrapy_ae250ac2-1278-40cf-8077-409e7273c58c", "access_epoch": 1615413290, "scraper_type": "scrapy", "extra_header_info": "a string that cant be loaded as a dict", "host_name": "circuitnet.com", "redirected_from": null, "date_guess": "None", "date_acc": "Accuracy.NONE"}-->',
            {
                "metajson_extraction_error": "Expected object or value",
            },
        ),
        (
            '<!--{"timestamp" 1615413290, "url": "https://www.circuitnet.com/", "wbm_id": "scrapy_ae250ac2-1278-40cf-8077-409e7273c58c", "access_epoch": 1615413290, "scraper_type": "scrapy", "extra_header_info": "{\\"checksum\\":\\"437bbe7ceccb3067c4be0acf783a50df\\", \\"ipaddress\\":\\"54.219.186.54\\", \\"host\\":\\"crawler-tf11.versed.ai\\"}", "host_name": "circuitnet.com", "redirected_from": null, "date_guess": "None", "date_acc": "Accuracy.NONE"}-->',
            {"metajson_extraction_error": "No ':' found when decoding object value"},
        ),
        ("", {"metajson_extraction_error": "first line in html is empty"}),
        (None, {"metajson_extraction_error": "first line in html is empty"}),
    ],
)
def test_get_metajson(input, expected):
    meta_json = get_metajson(input)
    assert meta_json == expected


def test_process(raw_html):
    meta_json, soup = process(raw_html)
    assert meta_json == meta_json
    assert soup is not None


def test_find_meta_content(raw_html):
    meta_json, soup = process(raw_html)
    metas = find_meta_content(soup, attrs={"name": "description"}, type="description")
    assert metas is not None


@pytest.mark.parametrize(
    "html, expected",
    [
        ("", "<html>\n <head>\n </head>\n <body>\n </body>\n</html>"),
        (
            "<body style='display: none'>Test no html tag</body>",
            '<html>\n <head>\n </head>\n <body style="display: none">\n  Test no html tag\n </body>\n</html>',
        ),
        (
            "<html><body style='display: none'>Test has html tag</body></html>",
            '<html>\n <head>\n </head>\n <body style="display: none">\n  Test has html tag\n </body>\n</html>',
        ),
        (
            "<?xml version='1.0' ?><html><body style='display: none'>Test has xml and html tags</body></html>",
            "<!--?xml version='1.0' ?-->\n<html>\n <head>\n </head>\n <body style=\"display: none\">\n  Test has xml and html tags\n </body>\n</html>",
        ),
        (
            "<html><body style='display: none'><ix:header>Things here.</ix:header>Test has xbrl and html tags</body></html>",
            '<html>\n <head>\n </head>\n <body style="display: none">\n  <ix:header>\n   Things here.\n  </ix:header>\n  Test has xbrl and html tags\n </body>\n</html>',
        ),
        (
            "<span style=\"color:#444867;font-family:'Calibri',sans-serif\">Contains sneaky unicode   whitespaces.</span>",
            "<html>\n <head>\n </head>\n <body>\n  <span style=\"color:#444867;font-family:'Calibri',sans-serif\">\n   Contains sneaky unicode whitespaces.\n  </span>\n </body>\n</html>",
        ),
        (
            "<html><body>AbbVie’s is using a unicode apostrophe. Should look like this AbbVie's</body></html>",
            "<html>\n <head>\n </head>\n <body>\n  AbbVie's is using a unicode apostrophe. Should look like this AbbVie's\n </body>\n</html>",
        ),
        ("á", "<html>\n <head>\n </head>\n <body>\n  á\n </body>\n</html>"),
    ],
)
def test_clean_html(html, expected):
    result = clean_html(html)

    assert result == expected


@pytest.mark.parametrize(
    "html, expected",
    [
        ("", ""),
        ("<body style='display: none'>test</body>", ""),
        ("<body style='display:none'>test</body>", ""),
        ("<body>test</body>", "test"),
        ("<body>test.<div>test</div></body>", "test.\ntest"),
        ("<body>test <span>test</span></body>", "test test"),
    ],
)
def test_html_to_text(html, expected):
    result = html_to_text(html)

    assert result == expected
