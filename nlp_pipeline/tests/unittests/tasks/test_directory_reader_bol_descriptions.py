from nlp_pipeline.schema.directory_reader import RawArticle
from nlp_pipeline.tasks.directory_reader_bol_evidence_descriptions import DirectoryReaderBolEvidenceDescriptions


def test_process_article():
    reader = DirectoryReaderBolEvidenceDescriptions()

    vid = "company_vid_001"
    source_type = "ik_us_evidence"

    file_name = "foo"
    archive_name = "bar"
    article = {
        "supplier_vid": vid,
        "source_type": source_type,
        "source": "bizz",
        "text": "Product description goes here",
        "evidence_date": "2020-02-14T00:00:00.000Z",
    }

    processed_article = reader.process_article(article, file_name, archive_name)

    assert type(processed_article) is RawArticle

    processed_article = processed_article.model_dump(by_alias=True)

    assert processed_article["metadata"]["extra_header_info"]["vid"] == vid
    assert processed_article["source_type"] == source_type
    assert processed_article["original_html_file"] == file_name
    assert processed_article["original_compressed_filename"] == archive_name
