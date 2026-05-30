import pytest

from nlp_pipeline.tasks.directory_reader_lexis_nexis import DirectoryReader


@pytest.mark.parametrize(
    "input, expected",
    [
        ("app/file1.tar.gz", "file1"),
        ("root/file2.lzma", "file2"),
        ("root/file3.pkg.tar.zst", "file3"),
    ],
)
def test_get_name_from_path(input, expected):
    name = DirectoryReader().get_name_from_path(input)
    assert name == expected
