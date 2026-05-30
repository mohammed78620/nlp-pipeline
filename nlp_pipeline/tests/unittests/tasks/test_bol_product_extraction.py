import pytest

from nlp_pipeline.schema.directory_reader_bol_product_extraction import BOLProductPrecleanedArticle
from nlp_pipeline.tasks.bol_product_extraction import BolProductExtraction


@pytest.fixture
def bol_product_precleaned_article():
    process = {
        "name": "Unit Test BOL Product Extraction",
        "pipeline_version": "x.x.x",
        "schema_version": "1.0.0",
        "created_on": "2024-08-08T00:00:00.000Z",
        "batch_id": "000001",
        "prompts": {
            "text_cleaning_prompt": "Text for a super smart cleaning prompt.",
        },
        "intermediary_texts": {
            "text_cleaning": "35 nuts",
        },
        "llm_model": "text-bison@001",
    }

    article = {
        "supplier_vid": "test-vid-001",
        "source_type": "bol_evidence",
        "source": "test-source-001",
        "text": "35 nuts",
        "llm_cleaned_text": "35 NUTS",
        "evidence_date": "2024-01-01T00:00:00.000Z",
        "processes": [process],
    }

    BOLProductPrecleanedArticle.model_validate(article)
    return article


class TestBolProductExtraction:
    @pytest.mark.parametrize(
        "products, block_terms, expected",
        [
            (None, ["BANANA"], []),
            ([], [], []),
            (["UNKNOWN"], [], []),
            (["nuts "], [], ["NUTS"]),
            (["UNKNOWN"], ["UNKNOWN"], []),
            (["UNKNOWN", "nuts"], ["UNKNOWN"], ["NUTS"]),
            (["UNKNOWN", "NUTS"], ["UNKNOWN", "nuts"], []),
            (["Bananas", "BANANAS", "bananas"], [], ["BANANAS"]),
            (["cccc", "bbbbb", "bbbbb", "aaaa", "dd"], [], ["AAAA", "BBBBB", "CCCC"]),
        ],
    )
    def test_clean_products(self, products, block_terms, expected):
        result = BolProductExtraction(block_terms=block_terms).clean_products(products)
        assert result == expected

    @pytest.mark.parametrize(
        "product_str, expected",
        [
            (None, None),
            ("", None),
            ("product", ["product"]),
            ("product_1, product_2", ["product_1", "product_2"]),
            ("product_1,Product_2", ["product_1", "Product_2"]),
        ],
    )
    def test_format_products(self, product_str, expected):
        result = BolProductExtraction().format_products(product_str)
        assert result == expected

    @pytest.mark.parametrize(
        "text, base_prompt, expected",
        [
            ("foo", "bar:", "bar: foo"),
            ("foo", "bar: ", "bar: foo"),
            ("foo", "bar ", "bar foo"),
        ],
    )
    def test_form_query(self, text, base_prompt, expected):
        task = BolProductExtraction(base_prompt=base_prompt)

        result = task.form_query(text)
        assert result == expected

        # check 2nd time to ensure base prompt isn't mangled
        result = task.form_query(text)
        assert result == expected

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("Screwdrivers, wooden spoon", ["SCREWDRIVERS", "WOODEN SPOON"]),
            ("Boxes of fish", ["BOXES OF FISH"]),
            ("Unknown thing, Boxes of fish", ["BOXES OF FISH"]),
            ("unknown", None),
        ],
    )
    def test_perform_query(self, text, expected):
        result = BolProductExtraction().perform_query(text)
        if expected is None:
            assert result is None
        else:
            assert result == expected

    def test_update_record(self, bol_product_precleaned_article):
        result = BolProductExtraction().update_record(bol_product_precleaned_article, ["Test Product"])
        assert result is not None

    def test_run(self, bol_product_precleaned_article):
        result = BolProductExtraction().run([bol_product_precleaned_article])
        assert len(result) == 1
