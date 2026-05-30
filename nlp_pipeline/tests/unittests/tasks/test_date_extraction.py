from copy import deepcopy

import pytest

from nlp_pipeline.tasks.date_extraction import DateExtraction


@pytest.fixture
def article_1(basic_article):
    article = deepcopy(basic_article)
    article["id"] = "1"
    article["text"] = """News 23 June 2009 COLT selects Infinera to boost pan-European network European
    business communications provider COLT has selected a digital optical network from Infinera
    Corp of Sunnyvale, CA, USA, a vertically integrated manufacturer of digital optical network
    systems incorporating its own indium phosphide-based photonic integrated circuits , for its
    pan-European network in order to speed delivery of a broad range of service."""
    article["sentences"] = []
    return article


@pytest.fixture
def batch_1(article_1):
    batch = {
        "batch_id": "1",
        "version": "1.0",
        "created_on": "2022-09-02",
        "source_file": "20220101/example.tar.gz",
        "source_type": "website",
        "source": "Directory Reader",
        "articles": [
            article_1,
        ],
    }
    return batch


@pytest.fixture
def article_1_expected(article_1):
    article = deepcopy(article_1)
    article["metadata"]["date"] = "2009-06-23"
    article["metadata"]["year"] = 2009
    return article


@pytest.fixture
def batch_1_expected(article_1_expected, batch_1):
    batch = deepcopy(batch_1)
    batch["articles"] = [deepcopy(article_1_expected)]
    return batch


@pytest.fixture
def batch_2(article_1):
    """
    Article with meta data
    """
    article = deepcopy(article_1)
    article["metadata"]["meta_date"] = "2009-06-23"
    article["metadata"]["meta_year"] = 2009

    batch = {
        "batch_id": "1",
        "version": "1.0",
        "created_on": "2022-09-02",
        "source_file": "20220101/example.tar.gz",
        "source_type": "website",
        "source": "Directory Reader",
        "articles": [
            article,
        ],
    }
    return batch


@pytest.fixture
def batch_2_expected(article_1_expected, batch_1):
    batch = deepcopy(batch_1)

    article = deepcopy(article_1_expected)
    article["metadata"]["date"] = "2009-06-23"
    article["metadata"]["year"] = 2009

    batch["articles"] = [article]
    return batch


@pytest.fixture
def batch_3(article_1):
    """
    Article with meta data
    """
    article = deepcopy(article_1)
    article["metadata"]["meta_date"] = "2009-06-23"
    article["metadata"]["meta_year"] = 2009
    article["metadata"]["date"] = "2009-06-23"
    article["metadata"]["year"] = 2009

    batch = {
        "batch_id": "1",
        "version": "1.0",
        "created_on": "2022-09-02",
        "source_file": "20220101/example.tar.gz",
        "source_type": "website",
        "source": "Directory Reader",
        "articles": [
            article,
        ],
    }
    return batch


@pytest.fixture
def batch_3_expected(article_1_expected, batch_1):
    batch = deepcopy(batch_1)

    article = deepcopy(article_1_expected)
    article["metadata"]["date"] = "2009-06-23"
    article["metadata"]["year"] = 2009

    batch["articles"] = [article]
    return batch


@pytest.mark.parametrize(
    "batch, expected",
    [("batch_1", "batch_1_expected"), ("batch_2", "batch_2_expected"), ("batch_3", "batch_3_expected")],
)
def test_run(batch, expected, request):
    batch = request.getfixturevalue(batch)
    expected = request.getfixturevalue(expected)

    res = DateExtraction().run(batch)

    assert res["articles"][0]["metadata"]["date"] == expected["articles"][0]["metadata"]["date"]
    assert res["articles"][0]["metadata"]["year"] == expected["articles"][0]["metadata"]["year"]
