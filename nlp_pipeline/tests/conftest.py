from copy import deepcopy
from typing import Dict, Tuple

import pytest
from google.cloud import storage
from supabase import Client

from nlp_pipeline.constants import SUPABASE, PipelineOutputs
from nlp_pipeline.db import engine
from nlp_pipeline.models.base import Base
from nlp_pipeline.settings import CELERY_BROKER_URL, SUPABASE_SERVICE_KEY, ENV, Environment

if ENV != Environment.test:
    pytest.exit("Environment isn't configured to be test environment. Check ENV env var.", pytest.ExitCode.USAGE_ERROR)


@pytest.fixture()
def test_db():
    """
    creates tables and deletes tables in test database

    """
    # setup
    Base.metadata.create_all(bind=engine)

    yield

    # teardown
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def celery_config():
    return {"broker_url": CELERY_BROKER_URL}


def teardown(bucket, path):
    """
    Remove all items in the specified location within a GCS bucket.

    Args:
        bucket (str): The name of the GCS bucket.
        prefix (str): The prefix within the bucket to remove items from.
    """
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket)

    blobs = list(bucket.list_blobs(prefix=path))
    for blob in blobs:
        if blob.size > 0:
            blob.delete()


def teardown_pe_supabase_table(supabase_table_name, supabase_url):
    """
    Delete all rows from table in supabase.

    Args:
        supabase_table_name (str): the name of the supabase table.
        supabase_url (str): the url to supabase enviroment.
    """
    supabase: Client = Client(supabase_url, SUPABASE_SERVICE_KEY)
    # TODO: figure out how to clear table better than this mess below.
    supabase.table(supabase_table_name).delete().neq("vid", None).execute()


@pytest.fixture
def handle_pe_supabase_table():
    outputs_config = getattr(SUPABASE, ENV.value).value
    supabase_table = outputs_config["pe_table_name"]
    supabase_url = outputs_config["url"]
    yield supabase_table, supabase_url

    teardown_pe_supabase_table(supabase_table, supabase_url)


def _handle_publish_location(outputs_config):
    destination_bucket = outputs_config["bucket"]
    destination_path = outputs_config["path"]
    destination_region = outputs_config["region"]

    # make sure all results of previous runs are gone
    # may happen if test ends before all results published
    teardown(bucket=destination_bucket, path=destination_path)

    yield destination_bucket, destination_path, destination_region

    # clear up after
    teardown(bucket=destination_bucket, path=destination_path)


@pytest.fixture
def handle_crawled_publish_location() -> Tuple[str, str, str]:

    outputs_config = PipelineOutputs.crawled.value.get_config_from_environment()
    yield from _handle_publish_location(outputs_config)


@pytest.fixture
def handle_lexisnexis_publish_location() -> Tuple[str, str, str]:

    outputs_config = PipelineOutputs.ln.value.get_config_from_environment()
    yield from _handle_publish_location(outputs_config)


@pytest.fixture
def handle_product_publish_location() -> Tuple[str, str, str]:
    outputs_config = PipelineOutputs.product.value.get_config_from_environment()
    yield from _handle_publish_location(outputs_config)


@pytest.fixture
def handle_company_mentions_publish_location() -> Tuple[str, str, str]:
    outputs_config = PipelineOutputs.company_mentions.value.get_config_from_environment()
    yield from _handle_publish_location(outputs_config)


@pytest.fixture
def handle_common_crawl_publish_location() -> Tuple[str, str, str]:
    outputs_config = PipelineOutputs.common_crawl.value.get_config_from_environment()
    yield from _handle_publish_location(outputs_config)


@pytest.fixture
def handle_homepage_publish_location() -> Tuple[str, str, str]:
    outputs_config = PipelineOutputs.product.value.get_config_from_environment()
    yield from _handle_publish_location(outputs_config)


@pytest.fixture
def handle_edgar_publish_location() -> Tuple[str, str, str]:
    outputs_config = PipelineOutputs.edgar.value.get_config_from_environment()
    yield from _handle_publish_location(outputs_config)


@pytest.fixture
def handle_bol_product_embedding_publish_location() -> Tuple[str, str, str]:
    outputs_config = PipelineOutputs.bol_product_embedding.value.get_config_from_environment()
    yield from _handle_publish_location(outputs_config)


