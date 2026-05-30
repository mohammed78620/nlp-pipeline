import pytest

from nlp_pipeline.tasks.acronym_resolver import AcronymResolver


@pytest.fixture
def edgar_article_batch_1(basic_article):
    basic_article["text"] = "Amazon Web Services (AWS) are planning to build a data center in the UK."
    batch = {"batch_id": "1", "articles": [basic_article]}
    return batch


@pytest.mark.parametrize(
    "input, expected",
    [
        ("edgar_article_batch_1", "Amazon Web Services are planning to build a data center in the UK."),
    ],
)
def test_acronym_resolver(input, expected, request):
    batch = request.getfixturevalue(input)
    result = AcronymResolver().run(batch)

    assert result["articles"][-1]["text"] == expected
