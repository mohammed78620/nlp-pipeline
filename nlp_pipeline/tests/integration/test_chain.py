import datetime
import os
import time
from typing import Any, Optional

import pytest
from google.cloud import storage

from nlp_pipeline.tasks.directory_reader import DirectoryReader
from nlp_pipeline.tasks.directory_reader_bigtable_lexisnexis import DirectoryReaderBigtableLexisnexis
from nlp_pipeline.tasks.directory_reader_bigtable_webz import DirectoryReaderBigtableWebz
from nlp_pipeline.tasks.directory_reader_bol_evidence_descriptions import DirectoryReaderBolEvidenceDescriptions
from nlp_pipeline.tasks.directory_reader_bol_product_embedding import DirectoryReaderBolProductEmbedding
from nlp_pipeline.tasks.directory_reader_bol_product_extraction import DirectoryReaderBolProductExtraction
from nlp_pipeline.tasks.directory_reader_common_crawl import DirectoryReaderCommonCrawl
from nlp_pipeline.tasks.directory_reader_company_mentions import DirectoryReaderCompanyMentions
from nlp_pipeline.tasks.directory_reader_edgar import DirectoryReaderEdgar
from nlp_pipeline.tasks.directory_reader_homepage import DirectoryReaderHomepage
from nlp_pipeline.tasks.directory_reader_lexis_nexis import DirectoryReaderLexisNexis

SOURCE_BUCKET = "dev-testing-versed-ai"
SOURCE_PATH = "test_nlp_dir/source_test_data/"
SOURCE_TEST_DATA_DIR = "nlp_pipeline/tests/data/integration/"  # relative path to local test data


def wait_for_blobs(bucket: str, path: str, wait_for: int = 180, poll_freq: int = 5) -> Optional[Any]:
    """
    For processes that take a noteable amount of time to produce any
    output in a bucket this allows a delay by polling for a max amount of time.

    If None, no blobs in path of bucket so no may be something didn't work
    or took a lot longer than expected.

    Args:
        bucket (str): The bucket to look in.
        path (str): The path in the bucket to look for blobs.
        wait_for (int, optional): Max time to wait in seconds.
        poll_freq (int, optional): How frequently (in seconds) to check for blobs.

    Returns:
        Optional[Any]: List of blobs if any were found.
    """
    start = datetime.datetime.now()
    checking_for = 0

    if wait_for < checking_for:
        return

    while checking_for < wait_for:
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket)
        blobs = list(bucket.list_blobs(prefix=path))

        if blobs:
            return blobs

        time.sleep(poll_freq)
        checking_for = (datetime.datetime.now() - start).seconds


@pytest.fixture()
def gcs_source_dir() -> str:
    """
    GCS bucket path to use for testing directory reader

    Returns:
        str: The path in the GCS bucket.
    """

    #
    # Ensure test data exists in bucket

    # determine local data
    test_files = []

    dir_contents = os.listdir(SOURCE_TEST_DATA_DIR)
    for name in dir_contents:
        file_path = f"{SOURCE_TEST_DATA_DIR}{name}"
        item = (file_path, name)

        if os.path.isfile(item[0]):
            test_files.append(item)

    # check local data is in bucket. Upload any that are missing
    storage_client = storage.Client()
    bucket = storage_client.bucket(SOURCE_BUCKET)
    for file_path, filename in test_files:
        prospect_remote_file_path = f"{SOURCE_PATH}{filename}"

        blob = bucket.blob(prospect_remote_file_path)
        if not blob.exists():
            blob.upload_from_filename(file_path)

    yield SOURCE_PATH


@pytest.fixture
def batch_1(gcs_source_dir):
    """
    Path to test data 1 in Test gcs bucket.
    """
    remote_file_path = f"{gcs_source_dir}b97f8a8528527787a2578db79355581c_trimmed.tar"
    return remote_file_path


@pytest.mark.parametrize(
    "batch_fixture_1",
    ["batch_1"],
)
def test_directory_reader(batch_fixture_1, handle_crawled_publish_location, request):
    # Setup
    destination_bucket, destination_path, _ = handle_crawled_publish_location
    batch_location = request.getfixturevalue(batch_fixture_1)
    batch_size = 2

    # Run
    DirectoryReader().run(destination_bucket, batch_location, batch_size)

    # Wait and Poll
    blobs = wait_for_blobs(destination_bucket, destination_path)

    # Test
    assert blobs is not None
    assert len(blobs) > 0


