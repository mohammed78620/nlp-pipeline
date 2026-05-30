import copy
from typing import Dict, List

import pytest

from nlp_pipeline.schema import vertexai as model
from nlp_pipeline.tasks.named_entity_recognition import NamedEntityRecognition


@pytest.fixture
def sentence_no_entity_1() -> Dict:
    """
    Sentence with no entities
    """
    sentence = {
        "id": "unique-001",
        "fingerprint": "[123456, 123456, 123456, 123456]",
        "text": "This is a sentence with no entity.",
    }
    return sentence


@pytest.fixture
def sentence_no_entity_2() -> Dict:
    """
    Different sentence with no entities
    """
    sentence = {
        "id": "unique-002",
        "fingerprint": "[123456, 123456, 123456, 123456]",
        "text": "This is a different sentence with no entity.",
    }
    return sentence


@pytest.fixture
def sentence_with_entities_1() -> Dict:
    """
    Sentence with 2 entities
    """
    sentence = {
        "id": "unique-003",
        "fingerprint": "[123456, 123456, 123456, 123456]",
        "text": "Google is an entity and Samsung is one too.",
    }
    return sentence


@pytest.fixture
def sentence_with_entities_2() -> Dict:
    """
    Different sentence with 2 entities
    """
    sentence = {
        "id": "unique-004",
        "fingerprint": "[123456, 123456, 123456, 123456]",
        "text": "Facebook is an entity and Boeing is one too.",
    }
    return sentence


@pytest.fixture
def entities_1() -> List[Dict]:
    """
    Entities definition for fixture `sentence_with_entities_1`
    """
    entities = [
        {
            "text": "Google",
            "label": "ORG",
            "start": 0,
            "end": 1,
            "start_char": 0,
            "end_char": 6,
        },
        {
            "text": "Samsung",
            "label": "ORG",
            "start": 5,
            "end": 6,
            "start_char": 24,
            "end_char": 31,
        },
    ]
    return entities


@pytest.fixture
def entities_2() -> List[Dict]:
    """
    Entities definition for fixture `sentence_with_entities_2`
    """
    entities = [
        {
            "text": "Facebook",
            "label": "ORG",
            "start": 0,
            "end": 1,
            "start_char": 0,
            "end_char": 8,
        },
        {
            "text": "Boeing",
            "label": "ORG",
            "start": 5,
            "end": 6,
            "start_char": 26,
            "end_char": 32,
        },
    ]
    return entities


@pytest.fixture
def segmented_article_0s0e_1(basic_article: Dict) -> Dict:
    """
    Segmented article: 0 sentences
    """
    article = copy.deepcopy(basic_article)
    article["id"] = "article_01"
    article["sentences"] = []
    return article


@pytest.fixture
def segmented_article_1s0e_1(basic_article: Dict, sentence_no_entity_1) -> Dict:
    """
    Segmented article: 1 sentence with no entities
    """
    article = copy.deepcopy(basic_article)
    article["id"] = "article_01"
    article["sentences"] = [sentence_no_entity_1]
    return article


@pytest.fixture
def segmented_article_1s0e_2(basic_article, sentence_no_entity_2):
    """
    Different segmented article: 1 sentence with no entities
    """
    article = copy.deepcopy(basic_article)
    article["id"] = "article_02"
    article["sentences"] = [sentence_no_entity_2]
    return article


@pytest.fixture
def segmented_article_1s1e_1(basic_article, sentence_with_entities_1):
    """
    Segmented article: 1 sentence with entities
    """
    article = copy.deepcopy(basic_article)
    article["id"] = "article_03"
    article["sentences"] = [sentence_with_entities_1]
    return article


@pytest.fixture
def segmented_article_2s0e_1(basic_article, sentence_no_entity_1, sentence_no_entity_2):
    """
    Segmented article: 2 sentences with no entities
    """
    article = copy.deepcopy(basic_article)
    article["id"] = "article_04"
    article["sentences"] = [sentence_no_entity_1, sentence_no_entity_2]
    return article


