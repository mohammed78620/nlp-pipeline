import random
import string
from typing import Tuple

import pytest

from nlp_pipeline.schema.segmentation import Sentence
from nlp_pipeline.tasks.segmentation import Segmentation


def random_word(length: int = None) -> str:
    """
    Generate a random word.

    Args:
        length (int, optional): Length of the word to be generated. If not
            provided, random between 1 and 6. Defaults to None.

    Returns:
        str: The result, the generated word.
    """
    if length is None or length < 1:
        length = random.randrange(1, 6)  # nosec CWE-330

    letters = string.ascii_lowercase
    word = "".join([random.choice(letters) for _ in range(length)])  # nosec CWE-330
    return word


def random_sentence(num_words: int) -> str:
    """
    Generate a random sentence, without a puncuation but first word capitlized.

    Args:
        num_words (int): Number of words for the sentence to have.

    Returns:
        str: The result.
    """
    sentence = " ".join([random_word() for _ in range(num_words)])
    sentence = sentence.capitalize()
    return sentence


def make_2_similar_sentences(base_num_words: int, num_extra_words: int) -> Tuple[str, str]:
    """
    Generate two sentences that are the same for the first `base_num_words` and differ
    by the second sentence having `num_extra_words` added to the end.

    Sentences are fullstop seperated.

    Args:
        base_num_words (int): Number of words for the sentences to have at the start that are the same.
        num_extra_words (int): The number of extra words the second sentence should have.

    Returns:
        Tuple[str, str]: The result, the base sentence and longer sentence.
    """
    # Generate first sentence
    base_sentence = random_sentence(base_num_words)

    # Sanity check we have expected number of tokens
    assert len(Segmentation().tokenize(base_sentence)) == base_num_words

    # Generate second sentence that's different by having extra words on the end of the last
    extra_words = random_sentence(num_extra_words)
    longer_similar_sentence = " ".join([base_sentence, extra_words])

    # Add full stops to the sentences
    base_sentence += "."
    longer_similar_sentence += "."

    return base_sentence, longer_similar_sentence


