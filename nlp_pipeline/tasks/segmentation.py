import re
import unicodedata
from typing import List, Optional

import psutil
from celery.utils.log import get_task_logger
from sentence_splitter import split_text_into_sentences

from nlp_pipeline.celery_app import app
from nlp_pipeline.lib.common.text import contains_mostly_numbers
from nlp_pipeline.schema.directory_reader import RawArticle, RawArticleBatch
from nlp_pipeline.schema.segmentation import SegmentedArticle, SegmentedArticleBatch, Sentence
from nlp_pipeline.settings import LSH_FINGERPRINT_MEMORY_LIMIT, LSH_SEED, MIN_JACCARD_SEG
from nlp_pipeline.utils.fingerprint import LSHFingerprintStore, fingerprint

logger = get_task_logger(__name__)


class Segmentation(app.Task):
    name = "Segmentation"

    # Max number of words allowed per sentence. Longer sentences are not processed
    MAX_SENTENCE_TOKENS = 32

    # Min number of words allowed per sentence. Shorter sentences are not processed
    MIN_SENTENCE_TOKENS = 5

    # Deal breaker tokens consisting of prefixes, suffixes and series of tokens.
    # When any of the deal breaker tokens is encountered, the sentence is not processed.
    # Deal Breaker Prefixes: (...)
    # Deal Breaker series: (continue reading), (also read), (click to read more about)
    # Deal Breaker Suffixes: (...)
    DEAL_BREAKER_TOKENS = re.compile(
        r"^(\.{3})|\b(\.{3})|\bcontinue reading\b|\balso read\b|\bclick to read more about\b|(\.{3})$",
        re.IGNORECASE,
    )

    # Split on 2 or more whitespaces
    SPLIT_ON_MULTISPACES = re.compile(r"\s{2,}")

    # Characters used to further segment sentences. When. encountered, the original sentence
    # is split by the character, yielding two new sentences.
    BREAKING_CHARS = re.compile(r" : | » | > | \| ")

    def __init__(self):
        self.fingerprint_store = LSHFingerprintStore(seed=LSH_SEED, min_jaccard=MIN_JACCARD_SEG)

    def run(self, input: RawArticleBatch):
        # Get the current worker's memory usage in megabytes
        worker_memory_size = psutil.Process().memory_info().rss / (1024 * 1024)

        if int(worker_memory_size) >= LSH_FINGERPRINT_MEMORY_LIMIT:
            self.fingerprint_store._cache.clear()
            self.fingerprint_store = LSHFingerprintStore(seed=LSH_SEED, min_jaccard=MIN_JACCARD_SEG)

        articles: List[SegmentedArticle] = []

        for article in input["articles"]:
            sentences = self.segment_article(article)
            if len(sentences) == 0:
                continue
            article["sentences"] = sentences

            if "pre_segmented_text" in article:
                del article["pre_segmented_text"]

            articles.append(article)

        num_sentences = sum([len(article["sentences"]) for article in articles])
        logger.info(f"Segmented batch {input['batch_id']} with sentences {num_sentences} total")

        batch = SegmentedArticleBatch(
            batch_id=input["batch_id"],
            version=input["version"],
            created_on=input["created_on"],
            source_file=input["source_file"],
            source_type=input["source_type"],
            source=input["source"],
            articles=articles,
        ).model_dump(by_alias=True)
        return batch

    def segment_article(self, article: RawArticle) -> List[Sentence]:
        """
        Segments an article into sentences

        Args:
            article (RawArticle): An article object
        Returns:
            List[Sentence]: A list of processed sentences
        """
        sentences = []

        source_type = article.get("source_type", None)
        if source_type == "edgar":
            # perform some pre-segment rules special to edgar
            for line in article["text"].split("\n"):
                for segment in self.SPLIT_ON_MULTISPACES.split(line):
                    sentences += split_text_into_sentences(segment, language="en")
        else:
            try:
                for sentence in article["pre_segmented_text"]:
                    sentences += split_text_into_sentences(sentence, language="en")
            except KeyError as e:
                logger.warning(f"Article object is missing key {e}. Article skipped.")
                return []

        segmented_sentences = []
        for sentence in sentences:
            segmented = self.segment_sentence(sentence)
            if segmented:
                segmented_sentences += segmented

        return segmented_sentences

    def segment_sentence(self, sentence: str) -> Optional[List[Sentence]]:
        """
        Further segments a sentence based on a series of punctuation words
        and desired or undesired prefixes. See DEAL_BREAKER_TOKENS and BREAKING_CHARS.
        """

        matches = self.DEAL_BREAKER_TOKENS.findall(sentence)

        if matches:
            logger.debug(f"Sentence '{sentence}' dropped due containing deal breaker tokens")
            return None

        sentences = []
        for s in self.BREAKING_CHARS.split(sentence):
            validated = self.validate_sentence(s)
            if validated:
                sentences.append(validated)

        return sentences

    def validate_sentence(self, sentence: str) -> Optional[Sentence]:
        """
        Validates a sentence fits within the MAX_SENTENCE_TOKENS and MIN_SENTENCE_TOKENS
        constrains. If valid, Computes the sentence fingerprint and returns a `Sentence`

        Args:
            sentence (str): A Sentence text
        Returns:
            The processed sentence metadata or None

        """
        sentence = sentence.encode("utf-8", "ignore").decode("utf-8", "ignore").strip()
        sentence = unicodedata.normalize("NFKC", sentence)
        sentence = re.sub(r"\s+", " ", sentence)
        tokens = self.tokenize(sentence)

        if len(tokens) < self.MIN_SENTENCE_TOKENS:
            return None
        if len(tokens) > self.MAX_SENTENCE_TOKENS:
            tokens = tokens[: self.MAX_SENTENCE_TOKENS]
        if contains_mostly_numbers(sentence):
            return None

        concatenated_tokens = " ".join(tokens)

        # Only return the sentence if it has not  been seen before
        sentence_fingerprint = self.fingerprint_store.add_item(concatenated_tokens)
        if not sentence_fingerprint:
            return None

        id = fingerprint(sentence_fingerprint)

        return {"text": sentence, "id": id, "fingerprint": sentence_fingerprint}

    def tokenize(self, sentence: str) -> List[str]:
        """
        Tokenize a sentence.

        Note: Not proper NLP tokens e.g.:
            - Puncuation will be part of the token
                - "Foo's" is a single token.
                - "Alice said, 'Hi'." = ["Alice", "said,", "'Hi'."]
            - Duplicate spaces lead to empty str tokens i.e. "foo  bar" = ["foo", "", "bar"]

        Args:
            sentence (str): The sentence to be tokenized.

        Returns:
            List[str]: The result, a list of tokens.
        """
        tokens = sentence.split(" ")
        return tokens


app.register_task(Segmentation())