@pytest.fixture
def batch_2(gcs_source_dir):
    """
    Path to test data 1 in Test gcs bucket.
    """
    remote_file_path = f"{gcs_source_dir}lexis_nexis_35c165c6-1293-4a65-a0c6-d0954fa3bdcf.tar.bz2"

    return remote_file_path


@pytest.mark.parametrize(
    "batch_fixture_2",
    ["batch_2"],
)
def test_directory_reader_lexis_nexis(batch_fixture_2, handle_lexisnexis_publish_location, request):
    # Setup
    destination_bucket, destination_path, _ = handle_lexisnexis_publish_location
    batch_location = request.getfixturevalue(batch_fixture_2)
    batch_size = 2

    # Run
    DirectoryReaderLexisNexis().run(destination_bucket, batch_location, batch_size)

    # Wait and Poll
    blobs = wait_for_blobs(destination_bucket, destination_path)

    # Test
    assert blobs is not None
    assert len(blobs) > 0


@pytest.fixture
def batch_3(gcs_source_dir):
    """
    Path to test data 3 in Test gcs bucket.
    """
    remote_file_path = f"{gcs_source_dir}d1aa90f80ec1acad2d73ca98e51aea46.tar.bz2"

    return remote_file_path


@pytest.mark.parametrize(
    "batch_fixture_3",
    ["batch_3"],
)
def test_directory_reader_company_mentions(batch_fixture_3, handle_company_mentions_publish_location, request):
    # Setup
    destination_bucket, destination_path, _ = handle_company_mentions_publish_location
    batch_location = request.getfixturevalue(batch_fixture_3)
    batch_size = 2

    # Run
    DirectoryReaderCompanyMentions().run(destination_bucket, batch_location, batch_size)

    # Wait and Poll
    blobs = wait_for_blobs(destination_bucket, destination_path)

    # Test
    assert blobs is not None
    assert len(blobs) > 0


@pytest.fixture
def batch_4(gcs_source_dir):
    """
    Path to test data 4 in Test gcs bucket.
    """
    remote_file_path = f"{gcs_source_dir}test_nlp_dir_source_test_data_1_cc_input.tar.bz2"

    return remote_file_path


@pytest.mark.parametrize(
    "batch_fixture_4",
    ["batch_4"],
)
def test_directory_reader_common_crawl(batch_fixture_4, handle_common_crawl_publish_location, request):
    # Setup
    destination_bucket, destination_path, _ = handle_common_crawl_publish_location
    batch_location = request.getfixturevalue(batch_fixture_4)
    batch_size = 2

    # Run
    DirectoryReaderCommonCrawl().run(destination_bucket, batch_location, batch_size)

    # Wait and Poll
    blobs = wait_for_blobs(destination_bucket, destination_path)

    # Test
    assert blobs is not None
    assert len(blobs) > 0


@pytest.fixture
def batch_5(gcs_source_dir):
    """
    Path to test data 4 in Test gcs bucket.
    """
    remote_file_path = f"{gcs_source_dir}sample_homepages-2.tar.bz2"

    return remote_file_path


@pytest.mark.parametrize(
    "batch_fixture_5",
    ["batch_5"],
)
def test_directory_reader_homepages(batch_fixture_5, handle_homepage_publish_location, request, test_db):
    # Setup
    destination_bucket, destination_path, _ = handle_homepage_publish_location
    batch_location = request.getfixturevalue(batch_fixture_5)
    batch_size = 2

    # Run
    DirectoryReaderHomepage().run(destination_bucket, batch_location, batch_size)

    # Wait and Poll
    blobs = wait_for_blobs(destination_bucket, destination_path)

    # Test
    assert blobs is not None
    assert len(blobs) > 0


@pytest.fixture
def batch_6(gcs_source_dir):
    """
    Path to test data 6 in Test gcs bucket.
    """
    remote_file_path = f"{gcs_source_dir}1_bol_evidence_description_sample.tar.gz"

    return remote_file_path


@pytest.mark.parametrize(
    "batch_fixture_6",
    ["batch_6"],
)
def test_directory_reader_bol_evidence_descriptions(
    batch_fixture_6, handle_homepage_publish_location, request, test_db
):
    # Setup
    destination_bucket, destination_path, _ = handle_homepage_publish_location
    batch_location = request.getfixturevalue(batch_fixture_6)
    batch_size = 2

    # Run
    DirectoryReaderBolEvidenceDescriptions().run(destination_bucket, batch_location, batch_size)

    # Wait and Poll
    blobs = wait_for_blobs(destination_bucket, destination_path)

    # Test
    assert blobs is not None
    assert len(blobs) > 0