class TestSegmentation:
    def test_segmentation(self, articles):
        data = {
            "batch_id": "1",
            "version": "1.0.0",
            "created_on": "2022-09-02",
            "source_file": "20220101/example.tar.gz",
            "source_type": "website",
            "source": "Directory Reader",
            "articles": articles,
        }
        res = Segmentation().run(data)

        assert len(res["articles"]) > 0

    @pytest.mark.parametrize(
        "test_input, expected",
        [
            (
                {"pre_segmented_text": ["Too short.", "Quite short too"]},
                [],
            ),
            (
                {"pre_segmented_text": ["This is an article that contains a sentence."]},
                [{"text": "This is an article that contains a sentence."}],
            ),
            (
                {
                    "pre_segmented_text": [
                        "This is an article that contains some sentences. This is a different sentence."
                    ]
                },
                [
                    {"text": "This is an article that contains some sentences."},
                    {"text": "This is a different sentence."},
                ],
            ),
            (
                {"pre_segmented_text": ["This is an article that contains some sentences. But this too short."]},
                [{"text": "This is an article that contains some sentences."}],
            ),
            (
                {"pre_segmented_text": ["This is a duplicated sentence. This is a duplicated sentence."]},
                [{"text": "This is a duplicated sentence."}],
            ),
            (
                {
                    "pre_segmented_text": [
                        "This is a sentence that contains a right double quotation mark unicode value \u201d."
                    ]
                },
                [{"text": "This is a sentence that contains a right double quotation mark unicode value ”."}],
            ),
            (
                {"pre_segmented_text": ["This is a sentence that contains \u00dcnicode values."]},
                [{"text": "This is a sentence that contains Ünicode values."}],
            ),
            (
                {"pre_segmented_text": ["This is a  sentence that contains    \t  double spaces."]},
                [{"text": "This is a sentence that contains double spaces."}],
            ),
            (
                {"pre_segmented_text": ["This sentence contains a \u3000 white space."]},
                [{"text": "This sentence contains a white space."}],
            ),
            (
                {
                    "pre_segmented_text": [
                        "PS5 exclusive Forspoken heading up Square Enix’s Tokyo Game Show plans | TechRadar"
                    ]
                },
                [{"text": "PS5 exclusive Forspoken heading up Square Enix’s Tokyo Game Show plans"}],
            ),
            (
                {"pre_segmented_text": ["Halfords acquires Lodge Tyre reportedly said - Tyrepress"]},
                [{"text": "Halfords acquires Lodge Tyre reportedly said - Tyrepress"}],
            ),
            (
                {
                    "pre_segmented_text": [
                        "RFID Tags Track Shipping Containers for JCI | 2016-10-01 | Assembly Magazine | ASSEMBLY"
                    ]
                },
                [{"text": "RFID Tags Track Shipping Containers for JCI"}],
            ),
            (
                {
                    "pre_segmented_text": [
                        "Home » Volvo Employs 3D Printing to Make Tools, Fixtures for its Virginia Assembly Plant"
                    ]
                },
                [{"text": "Volvo Employs 3D Printing to Make Tools, Fixtures for its Virginia Assembly Plant"}],
            ),
            (
                {"pre_segmented_text": ["...this sentence starts with three dots, hence it shouldn't be processed"]},
                [],
            ),
            (
                {
                    "pre_segmented_text": [
                        "The British Airways network infrastructure is being emulated at its new testing centre using ITrinegy Continue Reading"
                    ]
                },
                [],
            ),
            (
                {
                    "pre_segmented_text": [
                        "Click to read more about Vishay Releases Royalty-Free Courier-115 Software Protocol Enabling Infrared Wireless Communication for Texas Instruments MSP430 MCU Platform."
                    ]
                },
                [],
            ),
            (
                {"pre_segmented_text": ["This is a sentence that contains : colon."]},
                [{"text": "This is a sentence that contains"}],
            ),
            (
                {"pre_segmented_text": ["This is a sentence that contains Continue reading in the sentence"]},
                [],
            ),
            (
                {"pre_segmented_text": ["continue Reading is at the start of the sentence"]},
                [],
            ),
            (
                {"pre_segmented_text": ["this sentence contains ..."]},
                [],
            ),
            (
                {"pre_segmented_text": ["This is a sentence that contains > greater than sign."]},
                [{"text": "This is a sentence that contains"}],
            ),
            (
                {"pre_segmented_text": ["This is a sentence that contains also read in the sentence"]},
                [],
            ),
            (
                {
                    "pre_segmented_text": [
                        "This is a sentence that contains click to read more about read in the sentence"
                    ]
                },
                [],
            ),
            (
                {
                    "source_type": "edgar",
                    "text": "This is a sentence right here  this should appear as another sentence because of the spaces      the same for this one too.   ",
                },
                [
                    {"text": "This is a sentence right here"},
                    {"text": "this should appear as another sentence because of the spaces"},
                    {"text": "the same for this one too."},
                ],
            ),
            (
                {
                    "source_type": "edgar",
                    "text": "This is a sentence right here\nthis should appear as another sentence because of the newline. This splits based on grammar.  butthishastoomanynums  2000 1234 1234 54321 123",
                },
                [
                    {"text": "This is a sentence right here"},
                    {"text": "this should appear as another sentence because of the newline."},
                    {"text": "This splits based on grammar."},
                ],
            ),
        ],
    )
    def test_segment_article(self, test_input, expected):
        result = Segmentation().segment_article(test_input)

        assert len(result) == len(expected)
        for idx, sentence in enumerate(result):
            # check its whats expected
            assert sentence["text"] == expected[idx]["text"]

            # check its valid
            try:
                _ = Sentence(**sentence)
            except Exception as exc:
                raise AssertionError(f"Invalid result returned {exc}")

    def test_segment_sentence_long_1(self):
        """
        Test how 2 similar sentences are parsed when one is at the token limit and the other
        is only dissimilar after tha max token limit.
        """
        # Generate 2 sentences with enough tokens to hit the max token limit
        max_num_tokens = Segmentation().MAX_SENTENCE_TOKENS
        base_sentence, longer_similar_sentence = make_2_similar_sentences(max_num_tokens, 5)

        # Segment
        segmentation = Segmentation()
        result_1 = segmentation.segment_sentence(base_sentence)
        result_2 = segmentation.segment_sentence(longer_similar_sentence)

        assert result_1 is not None
        assert result_2 == []

    def test_segment_sentence_long_2(self):
        """
        Test how 2 similar sentences are parsed when both are the same beyond token limit then diverge
        """
        # Generate 2 sentences with enough tokens to hit the max token limit
        max_num_tokens = Segmentation().MAX_SENTENCE_TOKENS + 1
        base_sentence, longer_similar_sentence = make_2_similar_sentences(max_num_tokens, 5)

        # Segment
        segmentation = Segmentation()
        result_1 = segmentation.segment_sentence(base_sentence)
        result_2 = segmentation.segment_sentence(longer_similar_sentence)

        assert result_1 is not None
        assert result_2 == [] or result_2 is None

    @pytest.mark.parametrize(
        "test_input, expected",
        [
            ("Too short", None),
            ("Too many numbers 0123 12345 124124 131 34124 1512412 124141", None),
            ("This is a short sentence.", {"text": "This is a short sentence."}),
        ],
    )
    def test_segment_sentence(self, test_input, expected):
        result = Segmentation().segment_sentence(test_input)

        if result:
            # check its valid
            for sentence in result:
                try:
                    _ = Sentence(**sentence)
                except Exception as exc:
                    raise AssertionError(f"Invalid sentence returned {exc}. Sentence: {sentence}")

                assert sentence["text"] == expected["text"]
