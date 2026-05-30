from typing import Dict, Tuple

import pytest

from nlp_pipeline.schema import vertexai as model
from nlp_pipeline.tasks.named_entity_recognition import NamedEntityRecognition
from nlp_pipeline.tasks.relation_extraction import RelationExtraction
from nlp_pipeline.tasks.segmentation import Segmentation


def preprocess(batch):
    # process article to point it can be used by RE
    segmentated = Segmentation().run(batch)
    nered = NamedEntityRecognition().run(segmentated)
    return nered


@pytest.fixture
def batch_1a_1s0e0r0l(article_1s0e0r0l) -> Tuple[Dict]:
    article_1, _ = article_1s0e0r0l

    batch = {
        "batch_id": "01",
        "version": "1.0.0",
        "created_on": "2022-09-02",
        "source_file": "20220101/example.tar.gz",
        "source_type": "website",
        "source": "Directory Reader",
        "articles": [article_1],
    }
    batch = preprocess(batch)

    expected = {"articles": [], "payload": None}

    return batch, expected


@pytest.fixture
def batch_1a_1s1e0r0l(article_1s1e0r0l) -> Tuple[Dict]:
    article_1, _ = article_1s1e0r0l

    batch = {
        "batch_id": "01",
        "version": "1.0.0",
        "created_on": "2022-09-02",
        "source_file": "20220101/example.tar.gz",
        "source_type": "website",
        "source": "Directory Reader",
        "articles": [article_1],
    }
    batch = preprocess(batch)

    expected = {"articles": [], "payload": None}

    return batch, expected


@pytest.fixture
def batch_1a_1s2e0r2l(article_1s2e0r2l) -> Tuple[Dict]:
    article_1, _ = article_1s2e0r2l
    payload = {
        "instances": [
            {
                "annotation": {
                    "entities": [
                        {
                            "id": 0,
                            "text": "Facebook",
                        },
                        {
                            "id": 1,
                            "text": "Samsung",
                        },
                    ]
                },
                "id": "a7b7ce572979d2f72c8b5fd24efa8f7f",
                "text": "Facebook is an entity and Samsung is an entity too.",
            }
        ]
    }

    batch = {
        "batch_id": "01",
        "version": "1.0.0",
        "created_on": "2022-09-02",
        "source_file": "20220101/example.tar.gz",
        "source_type": "website",
        "source": "Directory Reader",
        "articles": [article_1],
    }
    batch = preprocess(batch)

    expected = {"articles": [], "payload": payload}

    return batch, expected


@pytest.fixture
def batch_1a_1s2e1r2l(article_1s2e1r2l_1) -> Tuple[Dict]:
    article_1, expected_1 = article_1s2e1r2l_1
    payload = {
        "instances": [
            {
                "annotation": {
                    "entities": [
                        {
                            "id": 0,
                            "text": "Samsung",
                        },
                        {
                            "id": 1,
                            "text": "Facebook",
                        },
                    ]
                },
                "id": "c3962d6a6d531c1f556ffa02160bfd88",
                "text": "Samsung is supplying Facebook with pencils.",
            }
        ]
    }

    batch = {
        "batch_id": "01",
        "version": "1.0.0",
        "created_on": "2022-09-02",
        "source_file": "20220101/example.tar.gz",
        "source_type": "website",
        "source": "Directory Reader",
        "articles": [article_1],
    }
    batch = preprocess(batch)

    expected = {"articles": [expected_1], "payload": payload}

    return batch, expected


@pytest.mark.parametrize(
    "batch_fixture",
    [("batch_1a_1s0e0r0l"), ("batch_1a_1s1e0r0l"), ("batch_1a_1s2e0r2l"), ("batch_1a_1s2e1r2l")],
)
def test_relation_extraction(batch_fixture, request):
    # fetch article and expected from fixture
    batch, expected = request.getfixturevalue(batch_fixture)

    # run test
    reed = RelationExtraction().run(batch)

    # test results of test
    assert len(reed["articles"]) == len(expected["articles"])

    for idx, expected_article in enumerate(expected["articles"]):
        article = reed["articles"][idx]

        assert len(article["sentences"]) == len(expected_article["sentences"])
        for jdx, expected_sentence in enumerate(expected_article["sentences"]):
            sentence = article["sentences"][jdx]

            assert len(sentence["entities"]) == expected_sentence["entities"]
            assert len(sentence["relations"]) == expected_sentence["relations"]


@pytest.mark.parametrize(
    "article_batch_fixture, batch_size, expected_num_payloads",
    [
        ("batch_1a_1s0e0r0l", 1, 0),
        ("batch_1a_1s1e0r0l", 1, 0),
        ("batch_1a_1s2e0r2l", 1, 1),
        ("batch_1a_1s2e1r2l", 1, 1),
    ],
)
def test_payloads_generator(article_batch_fixture, batch_size, expected_num_payloads, request):
    # fetch fixtures
    article_batch, expected = request.getfixturevalue(article_batch_fixture)

    re = RelationExtraction()
    re.endpoint_batch_size = batch_size

    # run it
    result = re.payloads_generator(article_batch)

    assert len(result) == expected_num_payloads

    try:
        for payload in result:
            # make sure result is valid
            _ = model.REPayload(**payload).model_dump(by_alias=True)
    except Exception as exc:
        raise AssertionError(f"Invalid payload returned {exc}")


@pytest.mark.parametrize(
    "num_articles, num_sentences, num_entities, max_time_cost, base_time_cost, max_num_entities, endpoint_batch_size, expected",
    [
        # not enough entities
        (1, 1, 0, 10000, 10, 10, 100, 0),
        # not enough entities
        (1, 1, 1, 10000, 10, 10, 100, 0),
        # too many entities
        (1, 1, 10, 10000, 10, 5, 100, 0),
        # costs too much
        (1, 1, 10, 100, 100, 500, 100, 0),
        # doesn't fill a payload
        (1, 2, 2, 10000, 10, 10, 100, 1),
        # payload split due to cost
        (1, 2, 2, 300, 200, 10, 100, 2),
        # payload split due to batch size
        (1, 2, 2, 10000, 200, 10, 1, 2),
    ],
)
def test_payloads_generator_time_split(
    num_articles,
    num_sentences,
    num_entities,
    max_time_cost,
    base_time_cost,
    max_num_entities,
    endpoint_batch_size,
    expected,
):
    batch = {"articles": []}
    for i in range(num_articles):
        article = {"sentences": []}
        for j in range(num_sentences):
            sentence = {
                "id": str(i) + "-" + str(j),
                "text": "test text",
                "entities": [0] * num_entities,
            }
            article["sentences"].append(sentence)
        batch["articles"].append(article)

    re = RelationExtraction()
    re.endpoint_batch_size = endpoint_batch_size
    re.max_num_entities = max_num_entities
    re.max_time_cost = max_time_cost
    re.base_time_cost = base_time_cost

    result = re.payloads_generator(batch)
    assert len(result) == expected


@pytest.mark.parametrize(
    "num_entities, expected",
    [
        (0, 0),
        (1, 0),
        (2, 200),
        (3, 600),
        (10, 9000),
    ],
)
def test_estimate_time_cost(num_entities, expected):
    re = RelationExtraction()
    re.base_time_cost = 200

    result = re.estimate_time_cost(num_entities)
    assert result == expected