@pytest.fixture
def segmented_article_2s1e_1(basic_article, sentence_no_entity_1, sentence_with_entities_1):
    """
    Segmented article: 2 sentences, only 2nd has entities
    """
    article = copy.deepcopy(basic_article)
    article["id"] = "article_05"
    article["sentences"] = [sentence_no_entity_1, sentence_with_entities_1]
    return article


@pytest.fixture
def article_batch_1a0s0e(segmented_article_0s0e_1):
    """
    Segmented batch: 1 article with 0 sentences.
    """
    data = {
        "batch_id": "1",
        "articles": [segmented_article_0s0e_1],
    }
    return data


@pytest.fixture
def article_batch_1a1s0e(segmented_article_1s0e_1):
    """
    Segmented batch: 1 article with 1 sentence that has no entities.
    """
    data = {
        "batch_id": "1",
        "version": "1.0.0",
        "created_on": "2022-09-02",
        "source_file": "20220101/example.tar.gz",
        "source_type": "website",
        "source": "Directory Reader",
        "articles": [segmented_article_1s0e_1],
    }
    return data


@pytest.fixture
def article_batch_1a1s1e(segmented_article_1s1e_1):
    """
    Segmented batch: 1 article with 1 sentence containing entities.
    """
    data = {
        "batch_id": "2",
        "version": "1.0.0",
        "created_on": "2022-09-02",
        "source_file": "20220101/example.tar.gz",
        "source_type": "website",
        "source": "Directory Reader",
        "articles": [segmented_article_1s1e_1],
    }
    return data


@pytest.fixture
def article_batch_1a2s0e(segmented_article_2s0e_1):
    """
    Segmented batch: 1 article with 2 sentences, no entities.
    """
    data = {
        "batch_id": "3",
        "articles": [segmented_article_2s0e_1],
    }
    return data


@pytest.fixture
def article_batch_1a2s1e(segmented_article_2s1e_1):
    """
    Segmented batch: 1 article with 2 sentence, 1 with entities.
    """
    data = {
        "batch_id": "4",
        "articles": [segmented_article_2s1e_1],
    }
    return data


@pytest.fixture
def article_batch_2a1s0e(segmented_article_1s0e_1, segmented_article_1s0e_2):
    """
    2 articles with 1 sentence each, both no entities.
    """
    data = {
        "batch_id": "5",
        "articles": [segmented_article_1s0e_1, segmented_article_1s0e_2],
    }
    return data


@pytest.fixture
def article_batch_2a1s1e(segmented_article_1s0e_1, segmented_article_1s1e_1):
    """
    2 articles with 1 sentence each, only 2nd has entities.
    """
    data = {
        "batch_id": "6",
        "articles": [segmented_article_1s0e_1, segmented_article_1s1e_1],
    }
    return data


@pytest.fixture
def ner_processed_1a1s0e():
    """
    Expected result after processing response from NER Vertex AI for:
    1 article with 1 sentence, no entities.
    """
    data = {
        "batch_id": "1",
        "articles": [],
    }
    return data


@pytest.fixture
def ner_processed_1a2s0e():
    """
    Expected result after processing response from NER Vertex AI for:
    1 article with 2 sentence, no entities.
    """
    data = {
        "batch_id": "3",
        "articles": [],
    }
    return data


@pytest.fixture
def ner_processed_1a1s1e(article_batch_1a1s1e, entities_1):
    """
    Expected result after processing response from NER Vertex AI for:
    1 article with 1 sentence containing entities.
    """

    data = article_batch_1a1s1e

    # patch in entities
    data["articles"][0]["sentences"][0]["entities"] = entities_1

    return data


@pytest.fixture
def ner_processed_1a2s1e(article_batch_1a2s1e, entities_1):
    """
    Expected result after processing response from NER Vertex AI for:
    1 article with 2 sentences, 1 with entities.
    """

    data = article_batch_1a2s1e

    # patch in entities to 2nd sentence since it has entities
    data["articles"][0]["sentences"][1]["entities"] = entities_1

    # remove first setence that has no entities
    data["articles"][0]["sentences"].pop(0)

    return data


