from typing import List

import pytest

from nlp_pipeline.tasks import BolProductEmbedding


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
def bol_products_1(products_1) -> List:
    """ """
    basic_article = {}
    basic_article["id"] = "article_1"
    basic_article["supplier_vid"] = "vid_1"
    basic_article["source"] = "bol_id_1"
    basic_article["source_type"] = "bol_evidence"
    basic_article["text"] = "this text contains Google products and services"
    basic_article["evidence_date"] = "vid_1"
    basic_article["processing_date"] = "vid_1"
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
    return data


@pytest.mark.parametrize(
    "batch_fixture, expected_fixture",
    [
        (
            "bol_products_batch_1",
            "product_embedding_1",
        ),
    ],
)
def test_run(batch_fixture, expected_fixture, request):
    # fetch fixture
    batch = request.getfixturevalue(batch_fixture)
    _, expected_embeddings = request.getfixturevalue(expected_fixture)

    result = BolProductEmbedding().run(batch)
    result_article = result["articles"][0]

    for (result_key, result_value), (expected_key, expected_value) in zip(
        result_article["products_embeddings"].items(), expected_embeddings.items()
    ):
        assert result_key == expected_key
        assert len(result_value["embedding"]) == expected_value["embedding_length"]
