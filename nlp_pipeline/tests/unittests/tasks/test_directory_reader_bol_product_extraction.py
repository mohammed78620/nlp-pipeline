import pytest

from nlp_pipeline.schema.bol_product_embedding import BOLProductEmbeddingArticle
from nlp_pipeline.schema.directory_reader_bol_product_embedding import DRBOLProductEmbeddingArticle
from nlp_pipeline.schema.directory_reader_bol_product_extraction.input_1_0_0 import BOLProductDescription
from nlp_pipeline.schema.directory_reader_bol_product_extraction.output_1_0_0 import BOLProductArticle
from nlp_pipeline.tasks.bol_product_embedding import BolProductEmbedding
from nlp_pipeline.tasks.bol_product_extraction import BolProductExtraction
from nlp_pipeline.tasks.bol_product_extraction_precleaning import BolProductExtractionPrecleaning
from nlp_pipeline.tasks.bol_product_publish import BolProductPublish
from nlp_pipeline.tasks.directory_reader_bol_product_embedding import DirectoryReaderBolProductEmbedding
from nlp_pipeline.tasks.directory_reader_bol_product_extraction import (
    BatchTracker,
    DirectoryReaderBolProductExtraction,
)


@pytest.fixture
def bol_product_description_01():
    data = {
        "supplier_vid": "sample-vid-001",
        "source_type": "bol_evidence",
        "source": "bol-sample-bol-id",
        "text": "Screwdrivers, 12kg of bolts",
        "evidence_date": "2024-01-01T00:00:00.000Z",
    }
    BOLProductDescription.model_validate(data)
    return data


def test_semi_run_pipeline(bol_product_description_01):
    """
    Test passing an article through BOL Product Extraction (bypassing file usage)
    and feed result to BOL Product Embedding in a similar way.
    """
    # Extraction
    # setup
    batch_info = BatchTracker()
    batch_info.compressed_name = "compressed_name"
    batch_info.original_file_path = "original_file_path"

    data = bol_product_description_01

    # semi run DR
    result = DirectoryReaderBolProductExtraction().process_article(proto_article=data, batch_info=batch_info)
    assert result is not None

    # run precleaning
    data = [result.model_dump(by_alias=True)]
    result = BolProductExtractionPrecleaning().run(data)
    assert len(result) == 1

    # run extraction
    result = BolProductExtraction().run(result)
    assert len(result) == 1

    # Embedding
    # setup
    batch_info = BatchTracker()
    batch_info.compressed_name = "compressed_name"
    batch_info.original_file_path = "original_file_path"

    result = DirectoryReaderBolProductEmbedding().process_article(result[0], batch_info)
    assert result is not None

    result = BolProductEmbedding().process_article(result)
    assert result is not None
    BOLProductEmbeddingArticle.model_validate(result)

    result = BolProductPublish().process_article(result, dry_run=True)
    assert result is not None
    DRBOLProductEmbeddingArticle.model_validate(result)


class TestDirectoryReaderBolProductExtraction:
    def test_process_article(self, bol_product_description_01):
        # setup
        batch_info = BatchTracker()
        batch_info.compressed_name = "compressed_name"
        batch_info.original_file_path = "original_file_path"

        data = bol_product_description_01

        # run
        result = DirectoryReaderBolProductExtraction().process_article(proto_article=data, batch_info=batch_info)

        # examine
        assert result is not None
        assert isinstance(result, BOLProductArticle)