@pytest.fixture
def ner_processed_2a1s1e(article_batch_2a1s1e, entities_1):
    """
    Expected result after processing response from NER Vertex AI for:
    2 articles with 1 sentence each, only 2nd has entities.
    """

    data = article_batch_2a1s1e

    # patch in entities
    data["articles"][1]["sentences"][0]["entities"] = entities_1

    # remove first article that has no entities
    data["articles"].pop(0)

    return data


@pytest.mark.parametrize(
    "article_batch_fixture, batch_size, expected_num_payloads",
    [
        ("article_batch_1a0s0e", 1, 0),
        ("article_batch_1a1s0e", 1, 1),
        ("article_batch_1a2s0e", 1, 2),
        ("article_batch_2a1s0e", 1, 2),
        ("article_batch_2a1s1e", 1, 2),
        ("article_batch_1a0s0e", 2, 0),
        ("article_batch_1a1s0e", 2, 1),
        ("article_batch_1a2s0e", 2, 1),
        ("article_batch_2a1s0e", 2, 1),
        ("article_batch_2a1s1e", 2, 1),
    ],
)
def test_payloads_generator(article_batch_fixture, batch_size, expected_num_payloads, request):
    # fetch fixtures
    article_batch = request.getfixturevalue(article_batch_fixture)

    ner = NamedEntityRecognition()
    ner.endpoint_batch_size = batch_size

    # run it
    result = ner.payloads_generator(article_batch)

    assert len(result) == expected_num_payloads

    try:
        for payload in result:
            # make sure result is valid
            model.NERPayload(**payload).model_dump(by_alias=True)
    except Exception as exc:
        raise AssertionError(f"Invalid payload returned {exc}")


@pytest.mark.parametrize(
    "article_batch_fixture, expected_fixture",
    [
        ("article_batch_1a1s0e", "ner_processed_1a1s0e"),
        ("article_batch_1a1s1e", "ner_processed_1a1s1e"),
        ("article_batch_1a2s0e", "ner_processed_1a2s0e"),
        ("article_batch_1a2s1e", "ner_processed_1a2s1e"),
        ("article_batch_2a1s1e", "ner_processed_2a1s1e"),
    ],
)
def test_process_response(article_batch_fixture, expected_fixture, request):
    # fetch fixture
    article_batch = request.getfixturevalue(article_batch_fixture)
    expected = request.getfixturevalue(expected_fixture)

    ner = NamedEntityRecognition()

    payloads = ner.payloads_generator(article_batch)
    response = ner.batch_query(payloads)
    result = ner.process_response(article_batch, response)

    assert result["batch_id"] == expected["batch_id"]
    assert len(result["articles"]) == len(expected["articles"])

    for a_idx, article in enumerate(result["articles"]):
        expected_article = expected["articles"][a_idx]
        assert len(article["sentences"]) == len(expected_article["sentences"])

        for s_idx, sentence in enumerate(article["sentences"]):
            expected_sentence = expected_article["sentences"][s_idx]
            assert len(sentence["entities"]) == len(expected_sentence["entities"])


@pytest.mark.parametrize(
    "article_batch_fixture, expected_fixture",
    [
        (
            "article_batch_1a1s0e",
            "ner_processed_1a1s0e",
        ),
        (
            "article_batch_1a1s1e",
            "ner_processed_1a1s1e",
        ),
    ],
)
def test_run(article_batch_fixture, expected_fixture, request):
    # fetch fixture
    article_batch = request.getfixturevalue(article_batch_fixture)
    expected = request.getfixturevalue(expected_fixture)

    result = NamedEntityRecognition().run(article_batch)

    assert result["batch_id"] == article_batch["batch_id"]
    assert len(result["articles"]) == len(expected["articles"])

    for a_idx, article in enumerate(result["articles"]):
        expected_article = expected["articles"][a_idx]
        assert len(article["sentences"]) == len(expected_article["sentences"])

        for s_idx, sentence in enumerate(article["sentences"]):
            expected_sentence = expected_article["sentences"][s_idx]
            assert len(sentence["entities"]) == len(expected_sentence["entities"])