@pytest.fixture
def handle_bol_product_extraction_publish_location() -> Tuple[str, str, str, str]:
    outputs_config = PipelineOutputs.bol_product_extraction.value.get_config_from_environment()
    yield from _handle_publish_location(outputs_config)


@pytest.fixture
def handle_bigtable_lexisnexis_publish_location() -> Tuple[str, str, str, str]:
    outputs_config = PipelineOutputs.bigtable_lexisnexis.value.get_config_from_environment()
    yield from _handle_publish_location(outputs_config)


@pytest.fixture
def handle_bigtable_webz_publish_location() -> Tuple[str, str, str, str]:
    outputs_config = PipelineOutputs.bigtable_webz.value.get_config_from_environment()
    yield from _handle_publish_location(outputs_config)


@pytest.fixture
def basic_article() -> Dict:
    """
    Raw article base model
    """
    article = {
        "id": "article_00",
        "html": "some html",
        "text": "some text",
        "pre_segmented_text": ["some text"],
        "original_compressed_filename": "afile_name.tar.gz",
        "original_html_file": "a.html",
        "source_type": "website",
        "metadata": {
            "timestamp": 1,
            "wbm_id": "2",
            "access_epoch": 3,
            "scraper_type": "thing",
            "extra_header_info": {
                "checksum": "437bbe7ceccb3067c4be0acf783a50df",
                "ipaddress": "54.219.186.54",
                "host": "crawler-tf11.versed.ai",
            },
            "host_name": "host",
            "date_guess": "2000",
            "date_acc": "1",
            "url": "http://example.com",
        },
    }
    return article


@pytest.fixture
def articles():
    return [
        {
            "id": "1",
            "html": "<p>This is an article that contains some text. Get some sentences and tokenize them!!</p><p>Lets see how it works. Some numbers 12391 here and some there 12312.</p>",
            "text": "This is an article that contains some text. Get some sentences and tokenize them!! Lets see how it works. Some numbers 12391 here and some there 12312.",
            "pre_segmented_text": [
                "This is an article that contains some text. Get some sentences and tokenize them!!",
                "Lets see how it works. Some numbers 12391 here and some there 12312.",
            ],
            "original_compressed_filename": "afile_name.tar.gz",
            "original_html_file": "a.html",
            "source_type": "website",
            "metadata": {
                "timestamp": 1,
                "wbm_id": "2",
                "access_epoch": 3,
                "scraper_type": "thing",
                "extra_header_info": {
                    "checksum": "437bbe7ceccb3067c4be0acf783a50df",
                    "ipaddress": "54.219.186.54",
                    "host": "crawler-tf11.versed.ai",
                },
                "host_name": "host",
                "date_guess": "2000",
                "date_acc": "1",
                "url": "http://example.com",
            },
        },
        {
            "id": "2",
            "html": "<p>Zara, Paypal and Samsung are the latest international firms to suspend trading in Russia after it invaded Ukraine. The clothes retailer's owner, Inditex, will shut all 502 stores of its eight brands, including Bershka, Stradivarius and Oysho, from Sunday. Payment giant Paypal cited \"violent military aggression in Ukraine\" as the reason to shut down its services.Samsung - Russia's top supplier of smartphones - is suspending shipments over geopolitical developments</p>",
            "text": "Zara, Paypal and Samsung are the latest international firms to suspend trading in Russia after it invaded Ukraine. The clothes retailer's owner, Inditex, will shut all 502 stores of its eight brands, including Bershka, Stradivarius and Oysho, from Sunday. Payment giant Paypal cited \"violent military aggression in Ukraine\" as the reason to shut down its services.Samsung - Russia's top supplier of smartphones - is suspending shipments over geopolitical developments",
            "pre_segmented_text": [
                "Zara, Paypal and Samsung are the latest international firms to suspend trading in Russia after it invaded Ukraine. The clothes retailer's owner, Inditex, will shut all 502 stores of its eight brands, including Bershka, Stradivarius and Oysho, from Sunday. Payment giant Paypal cited \"violent military aggression in Ukraine\" as the reason to shut down its services.Samsung - Russia's top supplier of smartphones - is suspending shipments over geopolitical developments"
            ],
            "original_compressed_filename": "afile_name.tar.gz",
            "original_html_file": "a.html",
            "source_type": "website",
            "metadata": {
                "timestamp": 1,
                "wbm_id": "2",
                "access_epoch": 3,
                "scraper_type": "thing",
                "extra_header_info": {
                    "checksum": "437bbe7ceccb3067c4be0acf783a50df",
                    "ipaddress": "54.219.186.54",
                    "host": "crawler-tf11.versed.ai",
                },
                "host_name": "host",
                "date_guess": "2000",
                "date_acc": "1",
                "url": "http://example.com",
            },
        },
    ]


