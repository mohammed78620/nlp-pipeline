import pytest

from nlp_pipeline.schema.directory_reader import FingerprintConfig, LSHFingerprintConfig
from nlp_pipeline.utils.fingerprint import VERSION, FingerprintStore, LSHFingerprintStore, clean, fingerprint


@pytest.fixture
def texts():
    texts = [
        {"key": "base_text", "value": "This is the sentence to fingerprint."},
        {"key": "samey_text_1", "value": "This is thesentence to Fingerprint"},
        {"key": "samey_text_2", "value": "This has the sentence to fingerprint."},
        {"key": "samey_text_3", "value": "This is bit more diff sentence to fingerprint."},
        {"key": "samey_text_4", "value": "This is once again a bit more diff to finger."},
        {"key": "different_text_1", "value": "This is a pretty different text."},
    ]
    return texts


@pytest.fixture
def documents():
    documents = {
        "doc_original": "If you’re nervous about speaking English in a new job, don’t try to memorize complicated things. Your coworkers won’t be testing you on your grammar knowledge, and they probably won’t care if you use an impressive vocabulary word.",
        "doc_small_diff1": "If you’re truly nervous about speaking English in a new job, don’t try to memorize complicated things. Your coworkers won’t be testing you on your grammar knowledge, and they probably will not care so much if you use an impressive vocabulary word.",
        "doc_small_diff2": "If you’re nervous about speaking English in a new job, don’t try to memorize complicated things. Your coworkers won’t be testing you on your grammar knowledge, and they probably won’t care if you use an impressive vocabulary word.",
        "doc_big_diff": "This is a completely different document",
        "doc_half_diff": "If you’re nervous about speaking English in a new job, don’t try to memorize complicated things. Your coworkers won’t be",
    }
    return documents


@pytest.fixture
def low_jaccard(texts):
    jaccard = 0.1
    expected = {
        "base_text": True,
        "samey_text_1": None,
        "samey_text_2": None,
        "samey_text_3": True,
        "samey_text_4": True,
        "different_text_1": True,
    }
    return texts, jaccard, expected


@pytest.fixture
def mid_jaccard(texts):
    jaccard = 0.4
    expected = {
        "base_text": True,
        "samey_text_1": None,
        "samey_text_2": None,
        "samey_text_3": True,
        "samey_text_4": True,
        "different_text_1": True,
    }
    return texts, jaccard, expected


@pytest.fixture
def high_jaccard(texts):
    """
    High jaccard should mean only None if exact match.
    """
    jaccard = 0.99
    expected = {
        "base_text": True,
        "samey_text_1": None,
        "samey_text_2": True,
        "samey_text_3": True,
        "samey_text_4": True,
        "different_text_1": True,
    }
    return texts, jaccard, expected


def test_clean():
    text = "123AbCd"
    char_set = "ABcd"
    result = clean(text, char_set)

    assert result == "cd"


def test_fingerprint():
    text = "123AbCd"
    char_set = "ABcd"
    result_1 = fingerprint(text, char_set)
    result_2 = fingerprint(text, char_set)

    assert result_1 is not None
    assert result_2 == result_1


class TestFingerprintStore:
    def test_init(self):
        text = "This is the sentence to fingerprint and store."

        store = FingerprintStore()
        store_2 = FingerprintStore()

        hash_1 = store.add_item(text)
        hash_2 = store_2.add_item(text)

        assert hash_1 is not None
        assert hash_2 == hash_1

    def test_get_config(self):
        store = FingerprintStore()
        result = store.get_config()

        assert type(result) is dict
        assert result["version"] == VERSION

        _ = FingerprintConfig(**result)

    def test_has_item(self):
        text = "This is the sentence to fingerprint and store."

        store = FingerprintStore()

        assert store.has_item(text) is False
        store.add_item(text)
        assert store.has_item(text) is True

    def test_has_hash(self):
        text = "This is the sentence to fingerprint and store."

        store = FingerprintStore()

        assert store.has_hash("totally_random_hash") is False
        store.add_item(text)
        assert store.has_item(text) is True

    def test_add_item(self):
        text = "This is the sentence to fingerprint and store."
        samey_text = "this is thesentence to fingerprint and store"
        different_text = "This is a sentence to fingerprint and store."

        store = FingerprintStore()

        hash_1 = store.add_item(text)
        assert hash_1 is not None
        assert store.has_hash(hash_1) is True
        assert store.has_item(text) is True

        hash_2 = store.add_item(text)
        assert hash_2 is None

        hash_3 = store.add_item(samey_text)
        assert hash_3 is None

        hash_4 = store.add_item(different_text)
        assert hash_4 is not None


