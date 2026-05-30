import pytest

from nlp_pipeline.schema.directory_reader_bol_product_extraction import BOLProductArticle
from nlp_pipeline.tasks.bol_product_extraction_precleaning import BolProductExtractionPrecleaning


@pytest.fixture
def bol_product_article():
    process = {
        "name": "Unit Test BOL Product Extraction",
        "pipeline_version": "x.x.x",
        "schema_version": "1.0.0",
        "created_on": "2024-08-08T00:00:00.000Z",
        "batch_id": "000001",
        "prompts": None,
        "intermediary_texts": None,
        "llm_model": None,
    }

    article = {
        "supplier_vid": "test-vid-001",
        "source_type": "bol_evidence",
        "source": "test-source-001",
        "text": "35 nuts, boxes of fish",
        "evidence_date": "2024-01-01T00:00:00.000Z",
        "processes": [process],
    }

    BOLProductArticle.model_validate(article)
    return article


class TestBolProductExtractionPrecleaning:
    @pytest.mark.parametrize(
        "text, base_prompt, expected",
        [
            ("foo", "bar:", "bar: foo"),
            ("foo", "bar: ", "bar: foo"),
            ("foo", "bar ", "bar foo"),
        ],
    )
    def test_form_query(self, text, base_prompt, expected):
        task = BolProductExtractionPrecleaning(base_prompt=base_prompt)

        result = task.form_query(text)
        assert result == expected

        # check 2nd time to ensure base prompt isn't mangled
        result = task.form_query(text)
        assert result == expected

    @pytest.mark.parametrize(
        "text, strip_terms, expected",
        [
            ("", None, None),
            ("", [], None),
            ("", ["Foo"], None),
            ("Foo", None, "FOO"),
            ("foO", ["Foo"], None),
            ("Foobar", ["Foo"], "BAR"),
            ("test bar test", ["bAr ", " tESt "], None),
            ("test bar test", ["test"], "BAR"),
        ],
    )
    def test_clean_product_description(self, text, strip_terms, expected):
        if strip_terms is None:
            result = BolProductExtractionPrecleaning().clean_product_description(text)
        else:
            result = BolProductExtractionPrecleaning(strip_terms=strip_terms).clean_product_description(text)

        if expected is None:
            assert result is None
        else:
            assert result == expected

    @pytest.mark.parametrize(
        "text, strip_terms, expected, not_expected",
        [
            ("Screwdrivers, bolts", None, ["SCREWDRIVERS", "BOLTS"], None),
            ("1MHO00123, Boxes of fish", None, ["FISH"], None),
            ("Boxes of fish", ["boxes of"], ["FISH"], ["BOXES OF"]),
        ],
    )
    def test_perform_query(self, text, strip_terms, expected, not_expected):
        if strip_terms:
            result = BolProductExtractionPrecleaning(strip_terms=strip_terms).perform_query(text)
        else:
            result = BolProductExtractionPrecleaning().perform_query(text)

        if expected is None:
            assert result is None
        else:
            for item in expected:
                assert item in result

        if not_expected:
            for item in not_expected:
                assert item not in result

    def test_update_record(self, bol_product_article):
        result = BolProductExtractionPrecleaning().update_record(bol_product_article, "TEST PRODUCT")
        assert result is not None

    @pytest.mark.parametrize(
        "text_override, expected",
        [
            ("Screwdrivers, 12kg of bolts", ["SCREWDRIVERS", "BOLTS"]),
            ("1MHO00123, Boxes of fish", ["FISH"]),
            ("52 cannd torpical fruit (HS23412)", ["TROPICAL FRUIT"]),
        ],
    )
    def test_run(self, text_override, expected, bol_product_article):
        bol_product_article["text"] = text_override
        result = BolProductExtractionPrecleaning().run([bol_product_article])

        if expected is None:
            assert len(result) == 0
        else:
            assert len(result) == 1
            assert result[0]["text"] == text_override
            for item in expected:
                assert item in result[0]["llm_cleaned_text"]
