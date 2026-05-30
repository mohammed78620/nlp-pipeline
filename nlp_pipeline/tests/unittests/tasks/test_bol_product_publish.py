from copy import deepcopy
from typing import Dict
from unittest.mock import patch

import pytest
from sqlalchemy.exc import DatabaseError

from nlp_pipeline.exceptions.postgres import DeadlockError
from nlp_pipeline.tasks.bol_product_embedding import BolProductEmbedding
from nlp_pipeline.tasks.bol_product_publish import BolProductPublish


@pytest.fixture
def mock_session():
    with patch("nlp_pipeline.db.Session") as mock_session:
        mock_session = mock_session.return_value
        yield mock_session


def preprocess(batch):
    # process batch to point it can be used by task
    bolproductembedded = BolProductEmbedding().run(batch)
    return bolproductembedded


@pytest.fixture
def products_1():
    products = ["Google products and services"]
    return products


@pytest.fixture
def product_embedding_1():
    embedding_length = 768
    product_embedding = {
        "Google products and services": {
            "embedding_length": embedding_length,
        },
    }
    return True, product_embedding


@pytest.fixture
def bol_products_1(products_1) -> Dict:
    """ """
    basic_article = {}
    basic_article["id"] = "article_1"
    basic_article["supplier_vid"] = "example-vid"
    basic_article["source"] = "bol_id_1"
    basic_article["source_type"] = "bol_evidence"
    basic_article["text"] = "this text contains Google products and services"
    basic_article["evidence_date"] = "2024-03-23T21:35:48.664921"
    basic_article["processing_date"] = "2024-05-21T21:35:48.664921"
    basic_article["metadata"] = {
        "llm_extracted_products": products_1,
        "llm_model": "nlp-pipeline-test",
        "input_texts": {"cleaning_input_text": "test", "product_extraction_text": "test"},
        "prompts": {"cleaning_prompt": "test", "product_extraction_prompt": "test"},
    }
    return basic_article


@pytest.fixture
def bol_products_batch_1(bol_products_1):
    """
    batch: 1 article with 1 product.
    """
    data = {
        "batch_id": "2",
        "version": "1.0.0",
        "source": "Directory Reader",
        "source_file": "unit_test_not_real.txt",
        "created_on": "2022-09-02",
        "source_type": "website",
        "articles": [bol_products_1],
    }
    data = preprocess(data)
    return data


@pytest.mark.parametrize(
    "input_fixture, expected_value",
    [
        (
            "bol_products_1",
            "example-vid",
        ),
    ],
)
def test_get_vid(input_fixture, expected_value, request):
    article = request.getfixturevalue(input_fixture)
    task = BolProductPublish()

    result_vid = task.publisher.get_vid(article)

    assert result_vid == expected_value


def test_run(bol_products_batch_1, test_db):
    article = bol_products_batch_1["articles"][0]
    vid = article["supplier_vid"]
    product = article["metadata"]["llm_extracted_products"][0]

    task = BolProductPublish()

    # pre test
    with task.publisher.session_scope() as session:
        pre_test = task.publisher._get_existing_product(session, vid, product)
        assert pre_test is None

    result = task.run(bol_products_batch_1)

    assert result == bol_products_batch_1

    with task.publisher.session_scope() as session:
        post_test = task.publisher._get_existing_product(session, vid, product)
        assert post_test is not None


def test_run_duplicate_bol_product(bol_products_batch_1, test_db):
    article = bol_products_batch_1["articles"][0]
    vid = article["supplier_vid"]
    product = article["metadata"]["llm_extracted_products"][0]

    task = BolProductPublish()

    # duplicate article
    bol_product = deepcopy(bol_products_batch_1["articles"][0])
    bol_products_batch_1["articles"].append(bol_product)

    # pre test
    with task.publisher.session_scope() as session:
        pre_test = task.publisher._get_existing_product(session, vid, product)
        assert pre_test is None

    result = task.run(bol_products_batch_1)

    assert result == bol_products_batch_1

    with task.publisher.session_scope() as session:
        post_test = task.publisher._get_existing_product(session, vid, product)
        assert post_test is not None


def test_raise_deadlock_exception_on_max_retries(mock_session, bol_products_batch_1, test_db):

    mock_session.commit.side_effect = DatabaseError(None, None, "deadlock detected")

    task = BolProductPublish()
    bol_product_with_embeddings = bol_products_batch_1["articles"][0]
    data = task.publisher.format_data(bol_product_with_embeddings)

    with patch("time.sleep", return_value=None) as mocked_sleep:
        with pytest.raises(DeadlockError) as exe_info:
            task.publisher.publish(data)

        # can potentially fail when stepping through debugger
        assert mocked_sleep.call_count == 4

    assert "deadlock detected" in str(exe_info.value)