class TestLSHFingerprintStore:
    def test_init(self):
        text = "This is the sentence to fingerprint and store."

        seed = 5
        min_jaccard = 0.5

        store = LSHFingerprintStore(seed, min_jaccard)
        store_2 = LSHFingerprintStore(seed, min_jaccard)

        assert store._random_state == seed
        assert store.min_jaccard == min_jaccard

        doc_id_1 = store.add_item(text)
        doc_id_2 = store_2.add_item(text)

        assert store._cache.bins == store_2._cache.bins
        assert doc_id_1 == doc_id_2

    def test_get_config(self):
        seed = 5
        min_jaccard = 0.5

        store = LSHFingerprintStore(seed, min_jaccard)
        result = store.get_config()

        assert type(result) is dict
        assert result["version"] == VERSION

        _ = LSHFingerprintConfig(**result)

    def test_has_doc_id(self):
        text = "This is the sentence to fingerprint."
        seed = 5
        min_jaccard = 0.5

        store = LSHFingerprintStore(seed, min_jaccard)
        doc_id = store.add_item(text)

        result = store.has_doc_id(doc_id)
        assert result is True

        result = store.has_doc_id("totally_random_doc_id")
        assert result is False

    def test_has_item(self):
        text = "This is the sentence to fingerprint."
        samey_text = "This is thesentence to Fingerprint"
        different_text = "This is a pretty different text."

        seed = 1
        min_jaccard = 0.8

        store = LSHFingerprintStore(seed, min_jaccard)
        _ = store.add_item(text)

        assert store.has_item(text) is True
        assert store.has_item(samey_text) is True
        assert store.has_item(different_text) is False

    @pytest.mark.parametrize(
        "test_fixture",
        [
            ("low_jaccard"),
            ("mid_jaccard"),
            ("high_jaccard"),
        ],
    )
    def test_add_item(self, test_fixture, request):
        seed = 5

        texts, min_jaccard, expected = request.getfixturevalue(test_fixture)

        store = LSHFingerprintStore(seed, min_jaccard)

        for entry in texts:
            key, value = entry.values()

            doc_id = store.add_item(value)

            if expected[key] is True:
                assert doc_id is not None
            else:
                assert doc_id is None

    def test_add_item_docs(self, documents):
        seed = 1
        min_jaccard = 0.5
        store = LSHFingerprintStore(seed, min_jaccard)

        item = documents["doc_original"]
        _ = store.add_item(item)
        """
        result = store.has_item(item, min_jaccard=0.5)
        assert result is True

        result = store.has_item(item, min_jaccard=0.1)
        assert result is True

        result = store.has_item(item, min_jaccard=0.9)
        assert result is True
        """

        item2 = documents["doc_small_diff1"]
        hash2 = store.add_item(item2)
        result = store.has_item(item2, min_jaccard=0.5)
        assert result is True
        assert hash2 is None

        result = store.has_item(item, min_jaccard=0.1)
        assert result is True

        result = store.has_item(item, min_jaccard=0.9)
        assert result is True

    def test_get_hash_fingerprint(self):
        seed = 1
        min_jaccard = 0.5
        store = LSHFingerprintStore(seed, min_jaccard)

        text = "foo bar baz"
        fingerprint = store.get_fingerprint(text)

        assert type(fingerprint) is str

        result = store.add_item(text)

        assert fingerprint == result
