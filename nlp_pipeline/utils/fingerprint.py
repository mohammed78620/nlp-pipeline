import hashlib
import json
import string
from typing import Callable, Dict, List, Optional, Set

from lsh.cache import Cache as _LSH_Cache
from lsh.minhash import MinHasher as _LSH_Hasher

hashchars = string.printable.replace(string.punctuation, "").replace(string.whitespace, "")
hashchars_lettersonly = string.ascii_letters


VERSION = "1.0.1"


def clean(text: str, char_set: Set | List | str = hashchars) -> str:
    """
    Filter `text` and make lowercase.

    Args:
        text (str): The text to be cleaned.
        char_set (Set | List | str, optional): Set of chars to filter by. Defaults to hashchars.

    Returns:
        str: The result.
    """
    return "".join([char for char in text.lower() if char in char_set])


def fingerprint(text: str, hash_chars: Set | List | str = hashchars) -> str:
    """
    Produce a fingerprint / hash of `text`. To increase chance of collision `text` is
    filtered to only contain provided `hash_chars`.

    Args:
        text (str): The text to be fingerprinted
        hash_chars (Set | List | str, optional): Set of accepted characters. Defaults to hashchars.

    Returns:
        str: The result.
    """
    cleaned_text = clean(text, char_set=hash_chars)
    encoded_text = cleaned_text.encode("utf-8")
    hashed_text = hashlib.md5(encoded_text).hexdigest()  # nosec
    return hashed_text


class FingerprintStore:
    def __init__(self, hash_func: Callable[[str], str] = fingerprint) -> None:
        """
        Simple fingerprint store using hash collisions.

        Args:
            hash_func (Callable[[str], str], optional): Function to provide the
                hashing / fingerprinting method. Defaults to fingerprint.
        """
        self._hash_func = hash_func
        self._cache = set()

    def get_config(self) -> Dict:
        """
        Return the configuration settings used.

        Returns:
            Dict: The result.
        """
        config = {"method": "Basic", "version": VERSION}
        return config

    def has_hash(self, hashcode: str) -> bool:
        """
        Determin if `hashcode` exists in the store.

        Args:
            hashcode (str): The hash to check.

        Returns:
            bool: The result.
        """
        return hashcode in self._cache

    def has_item(self, item: str) -> bool:
        """
        Determine if `item` exists hashed in the store.

        Args:
            item (str): The item to check.

        Returns:
            bool: The result.
        """
        hashcode = self._hash_func(item)
        return self.has_hash(hashcode)

    def get_fingerprint(self, item: str) -> str:
        """
        Get fingerprint of item.

        Args:
            item (str): The text to fingerprint.

        Returns:
            str: The result.
        """
        hashcode = self._hash_func(item)
        return hashcode

    def add_item(self, item: str) -> Optional[str]:
        """
        Fingerprints `item` and adds to the store.

        Args:
            item (str): The item to be fingerprinted and stored.

        Returns:
            Optional[str]: The result. If `item` isn't already cached then
                its hash is returned, otherwise None is returned.
        """
        hashcode = self.get_fingerprint(item)
        if self.has_hash(hashcode):
            return None

        self._cache.add(hashcode)
        return hashcode


class LSHFingerprintStore:
    def __init__(self, seed: int, min_jaccard: float) -> None:
        """
        LSH based fingerprint store for fuzzy collision.

        Args:
            seed (int): The seed to use for the LSH Hasher.
            min_jaccard (float): Min Jaccard value. Used for determining an item is in the cache.
        """
        # hash settings
        self._seeds = 100
        self._char_ngram = 5
        self._hashbytes = 4
        self._random_state = seed

        # cache settings
        self._num_bands = 20
        self.min_jaccard = min_jaccard

        self._hash_func = _LSH_Hasher(
            seeds=self._seeds, char_ngram=self._char_ngram, hashbytes=self._hashbytes, random_state=self._random_state
        )
        self._cache = _LSH_Cache(self._hash_func, num_bands=self._num_bands)

    def get_config(self) -> Dict:
        """
        Return the configuration settings used.

        Returns:
            Dict: The result.
        """
        config = {
            "method": "LSH",
            "version": VERSION,
            "seed": self._random_state,
            "num_seeds": self._seeds,
            "char_ngram": self._char_ngram,
            "hashbytes": self._hashbytes,
            "num_bands": self._num_bands,
        }
        return config

    def has_doc_id(self, doc_id: str) -> bool:
        """
        Determine if `doc_id` is in cache or not.

        Args:
            doc_id (str): The item's doc id.

        Returns:
            bool: The result.
        """
        return doc_id in self._cache.fingerprints.keys()

    def has_item(self, item: str, min_jaccard: float = None) -> bool:
        """
        Determine if `item` is in the cache by LSH matching.

        Args:
            item (str): The item.
            min_jaccard (float, optional): Optional override of the store's configured setting. Defaults to None.

        Returns:
            bool: The result.
        """
        processed_item = self._preprocess_item(item)

        if min_jaccard is None:
            min_jaccard = self.min_jaccard

        dupes = self._cache.get_duplicates_of(processed_item, min_jaccard=min_jaccard)
        return len(dupes) > 0

    def _hash_lsh_fingerprint(self, lsh_fingerprint: List) -> str:
        """
        Return hash of LSH Fingerprint

        Args:
            lsh_fingerprint (List): The LSH bins to hash

        Returns:
            str: The result.
        """
        bin_string = self._lsh_fingerprint(lsh_fingerprint)
        encoded = bin_string.encode("utf-8")
        hash = hashlib.md5(encoded).hexdigest()  # nosec
        return hash

    def _lsh_fingerprint(self, lsh_fingerprint: List) -> str:
        """
        Return stringified version of LSH bins to act as a fingerprint.

        Args:
            lsh_fingerprint (List): The LSH bins to stringify.

        Returns:
            str: The result.
        """
        bin_string = json.dumps(lsh_fingerprint.tolist())
        return bin_string

    def _preprocess_item(self, item: str) -> str:
        """
        Process the item, such as clean.

        Args:
            item (str): The item to preprocess.

        Returns:
            str: The result
        """
        cleaned_text = clean(item, char_set=hashchars)
        return cleaned_text

    def get_fingerprint(self, item: str, preprocess: bool = True) -> str:
        """
        Return the fingerprint of the `item`

        Args:
            item (str): The item to fingerprint.
            preprocess (bool, optional): Whether or not item needs to be preprocessed. Defaults to True.

        Returns:
            str: The result. The fingerprint.
        """
        if preprocess:
            item = self._preprocess_item(item)

        raw_fingerprint = self._cache.hasher.fingerprint(item)
        fingerprint = self._lsh_fingerprint(raw_fingerprint)
        return fingerprint

    def add_item(self, item: str) -> Optional[str]:
        """
        Fingerprints `item` and adds to the store.

        Args:
            item (str): The item to be fingerprinted and stored.

        Returns:
            Optional[str]: The result. If `item` isn't already cached then
                its doc_id is returned, otherwise None is returned.
        """
        processed_item = self._preprocess_item(item)
        doc_id = self.get_fingerprint(processed_item, preprocess=False)

        if self.has_doc_id(doc_id):
            # is a dupe based on exact hash match
            return None
        if self.has_item(item):
            # is a dupe based on LSH match
            return None

        self._cache.add_doc(processed_item, doc_id)

        return doc_id
