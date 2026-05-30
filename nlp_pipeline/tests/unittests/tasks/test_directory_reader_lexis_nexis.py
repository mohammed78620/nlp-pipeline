import pytest

from nlp_pipeline.tasks.directory_reader_lexis_nexis import DirectoryReaderLexisNexis


@pytest.fixture
def exclude_list():
    return ["Finance", "Media", "Society"]


@pytest.mark.parametrize(
    "input, expected",
    [
        (None, False),
        ([], False),
        (
            [
                {"name": "Consumer durables news", "group": "Industry"},
                {"name": "Retail industry news", "group": "Industry"},
            ],
            False,
        ),
        ([{"group": "Finance", "name": "Stock Exchanges news"}], True),
        (
            [
                {"group": "Finance", "name": "Stock Exchanges news"},
                {"name": "Retail industry news", "group": "Industry"},
            ],
            True,
        ),
    ],
)
def test_has_excluded_topic(
    exclude_list,
    input,
    expected,
):
    output = DirectoryReaderLexisNexis().has_excluded_topic(input, exclude_list)
    assert output == expected