@pytest.fixture
def raw_html():
    return '<!--{"timestamp": 1615413290, "url": "https://www.circuitnet.com/", "wbm_id": "scrapy_ae250ac2-1278-40cf-8077-409e7273c58c", "access_epoch": 1615413290, "scraper_type": "scrapy", "extra_header_info": "{\\"checksum\\":\\"437bbe7ceccb3067c4be0acf783a50df\\", \\"ipaddress\\":\\"54.219.186.54\\", \\"host\\":\\"crawler-tf11.versed.ai\\"}", "host_name": "circuitnet.com", "redirected_from": null, "date_guess": "None", "date_acc": "Accuracy.NONE"}-->\n<!DOCTYPE html><html><head><!-- head definitions go here --><meta name="description" content="Some metadata!"><meta name="keywords" content="This should contains keywords"></head><body><p>this is a sentence</p><p>this is another sentence</p><span>this is a sentence with a <a href=#>link</a></span></body></html>'


@pytest.fixture
def article_1s0e0r0l(basic_article) -> Tuple[Dict]:
    """
    Raw article: 1 sentence, 0 entities, 0 relations, 0 links
    """
    basic_article = deepcopy(basic_article)
    basic_article["id"] = "article_1s0e0r0l"
    basic_article["text"] = "This sentence has no entities."
    basic_article["pre_segmented_text"] = ["This sentence has no entities."]
    expected = {"sentences": [{"entities": 0, "relations": 0, "links": 0}]}

    return basic_article, expected


@pytest.fixture
def article_1s1e0r0l(basic_article) -> Tuple[Dict]:
    """
    Raw article: 1 sentence, 1 entity, 0 relations, 0 links
    """
    basic_article = deepcopy(basic_article)
    basic_article["id"] = "article_1s1e0r0l"
    basic_article["text"] = "Facebook is an entity"
    basic_article["pre_segmented_text"] = ["Facebook is an entity"]
    expected = {"sentences": [{"entities": 1, "relations": 0, "links": 0}]}

    return basic_article, expected


@pytest.fixture
def article_1s2e0r2l(basic_article) -> Tuple[Dict]:
    """
    Raw article: 1 sentence, 2 entitities, 0 relations, 2 links
    """
    basic_article = deepcopy(basic_article)
    basic_article["id"] = "article_1s2e0r2l"
    basic_article["text"] = "Facebook is an entity and Samsung is an entity too."
    basic_article["pre_segmented_text"] = ["Facebook is an entity and Samsung is an entity too."]
    expected = {"sentences": [{"entities": 2, "relations": 0, "links": 2}]}

    return basic_article, expected


@pytest.fixture
def article_1s2e1r2l_1(basic_article) -> Tuple[Dict]:
    """
    Raw article: 1 sentence, 2 entitities (different), 1 relations, 2 links
    """
    basic_article = deepcopy(basic_article)
    basic_article["id"] = "article_1s2e1r2l_1"
    basic_article["text"] = "Samsung is supplying Facebook with pencils."
    basic_article["pre_segmented_text"] = ["Samsung is supplying Facebook with pencils."]
    expected = {"sentences": [{"entities": 2, "relations": 1, "links": 2}]}

    return basic_article, expected


@pytest.fixture
def article_1s2e1r2l_2(basic_article) -> Tuple[Dict]:
    """
    Raw article: 1 sentence, 2 entitities (same), 1 relations, 2 links
    """
    basic_article = deepcopy(basic_article)
    basic_article["id"] = "article_1s2e1r2l_2"
    basic_article["text"] = "Samsung is supplying Samsung with pencils."
    basic_article["pre_segmented_text"] = ["Samsung is supplying Samsung with pencils."]
    expected = {"sentences": [{"entities": 2, "relations": 1, "links": 2}]}

    return basic_article, expected
