from copy import deepcopy
from typing import List

import pytest

from nlp_pipeline.constants import SUPABASE
from nlp_pipeline.settings import SUPABASE_SERVICE_KEY, ENV
from nlp_pipeline.tasks.product_embedding import ProductEmbedding
from nlp_pipeline.tasks.publish_product_supabase import PublishProduct, SupabasePublisher

# test cases are skipped because PublishProduct is not used by any pipeline
if pytest.__version__ < "3.0.0":
    pytest.skip()
else:
    pytestmark = pytest.mark.skip


@pytest.fixture
def article_homepage_evidence():
    article = {
        "metadata": {
            "url": "the_source",
            "extra_header_info": {"vid": "vid-001"},
            "product_embedding": {"model_name": "the_model"},
            "product_extraction": {"prompt_template": "the_prompt_template"},
        },
        "source_type": "product",
        "products_embeddings": {"product-01": {"embedding": "the_embedding"}},
        "text": "the_text",
    }
    return article


@pytest.fixture
def article_ik_global_evidence():
    article = {
        "metadata": {
            "url": "",
            "extra_header_info": {"vid": "vid-002"},
            "product_embedding": {"model_name": "the_model"},
            "product_extraction": {"prompt_template": "the_prompt_template"},
        },
        "source_type": "ik_global_evidence",
        "source": "the_source",
        "products_embeddings": {"product-01": {"embedding": "the_embedding"}},
        "text": "the_text",
    }
    return article


@pytest.fixture
def article_ik_us_evidence():
    article = {
        "metadata": {
            "url": "",
            "extra_header_info": {"vid": "vid-003"},
            "product_embedding": {"model_name": "the_model"},
            "product_extraction": {"prompt_template": "the_prompt_template"},
        },
        "source_type": "ik_us_evidence",
        "source": "the_source",
        "products_embeddings": {"product-01": {"embedding": "the_embedding"}},
        "text": "the_text",
    }
    return article


class TestSupabasePublisher:
    @pytest.mark.parametrize(
        "article_fixture, expected_source, expected_source_type",
        [
            ("article_homepage_evidence", "the_source", "product"),
            ("article_ik_us_evidence", "the_source", "ik_us_evidence"),
            ("article_ik_global_evidence", "the_source", "ik_global_evidence"),
        ],
    )
    def test_format_data(self, article_fixture, expected_source, expected_source_type, request):
        # fetch fixture
        article = request.getfixturevalue(article_fixture)

        sb_details = getattr(SUPABASE, ENV.value).value
        table = sb_details["pe_table_name"]
        url = sb_details["url"]
        sb_pub = SupabasePublisher(url=url, service_key=SUPABASE_SERVICE_KEY, table_name=table)

        result = sb_pub.format_data(article)

        # expecting 1 product in the article so only checking index 0 of the result
        assert result[0]["product_source"] == expected_source
        assert result[0]["product_source_type"] == expected_source_type


def preprocess(batch):
    # process batch to point it can be used by task
    productembedded = ProductEmbedding().run(batch)
    return productembedded


@pytest.fixture
def products_1():
    products = ["Google products and services"]
    return products


@pytest.fixture
def article_with_products_1(basic_article, products_1) -> List:
    basic_article = deepcopy(basic_article)
    basic_article["id"] = "article_1"
    basic_article["text"] = "Samsung is supplying Facebook with pencils."
    basic_article["pre_segmented_text"] = ["Samsung is supplying Facebook with pencils."]
    basic_article["metadata"]["extra_header_info"] = {"vid": "example-vid"}
    basic_article["metadata"]["product_extraction"] = {
        "prompt_template": "List as bullet points products and services in the following: '{}'"
    }
    basic_article["products"] = products_1

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
    data = preprocess(data)
    return data


@pytest.mark.parametrize(
    "input_fixture, expected_value",
    [
        (
            "article_with_products_1",
            "example-vid",
        ),
    ],
)
def test_get_vid(input_fixture, expected_value, request):
    article = request.getfixturevalue(input_fixture)
    task = PublishProduct()

    result_vid = task.publisher.get_vid(article)

    assert result_vid == expected_value


def test_run(article_batch_with_products_1, handle_pe_supabase_table):
    result = PublishProduct().run(article_batch_with_products_1)

    assert result == article_batch_with_products_1
