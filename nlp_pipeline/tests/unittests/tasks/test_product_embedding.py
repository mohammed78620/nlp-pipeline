from copy import deepcopy
from typing import List

import pytest
from celery.exceptions import Ignore

from nlp_pipeline.tasks.product_embedding import ProductEmbedding


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
def products_3():
    products = [
        "Google Ads",
        "Gmail",
        "Google Drive",
    ]
    return products


@pytest.fixture
def product_embedding_3():
    embedding_length = 768
    product_embedding = {
        "Google Ads": {
            "embedding_length": embedding_length,
        },
        "Gmail": {
            "embedding_length": embedding_length,
        },
        "Google Drive": {
            "embedding_length": embedding_length,
        },
    }
    return True, product_embedding


@pytest.fixture
def article_with_products_1(basic_article, products_1) -> List:
    """ """
    basic_article = deepcopy(basic_article)
    basic_article["id"] = "article_1"
    basic_article["text"] = "Samsung is supplying Facebook with pencils."
    basic_article["pre_segmented_text"] = ["Samsung is supplying Facebook with pencils."]
    basic_article["products"] = products_1

    return basic_article


@pytest.fixture
def article_with_products_3(basic_article, products_3) -> List:
    """ """
    basic_article = deepcopy(basic_article)
    basic_article["id"] = "article_3"
    basic_article["text"] = "Samsung is supplying Facebook with pencils."
    basic_article["pre_segmented_text"] = ["Samsung is supplying Facebook with pencils."]
    basic_article["products"] = products_3

    return basic_article


@pytest.fixture
def article_batch_with_products_1(article_with_products_1):
    """
    batch: 1 article with 1 product.
    """
    data = {
        "batch_id": "2",
        "version": "1.0.0",
        "source": "Directory Reader",
        "created_on": "2022-09-02",
        "source_type": "website",
        "articles": [article_with_products_1],
    }
    return data


@pytest.fixture
def article_batch_with_products_3(article_with_products_3):
    """
    batch: 1 article with 3 product.
    """
    data = {
        "batch_id": "2",
        "version": "1.0.0",
        "source": "Directory Reader",
        "created_on": "2022-09-02",
        "source_type": "website",
        "articles": [article_with_products_3],
    }
    return data


@pytest.mark.parametrize(
    "products_fixture, expected_fixture",
    [
        (
            "products_1",
            "product_embedding_1",
        ),
        (
            "products_3",
            "product_embedding_3",
        ),
    ],
)
def test_embed(products_fixture, expected_fixture, request):
    # fetch fixture
    products = request.getfixturevalue(products_fixture)
    expected_success, expected_embeddings = request.getfixturevalue(expected_fixture)

    task = ProductEmbedding()
    success, result = task.embed(products)
    assert len(result) == len(expected_embeddings)
    assert success == expected_success
    assert result.keys() == expected_embeddings.keys()
    for (result_key, result_value), (expected_key, expected_value) in zip(result.items(), expected_embeddings.items()):
        assert result_key == expected_key
        assert len(result_value["embedding"]) == expected_value["embedding_length"]


@pytest.mark.parametrize(
    "batch_fixture, expected_fixture",
    [
        (
            "article_batch_with_products_1",
            "product_embedding_1",
        ),
        (
            "article_batch_with_products_3",
            "product_embedding_3",
        ),
    ],
)
def test_run(batch_fixture, expected_fixture, request):
    # fetch fixture
    batch = request.getfixturevalue(batch_fixture)
    _, expected_embeddings = request.getfixturevalue(expected_fixture)

    result = ProductEmbedding().run(batch)
    result_article = result["articles"][0]

    for (result_key, result_value), (expected_key, expected_value) in zip(
        result_article["products_embeddings"].items(), expected_embeddings.items()
    ):
        assert result_key == expected_key
        assert len(result_value["embedding"]) == expected_value["embedding_length"]


@pytest.fixture
def article_batch_with_no_products(basic_article):
    """
    batch: 1 article with 0 products.
    """
    data = {
        "batch_id": "2",
        "version": "1.0.0",
        "source": "Directory Reader",
        "created_on": "2022-09-02",
        "source_type": "website",
        "articles": [basic_article],
    }
    return data


def test_invalid_batch(article_batch_with_no_products):
    with pytest.raises(Ignore):
        ProductEmbedding().run(article_batch_with_no_products)
