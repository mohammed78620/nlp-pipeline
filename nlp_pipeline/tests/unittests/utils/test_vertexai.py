import pytest

from nlp_pipeline.exceptions.vertexai import EndpointDoesNotExistError
from nlp_pipeline.schema import vertexai as model
from nlp_pipeline.utils.vertexai import Endpoint, VertexAI


@pytest.fixture
def data_ner():
    data = {
        "instances": [
            {
                "id": "c3962d6a6d531c1f556ffa02160bfd88",
                "text": "Samsung is supplying Facebook with pencils.",
            }
        ]
    }
    data = model.NERPayload(**data).model_dump(by_alias=True)
    return data


@pytest.fixture
def data_re():
    data = {
        "instances": [
            {
                "annotation": {
                    "entities": [
                        {
                            "id": 0,
                            "text": "Samsung",
                            "type": "ORG",
                            "token_start": 0,
                            "token_end": 1,
                            "end_pos": 7,
                            "start_pos": 0,
                            "ner_score": 0.9993829727172852,
                        },
                        {
                            "id": 1,
                            "text": "Facebook",
                            "type": "ORG",
                            "token_start": 3,
                            "token_end": 4,
                            "end_pos": 29,
                            "start_pos": 21,
                            "ner_score": 0.9989801049232483,
                        },
                    ]
                },
                "id": "c3962d6a6d531c1f556ffa02160bfd88",
                "text": "Samsung is supplying Facebook with pencils.",
            }
        ]
    }
    data = model.REPayload(**data).model_dump(by_alias=True)
    return data


@pytest.fixture
def data_nel():
    data = {
        "instances": [
            {
                "annotation": {
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
                            "ner_score": 0.9993829727172852,
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
                            "ner_score": 0.9989801049232483,
                            "ner_version": "0.0.1",
                        },
                    ]
                },
                "text": "Samsung is supplying Facebook with pencils.",
                "id": "c3962d6a6d531c1f556ffa02160bfd88",
            }
        ]
    }

    data = model.NELPayload(**data).model_dump(by_alias=True)
    return data


@pytest.fixture
def data_de():
    data = {
        "instances": [
            {
                "id": "1",
                "text": "News 23 June 2009 COLT selects Infinera to boost pan-European network European business communications provider COLT has selected a digital optical network from Infinera Corp of Sunnyvale, CA, USA, a vertically integrated manufacturer of digital optical network systems incorporating its own indium phosphide-based photonic integrated circuits , for its pan-European network in order to speed delivery of a broad range of service.",
            },
            {
                "id": "2",
                "text": "As seismic processing was moved aggressively to GPUs in the next couple of years, Eni held steady with its systems during the oil downturn, and when things were looking a little brighter in 2017, the company decommissioned HPC1 and brought the HPC3 system online, which was built by Lenovo using the follow-on to the iDataPlex, called the NextScale nx360M5, it had acquired from IBM as part of its deal to buy the System x division.",
            },
            {
                "id": "3",
                "text": "Dell experienced rising orders from the enterprise and education sectors in April, helping the US-based vendor advance to second place in vendors ranking, surpassing Lenovo.",
            },
            {
                "id": "4",
                "text": "In fact, HP is the second biggest PC manufacturer in the world (behind Lenovo, and very close behind for that matter).So as you'd expect, HP makes lots of different desktops and laptops, and Chromebooks are a part of the latter equation.",
            },
            {
                "id": "5",
                "text": "Lenovo is launching a performance optimized offering based on Lenovo ThinkSystem SR650/SR630 servers and switches, Red Hat OpenStack Platform, and Mellanox ConnectX-4 NICs for accelerated packet processing.",
            },
        ]
    }
    data = model.DEPayload(**data).model_dump(by_alias=True)
    return data


def test_vertexai_ner(data_ner):
    endpoint = Endpoint.named_entity_recognition
    payload = data_ner

    sm_client = VertexAI(endpoint)

    successful, response = sm_client.run(payload)
    data = model.NERResponse(**response).model_dump(by_alias=True)

    predictions = {}
    for prediction in data["predictions"]:
        predictions.update(prediction)

    assert successful is True
    assert len(predictions) == len(data_ner["instances"])

    for id in predictions:
        for entry in predictions[id]:
            assert "ner_version" in entry.keys()
            assert entry["ner_version"] != "0.0.0"


def test_vertexai_re(data_re):
    endpoint = Endpoint.relation_extraction
    payload = data_re

    sm_client = VertexAI(endpoint)

    successful, response = sm_client.run(payload)
    data = model.REResponse(**response).model_dump(by_alias=True)

    predictions = {}
    for prediction in data["predictions"]:
        predictions.update(prediction)

    assert successful is True
    assert len(predictions) == len(data_re["instances"])

    for id in predictions:
        for entry in predictions[id]:
            assert "re_version" in entry.keys()
            assert entry["re_version"] != "0.0.0"


def test_vertexai_nel(data_nel):
    endpoint = Endpoint.named_entity_linking
    payload = data_nel

    sm_client = VertexAI(endpoint)

    successful, response = sm_client.run(payload)
    data = model.NELResponse(**response).model_dump(by_alias=True)

    predictions = {}
    for prediction in data["predictions"]:
        predictions.update(prediction)

    assert successful is True
    assert len(predictions) == len(data_nel["instances"])

    for id in predictions:
        for idx, entry in enumerate(predictions[id]):
            assert "ner_version" in entry.keys()
            if idx == 1:
                assert entry["ner_version"] == "0.0.1"

            assert "nel_version" in entry.keys()
            assert entry["nel_version"] != "0.0.0"


def test_vertexai_de(data_de):
    endpoint = Endpoint.date_extraction
    payload = data_de

    sm_client = VertexAI(endpoint)

    successful, response = sm_client.run(payload)
    data = model.DEResponse(**response).model_dump(by_alias=True)

    predictions = {}
    for prediction in data["predictions"]:
        predictions.update(prediction)

    assert successful is True
    assert len(predictions) == len(data_de["instances"])

    for id in predictions:
        entry = predictions[id]

        assert "de_version" in entry.keys()
        assert entry["de_version"] != "0.0.0"


@pytest.mark.parametrize(
    "input, expected",
    [
        (Endpoint.named_entity_recognition, True),
        (Endpoint.relation_extraction, True),
        (Endpoint.named_entity_linking, True),
        (Endpoint.date_extraction, True),
    ],
)
def test_is_endpoint_up(input, expected):
    sm_client = VertexAI(input)
    assert sm_client.is_endpoint_up() == expected


def test_endpoint_does_not_exist():
    endpoint = "ThisEndpointShouldntExist"

    with pytest.raises(EndpointDoesNotExistError):
        VertexAI(endpoint, validate_endpoint=True)
