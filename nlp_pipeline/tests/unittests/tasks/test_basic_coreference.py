import pytest

from nlp_pipeline.tasks.basic_coreference import BasicCoreference


@pytest.fixture
def edgar_article_batch_1(basic_article):
    basic_article["text"] = "We are a company that makes things."
    basic_article["metadata"] = {"extra_edgar_info": {"query_result": {"companyName": "Intel Inc."}}}
    batch = {"batch_id": "1", "articles": [basic_article]}
    return batch


@pytest.fixture
def edgar_article_batch_2(basic_article):
    basic_article["text"] = "American Express' credit cards are ok. We do banking things."
    basic_article["metadata"] = {"extra_edgar_info": {"query_result": {"companyName": "American Express"}}}
    batch = {"batch_id": "1", "articles": [basic_article]}
    return batch


@pytest.fixture
def edgar_article_batch_3(basic_article):
    basic_article["text"] = "Google's search engine is famous. We search things."
    basic_article["metadata"] = {"extra_edgar_info": {"query_result": {"companyName": "Google"}}}
    batch = {"batch_id": "1", "articles": [basic_article]}
    return batch


@pytest.mark.parametrize(
    "input, expected",
    [
        ("edgar_article_batch_1", "Intel Inc. are a company that makes things."),
        ("edgar_article_batch_2", "American Express ' credit cards are ok. American Express do banking things."),
        ("edgar_article_batch_3", "Google's search engine is famous. Google search things."),
    ],
)
def test_basic_coreference(input, expected, request):
    batch = request.getfixturevalue(input)
    result = BasicCoreference().run(batch)

    assert result["articles"][-1]["text"] == expected
