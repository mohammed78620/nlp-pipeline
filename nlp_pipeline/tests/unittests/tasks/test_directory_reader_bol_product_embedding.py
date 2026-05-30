import pytest

from nlp_pipeline.tasks.directory_reader_bol_product_embedding import DirectoryReaderBolProductEmbedding


@pytest.mark.parametrize(
    "products, blacklisted_products, expected",
    [
        (["metal Bolts", "Screws"], ["screws"], ["METAL BOLTS"]),
        (["engine", "screw", "light "], [], ["ENGINE", "LIGHT", "SCREW"]),
        (["engine", " Screw", " light  "], ["screw", "light"], ["ENGINE"]),
        (["screw", "light"], ["engine", " Screw", " light  "], []),
        ([], ["screws"], []),
    ],
)
def test_process_products(products, blacklisted_products, expected):
    reader = DirectoryReaderBolProductEmbedding()
    result = reader.process_products(products, blacklisted_products)

    assert result == expected
