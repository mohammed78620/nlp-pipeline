from unittest.mock import Mock, patch

import pytest
from celery.exceptions import MaxRetriesExceededError
from google.api_core import exceptions

from nlp_pipeline.exceptions.vertexai import EndpointDoesNotExistError
from nlp_pipeline.settings import NAMED_ENTITY_RECOGNITION_ERROR_QUEUE_NAME
from nlp_pipeline.tasks.vertexai_endpoint import VertexAIEndpoint
from nlp_pipeline.utils.vertexai import Endpoint


@patch("nlp_pipeline.tasks.vertexai_endpoint.VertexAIEndpoint.request")
def test_get_subbatch_size(mock_vertexaiendpoint_request: Mock = None):
    """
    Test retries affect subbatch size to use
    """
    # Setup
    initial_batch_size = 10
    settings = {
        "name": "Test NER",
        "endpoint": Endpoint.named_entity_recognition,
        "queue": "named-entity-recognition",
        "endpoint_batch_size": initial_batch_size,
        "validation": {
            "payload": False,
            "response": False,
            "batch_input": False,
            "batch_output": False,
            "nuke_if_no_payload": False,
        },
        "models": {
            "task_input": None,
            "task_output": None,
            "endpoint_payload": None,
            "endpoint_response": None,
        },
    }
    vaie = VertexAIEndpoint(settings)

    # Run test - no retries occured
    mock_vertexaiendpoint_request.retries = 0
    result = vaie.get_subbatch_size()

    assert type(result) is int
    assert result == initial_batch_size

    # Run test - 1 retry occured
    mock_vertexaiendpoint_request.retries = 1
    result = vaie.get_subbatch_size()

    assert type(result) is int
    assert result < initial_batch_size

    # Run test - 2 retry occured (will catch if a float returned)
    mock_vertexaiendpoint_request.retries = 2
    result = vaie.get_subbatch_size()

    assert type(result) is int
    assert result < initial_batch_size

    # Run test - Enough retries occured that subbatch would be less than 1
    mock_vertexaiendpoint_request.retries = 100
    result = vaie.get_subbatch_size()

    assert type(result) is int
    assert result == 1


@patch("nlp_pipeline.tasks.vertexai_endpoint.VertexAIEndpoint.retry")
@patch("nlp_pipeline.utils.vertexai.VertexAI.run")
def test_batch_query_not_successful_controlled_retry(mock_vertexai_run: Mock, mock_retry: Mock):
    """
    Test certain exceptions can trigger manual retry
    """
    # Setup
    mock_vertexai_run.return_value = (False, exceptions.DeadlineExceeded)

    initial_batch_size = 10
    settings = {
        "name": "Test NER",
        "endpoint": Endpoint.named_entity_recognition,
        "queue": "named-entity-recognition",
        "endpoint_batch_size": initial_batch_size,
        "validation": {
            "payload": False,
            "response": False,
            "batch_input": False,
            "batch_output": False,
            "nuke_if_no_payload": False,
        },
        "models": {
            "task_input": None,
            "task_output": None,
            "endpoint_payload": None,
            "endpoint_response": None,
        },
    }

    vaie = VertexAIEndpoint(settings)

    payloads = [[]]

    # Run test
    vaie.batch_query(payloads)

    # Test outcomes are expected
    assert mock_retry.call_count == 1


@patch("nlp_pipeline.tasks.vertexai_endpoint.publish_to_queue")
@patch("nlp_pipeline.tasks.vertexai_endpoint.VertexAIEndpoint.retry", side_effect=MaxRetriesExceededError())
@patch("nlp_pipeline.utils.vertexai.VertexAI.run")
def test_batch_query_max_retries_exceeded(mock_vertexai_run: Mock, mock_retry: Mock, mock_publish_to_queue: Mock):
    """
    Test certain exceptions can trigger manual retry
    """
    # Setup
    mock_vertexai_run.return_value = (False, exceptions.DeadlineExceeded)
    mock_publish_to_queue.return_value = None

    initial_batch_size = 10
    settings = {
        "name": "Test NER",
        "endpoint": Endpoint.named_entity_recognition,
        "queue": "named-entity-recognition",
        "error_queue": NAMED_ENTITY_RECOGNITION_ERROR_QUEUE_NAME,
        "endpoint_batch_size": initial_batch_size,
        "validation": {
            "payload": False,
            "response": False,
            "batch_input": False,
            "batch_output": False,
            "nuke_if_no_payload": False,
        },
        "models": {
            "task_input": None,
            "task_output": None,
            "endpoint_payload": None,
            "endpoint_response": None,
        },
    }

    vaie = VertexAIEndpoint(settings)

    payloads = [[]]

    # Run test
    with pytest.raises(MaxRetriesExceededError):
        vaie.batch_query(payloads)


@patch("nlp_pipeline.tasks.vertexai_endpoint.VertexAIEndpoint.retry")
def test_batch_query_no_endpoint(mock_retry):
    """
    Test behaviour of end point not existing
    """
    # Setup
    initial_batch_size = 1

    settings = {
        "name": "Test NER",
        "endpoint": Endpoint.named_entity_recognition.value,
        "queue": "named-entity-recognition",
        "endpoint_batch_size": initial_batch_size,
        "validation": {
            "payload": False,
            "response": False,
            "batch_input": False,
            "batch_output": False,
            "nuke_if_no_payload": False,
        },
        "models": {
            "task_input": None,
            "task_output": None,
            "endpoint_payload": None,
            "endpoint_response": None,
        },
    }
    vaie = VertexAIEndpoint(settings)
    # TODO: refactor this mess
    vaie.vertexai.client = None
    fake_endpoint = "929462557477958368"
    vaie.vertexai.endpoint_id = fake_endpoint

    payloads = [[]]

    # Run test
    with pytest.raises(EndpointDoesNotExistError):
        vaie.batch_query(payloads)

    assert mock_retry.call_count == 0
