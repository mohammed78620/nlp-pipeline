from datetime import datetime

import pytest

from nlp_pipeline.tasks import (
    DateExtraction,
    NamedEntityLinking,
    NamedEntityRecognition,
    Publish,
    RelationExtraction,
    Segmentation,
)


def preprocess(batch):
    # process article to point it can be used by publish task
    segmentated = Segmentation().run(batch)
    nered = NamedEntityRecognition().run(segmentated)
    reed = RelationExtraction().run(nered)
    neled = NamedEntityLinking().run(reed)
    deed = DateExtraction().run(neled)
    return deed


@pytest.fixture
def batch_1(article_1s2e1r2l_1, handle_crawled_publish_location):
    destination_bucket, destination_path, destination_region = handle_crawled_publish_location
    article_1, _ = article_1s2e1r2l_1
    batch = {
        "batch_id": "01",
        "version": "1.0.0",
        "created_on": "2022-09-02",
        "source_file": "20220101/example.tar.gz",
        "source_type": "website",
        "source": "Directory Reader",
        "articles": [article_1],
    }
    deed = preprocess(batch)

    expected = f"{destination_path}{batch['batch_id']}.tar.gz"
    return deed, expected


@pytest.fixture
def batch_2(handle_crawled_publish_location):
    destination_bucket, destination_path, destination_region = handle_crawled_publish_location
    data = {
        "batch_id": "01",
        "version": "1.0.0",
        "created_on": "2022-09-02",
        "source_file": "20220101/example.tar.gz",
        "source_type": "website",
        "source": "Directory Reader",
        "articles": [
            {
                "id": "article_1s2e1r2l_1",
                "timestamp": 1,
                "wbm_id": "2",
                "access_epoch": 3,
                "scraper_type": "thing",
                "extra_header_info": "stuff",
                "host_name": "host",
                "redirected_from": None,
                "date_guess": "2000",
                "date_acc": "1",
                "url": "http://example.com",
                "meta_date": None,
                "meta_year": None,
                "html": "some html",
                "text": "Samsung is supplying Facebook with pencils.",
                "processed_file": "a file name",
                "sentences": [
                    {
                        "id": "c3962d6a6d531c1f556ffa02160bfd88",
                        "text": "Samsung is supplying Facebook with pencils.",
                        "entities": [
                            {
                                "id": 0,
                                "text": "Samsung",
                                "display_name": None,
                                "type": "ORG",
                                "token_start": 0,
                                "token_end": 1,
                                "end_pos": 7,
                                "start_pos": 0,
                                "vid": "samsungelectronicscoltd-bfe37bc8-a7ce-4081-a09c-e20d14e31d10",
                                "nel_score": 0.9953137040138245,
                            },
                            {
                                "id": 1,
                                "text": "Facebook",
                                "display_name": None,
                                "type": "ORG",
                                "token_start": 3,
                                "token_end": 4,
                                "end_pos": 29,
                                "start_pos": 21,
                                "vid": "facebookinc-ba1aead2-42fc-483c-b80d-566f85750ef3",
                                "nel_score": 1.0,
                            },
                        ],
                        "relations": [
                            {"from": 0, "to": 1, "label": "Supply1", "class": 1, "re_score": 0.9609044194221497}
                        ],
                    }
                ],
                "date": None,
                "year": None,
                "score": None,
            }
        ],
    }
    expected = f"{destination_path}01.tar.gz"
    return data, expected


@pytest.fixture
def batch_no_articles():
    data = {
        "batch_id": "01",
        "version": "1.0.0",
        "created_on": "2022-09-02",
        "source_file": "20220101/example.tar.gz",
        "source_type": "website",
        "source": "Directory Reader",
        "articles": [],
    }
    expected = {
        "batch_id": "01",
        "version": "1.0.0",
        "created_on": "2022-09-02",
        "source_file": "20220101/example.tar.gz",
        "source_type": "website",
        "source": "Directory Reader",
        "articles": [],
    }
    return data, expected


@pytest.fixture
def batch_none():
    data = None
    expected = None
    return data, expected


@pytest.mark.parametrize(
    "batch_fixture",
    [("batch_1"), ("batch_2"), ("batch_no_articles"), ("batch_none")],
)
def test_run(batch_fixture, handle_crawled_publish_location, request):
    # fetch fixtures
    batch, expected = request.getfixturevalue(batch_fixture)

    publish = Publish()
    publish.partition_by_day = False

    # run
    destination_bucket, destination_path, destination_region = handle_crawled_publish_location
    key = publish.run(batch, bucket=destination_bucket, path=destination_path, region=destination_region)

    # test results
    assert key == expected


@pytest.mark.parametrize(
    "year, month, day, expected",
    [(2020, 10, 30, "20201030"), (1980, 1, 7, "19800107")],
)
def test_format_date(year, month, day, expected):
    date = datetime(year=year, month=month, day=day)
    result = Publish().format_date(date)

    assert expected == result


def test_format_date_no_param():
    date = datetime.now()

    result = Publish().format_date()

    assert str(date.year) in result
    assert str(date.month) in result
    assert str(date.day) in result


@pytest.mark.parametrize(
    "partition_by_day, expect_date",
    [(True, True), (True, True), (False, False)],
)
def test_get_publish_path(partition_by_day, expect_date):
    publish = Publish()
    publish.partition_by_day = partition_by_day

    filename = "foo_bar"

    result = publish.get_publish_path(filename)

    assert filename in result

    date = Publish().format_date()
    if expect_date:
        assert date in result
    else:
        assert date not in result