@pytest.fixture
def batch_7(gcs_source_dir):
    """
    Path to test data 7 in Test gcs bucket.
    """
    remote_file_path = f"{gcs_source_dir}edgar_sample-1_0_1.tar.gz"

    return remote_file_path


@pytest.mark.parametrize(
    "batch_fixture_7",
    ["batch_7"],
)
def test_directory_reader_edgar(batch_fixture_7, handle_edgar_publish_location, request):
    # Setup
    destination_bucket, destination_path, _ = handle_edgar_publish_location
    batch_location = request.getfixturevalue(batch_fixture_7)
    batch_size = 2

    # Run
    DirectoryReaderEdgar().run(destination_bucket, batch_location, batch_size)

    # Wait and Poll
    blobs = wait_for_blobs(destination_bucket, destination_path, wait_for=400)

    # Test
    assert blobs is not None
    assert len(blobs) > 0


@pytest.fixture
def batch_8(gcs_source_dir):
    """
    Path to test data 8 in Test gcs bucket.
    """
    remote_file_path = f"{gcs_source_dir}bol_product_embedding_pipeline_input_1.tar.gz"

    return remote_file_path


@pytest.mark.parametrize(
    "batch_fixture_8",
    ["batch_8"],
)
def test_directory_reader_bol_product_embedding(
    batch_fixture_8, handle_bol_product_embedding_publish_location, request, test_db
):
    # Setup
    destination_bucket, destination_path, _ = handle_bol_product_embedding_publish_location
    batch_location = request.getfixturevalue(batch_fixture_8)
    batch_size = 2

    # Run
    DirectoryReaderBolProductEmbedding().run(destination_bucket, batch_location, batch_size)

    # Wait and Poll
    blobs = wait_for_blobs(destination_bucket, destination_path)

    # Test
    assert blobs is not None
    assert len(blobs) > 0


@pytest.fixture
def batch_9(gcs_source_dir):
    """
    Path to test Directory Reader BOL Product Extraction in Test bucket.
    """
    remote_file_path = f"{gcs_source_dir}bol_product_extraction_pipeline_input_1.tar.gz"

    return remote_file_path


@pytest.mark.parametrize(
    "batch_fixture_9",
    ["batch_9"],
)
def test_directory_reader_bol_product_extraction(
    batch_fixture_9, handle_bol_product_extraction_publish_location, request
):
    # Setup
    destination_bucket, destination_path, _ = handle_bol_product_extraction_publish_location
    batch_location = request.getfixturevalue(batch_fixture_9)
    batch_size = 2

    # Run
    DirectoryReaderBolProductExtraction().run(destination_bucket, batch_location, batch_size)

    # Wait and Poll
    blobs = wait_for_blobs(destination_bucket, destination_path)

    # Test
    assert blobs is not None
    assert len(blobs) > 0


@pytest.fixture
def batch_10(gcs_source_dir):
    """
    Path to test Directory Reader BOL Product Extraction in Test bucket.
    """
    remote_file_path = f"{gcs_source_dir}lexisnexis_bigtable_data.jsonl.tar.gz"

    return remote_file_path


@pytest.mark.parametrize(
    "batch_fixture_10",
    ["batch_10"],
)
def test_directory_reader_bigtable_lexisnexis(batch_fixture_10, handle_bigtable_lexisnexis_publish_location, request):
    # Setup
    destination_bucket, destination_path, _ = handle_bigtable_lexisnexis_publish_location
    batch_location = request.getfixturevalue(batch_fixture_10)
    batch_size = 2

    # Run
    DirectoryReaderBigtableLexisnexis().run(destination_bucket, batch_location, batch_size)

    # Wait and Poll
    blobs = wait_for_blobs(destination_bucket, destination_path)

    # Test
    assert blobs is not None
    assert len(blobs) > 0


@pytest.fixture
def batch_11(gcs_source_dir):
    """
    Path to test Directory Reader BOL Product Extraction in Test bucket.
    """
    remote_file_path = f"{gcs_source_dir}webz_sample_1.tar.gz"

    return remote_file_path


@pytest.mark.parametrize(
    "batch_fixture_11",
    ["batch_11"],
)
def test_directory_reader_bigtable_webz_nexis(batch_fixture_11, handle_bigtable_webz_publish_location, request):
    # Setup
    destination_bucket, destination_path, _ = handle_bigtable_webz_publish_location
    batch_location = request.getfixturevalue(batch_fixture_11)
    batch_size = 2

    # Run
    DirectoryReaderBigtableWebz().run(destination_bucket, batch_location, batch_size)

    # Wait and Poll
    blobs = wait_for_blobs(destination_bucket, destination_path)

    # Test
    assert blobs is not None
    assert len(blobs) > 0
