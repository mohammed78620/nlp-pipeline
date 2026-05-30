from copy import deepcopy

import pytest

from nlp_pipeline.tasks.named_entity_linking import NamedEntityLinking


@pytest.fixture
def article_1(basic_article):
    article = deepcopy(basic_article)
    article["id"] = "1"
    article["sentences"] = [
        {
            "id": "1",
            "fingerprint": "[123456, 123456, 123456, 123456]",
            "text": "Empired has won a place in the prestigious Micros      oft Dynamics Inner Circle - an elite group of Dynamics",
            "entities": [
                {
                    "id": 1,
                    "end_pos": 7,
                    "text": "Empired",
                    "type": "ORG",
                    "start_pos": 0,
                    "token_start": 0,
                    "token_end": 1,
                    "ner_score": 0.99,
                },
                {
                    "id": 2,
                    "end_pos": 52,
                    "text": "Microsoft",
                    "type": "ORG",
                    "start_pos": 43,
                    "token_start": 8,
                    "token_end": 9,
                    "ner_score": 0.99,
                },
            ],
            "relations": [],
        }
    ]
    return article


@pytest.fixture
def article_2(basic_article):
    article = deepcopy(basic_article)
    article["id"] = "2"
    article["sentences"] = [
        {
            "id": "1",
            "fingerprint": "[123456, 123456, 123456, 123456]",
            "text": "UXC wins $25 million NSW government agency contra      ct",
            "entities": [
                {
                    "id": 3,
                    "end_pos": 3,
                    "text": "UXC",
                    "type": "ORG",
                    "start_pos": 0,
                    "token_start": 0,
                    "token_end": 1,
                    "ner_score": 0.99,
                },
                {
                    "id": 4,
                    "end_pos": 42,
                    "text": "NSW government agency",
                    "type": "ORG",
                    "start_pos": 21,
                    "token_start": 5,
                    "token_end": 8,
                    "ner_score": 0.99,
                },
            ],
            "relations": [],
        }
    ]
    return article


@pytest.fixture
def batch1(article_1, article_2):
    batch = {
        "batch_id": "1",
        "version": "1.0.0",
        "created_on": "2022-09-02",
        "source_file": "20220101/example.tar.gz",
        "source_type": "website",
        "source": "Directory Reader",
        "articles": [
            article_1,
            article_2,
        ],
    }
    return batch


