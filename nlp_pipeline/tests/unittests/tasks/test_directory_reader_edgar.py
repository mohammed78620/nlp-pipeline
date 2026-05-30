import pytest

from nlp_pipeline.schema.input.edgar import SecFiling
from nlp_pipeline.tasks.directory_reader_edgar import (
    LSH_SEED,
    MIN_JACCARD_DR,
    DirectoryReaderEdgar,
    LSHFingerprintStore,
)


@pytest.fixture
def sample_edgar():
    data_dir = "nlp_pipeline/tests/data/edgar/"
    filename = f"{data_dir}edgar-1_0_1-trimmed_sample.jsonl"

    articles = []
    with open(filename, "r", encoding="utf-8") as fp:
        for line in fp:
            edgar_article = SecFiling.parse_raw(line)
            articles.append(edgar_article)
    yield articles


def test_process_article(sample_edgar):
    article_text = sample_edgar[0]
    file_name = "file_name.jsonl"
    compressed_name = "compressed_name.tar"

    result = DirectoryReaderEdgar().process_article(article_text, file_name, compressed_name, fingerprintstore=None)

    assert result is not None
    assert "<html" in result.html
    assert "<html" not in result.text


def test_process_article_with_fingerprintstore(sample_edgar):
    article_text = sample_edgar[0]
    file_name = "file_name.jsonl"
    compressed_name = "compressed_name.tar"

    fingerprintstore = LSHFingerprintStore(seed=LSH_SEED, min_jaccard=MIN_JACCARD_DR)

    result = DirectoryReaderEdgar().process_article(
        article_text, file_name, compressed_name, fingerprintstore=fingerprintstore
    )

    assert result is not None
    assert "<html" in result.html
    assert "<html" not in result.text

    result = DirectoryReaderEdgar().process_article(
        article_text, file_name, compressed_name, fingerprintstore=fingerprintstore
    )

    assert result is None