@pytest.fixture
def batch2(article_1):
    batch = {
        "batch_id": "1",
        "version": "1.0.0",
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
def batch3(article_2):
    batch = {
        "batch_id": "2",
        "version": "1.0.0",
        "created_on": "2022-09-02",
        "source_file": "20220101/example.tar.gz",
        "source_type": "website",
        "source": "Directory Reader",
        "articles": [
            article_2,
        ],
    }
    return batch


@pytest.fixture
def nel_predicted1(batch1):
    prediction = deepcopy(batch1)
    prediction["articles"][0]["sentences"][0]["entities"] = [
        {
            "id": 3,
            "text": "UXC",
            "display_name": None,
            "type": "ORG",
            "token_start": 0,
            "token_end": 1,
            "end_pos": 3,
            "start_pos": 0,
            "vid": None,
            "nel_score": 0.0,
            "ner_score": 0.99,
        },
        {
            "id": 4,
            "text": "NSW government agency",
            "display_name": None,
            "type": "ORG",
            "token_start": 5,
            "token_end": 8,
            "end_pos": 42,
            "start_pos": 21,
            "vid": None,
            "nel_score": 0.0,
            "ner_score": 0.99,
        },
    ]

    prediction["articles"][1]["sentences"][0]["entities"] = [
        {
            "id": 3,
            "text": "UXC",
            "display_name": None,
            "type": "ORG",
            "token_start": 0,
            "token_end": 1,
            "end_pos": 3,
            "start_pos": 0,
            "vid": None,
            "nel_score": 0.0,
            "ner_score": 0.99,
        },
        {
            "id": 4,
            "text": "NSW government agency",
            "display_name": None,
            "type": "ORG",
            "token_start": 5,
            "token_end": 8,
            "end_pos": 42,
            "start_pos": 21,
            "vid": None,
            "nel_score": 0.0,
            "ner_score": 0.99,
        },
    ]

    return prediction


@pytest.fixture
def nel_predicted2():
    return {
        "batch_id": "1",
        "version": "1.0.0",
        "source": "Directory Reader",
        "created_on": "2022-09-02",
        "source_type": "website",
        "articles": [
            {
                "id": "1",
                "sentences": [
                    {
                        "id": "1",
                        "fingerprint": "[123456, 123456, 123456, 123456]",
                        "text": "Empired has won a place in the prestigious Micros      oft Dynamics Inner Circle - an elite group of Dynamics",
                        "entities": [
                            {
                                "id": 1,
                                "text": "Empired",
                                "display_name": None,
                                "type": "ORG",
                                "token_start": 0,
                                "token_end": 1,
                                "end_pos": 7,
                                "start_pos": 0,
                                "vid": None,
                                "nel_score": 0.0,
                                "ner_score": 0.99,
                            }
                        ],
                    }
                ],
            }
        ],
    }


@pytest.fixture
def nel_predicted3():
    return {
        "batch_id": "2",
        "version": "1.0.0",
        "source": "Directory Reader",
        "created_on": "2022-09-02",
        "source_type": "website",
        "articles": [
            {
                "id": "2",
                "sentences": [
                    {
                        "id": "1",
                        "fingerprint": "[123456, 123456, 123456, 123456]",
                        "text": "UXC wins $25 million NSW government agency contra      ct",
                        "entities": [
                            {
                                "id": 3,
                                "text": "UXC",
                                "display_name": None,
                                "type": "ORG",
                                "token_start": 0,
                                "token_end": 1,
                                "end_pos": 3,
                                "start_pos": 0,
                                "vid": None,
                                "nel_score": 0.0,
                                "ner_score": 0.99,
                            },
                            {
                                "id": 4,
                                "text": "NSW government agency",
                                "display_name": None,
                                "type": "ORG",
                                "token_start": 5,
                                "token_end": 8,
                                "end_pos": 42,
                                "start_pos": 21,
                                "vid": None,
                                "nel_score": 0.0,
                                "ner_score": 0.99,
                            },
                        ],
                    }
                ],
            }
        ],
    }


@pytest.mark.parametrize(
    "batch, expected",
    [
        ("batch1", "nel_predicted1"),
        ("batch2", "nel_predicted2"),
        ("batch3", "nel_predicted3"),
    ],
)
def test_named_entity_linking_run(batch, expected, request):
    batch = request.getfixturevalue(batch)
    expected = request.getfixturevalue(expected)
    res = NamedEntityLinking().run(batch)

    assert len(res["articles"]) == len(expected["articles"])
    for idx, article in enumerate(res["articles"]):
        assert len(article["sentences"]) == len(expected["articles"][idx]["sentences"])
        for ydx, sentence in enumerate(article["sentences"]):
            expected_entities = expected["articles"][idx]["sentences"][ydx]["entities"]
            assert len(sentence["entities"]) == len(expected_entities)


@pytest.fixture
def nel_payload():
    return {
        "annotations": [
            {
                "annotation": {
                    "entities": [
                        {
                            "id": 1,
                            "text": "Empired",
                            "display_name": None,
                            "type": "ORG",
                            "token_start": 0,
                            "token_end": 1,
                            "end_pos": 7,
                            "start_pos": 0,
                            "ner_score": 0.99,
                        },
                        {
                            "id": 2,
                            "text": "Microsoft",
                            "display_name": None,
                            "type": "ORG",
                            "token_start": 8,
                            "token_end": 9,
                            "end_pos": 52,
                            "start_pos": 43,
                            "ner_score": 0.99,
                        },
                    ]
                },
                "text": "Empired has won a place in the prestigious Micros      oft Dynamics Inner Circle - an elite group of Dynamics",
                "id": "1",
                "fingerprint": "[123456, 123456, 123456, 123456]",
            },
            {
                "annotation": {
                    "entities": [
                        {
                            "id": 3,
                            "text": "UXC",
                            "display_name": None,
                            "type": "ORG",
                            "token_start": 0,
                            "token_end": 1,
                            "end_pos": 3,
                            "start_pos": 0,
                            "ner_score": 0.99,
                        },
                        {
                            "id": 4,
                            "text": "NSW government agency",
                            "display_name": None,
                            "type": "ORG",
                            "token_start": 5,
                            "token_end": 8,
                            "end_pos": 42,
                            "start_pos": 21,
                            "ner_score": 0.99,
                        },
                    ]
                },
                "text": "UXC wins $25 million NSW government agency contra      ct",
                "id": "1",
                "fingerprint": "[123456, 123456, 123456, 123456]",
            },
        ]
    }


def test_nel_extract_payload(batch1, nel_payload):
    nel = NamedEntityLinking()
    payloads = nel.payloads_generator(batch1)

    assert payloads != []
    assert len(payloads) > 0


@pytest.fixture
def nel_response():
    return {
        "batch_size": "1",
        "version": "1.0.0",
        "source": "Directory Reader",
        "created_on": "2022-09-02",
        "source_type": "website",
        "predictions": [
            {
                "1": [
                    {
                        "id": 3,
                        "text": "UXC",
                        "display_name": None,
                        "type": "ORG",
                        "token_start": 0,
                        "token_end": 1,
                        "end_pos": 3,
                        "start_pos": 0,
                        "vid": None,
                        "nel_score": 0.0,
                        "ner_score": 0.99,
                    },
                    {
                        "id": 4,
                        "text": "NSW government agency",
                        "display_name": None,
                        "type": "ORG",
                        "token_start": 5,
                        "token_end": 8,
                        "end_pos": 42,
                        "start_pos": 21,
                        "vid": None,
                        "nel_score": 0.0,
                        "ner_score": 0.99,
                    },
                ]
            }
        ],
    }


def test_nel_process_output(batch1, nel_response, nel_predicted1):
    nel = NamedEntityLinking()
    result = nel.process_response(batch1, nel_response)

    assert result.keys() == nel_predicted1.keys()
    assert len(result["articles"]) == len(nel_predicted1["articles"])
    for idx, article in enumerate(result["articles"]):
        assert len(article["sentences"]) == len(nel_predicted1["articles"][idx]["sentences"])
        for ydx, sentence in enumerate(article["sentences"]):
            assert sentence["text"] == nel_predicted1["articles"][idx]["sentences"][ydx]["text"]
            assert len(sentence["entities"]) == len(nel_predicted1["articles"][idx]["sentences"][ydx]["entities"])
