import pytest

from nlp_pipeline.utils.acronym_resolver import AcronymResolver


class TestAcronymResolver:
    """
    Class containing all unit tests associated with the AcronymResolver class.
    """

    @pytest.fixture
    def data(self):
        """
        Define some examples of text containing acronyms and their associated
        backronyms.
        """

        return [
            {
                "id": 0,
                "purpose": "Simple backronym/acronym pair replacement with the backronym.",
                "text": "Amazon Web Services (AWS) are planning to build a data center in the UK.",
                "acronym_dictionaries": {
                    "Amazon Web Services (AWS)": "Amazon Web Services",
                    "AWS": "Amazon Web Services",
                },
                "resolved_text": "Amazon Web Services are planning to build a data center in the UK.",
            },
            {
                "id": 1,
                "purpose": "Replacement of backronym/acronym pair and additional acronym later in the text.",
                "text": "The mission of World Wildlife Fund (WWF) is to "
                "conserve nature. WWF also wish to reduce the most "
                "pressing threats to the diversity of life on Earth.",
                "acronym_dictionaries": {
                    "World Wildlife Fund (WWF)": "World Wildlife Fund",
                    "WWF": "World Wildlife Fund",
                },
                "resolved_text": "The mission of World Wildlife Fund is to "
                "conserve nature. World Wildlife Fund also "
                "wish to reduce the most pressing threats to "
                "the diversity of life on Earth.",
            },
            {
                "id": 2,
                "purpose": "Replacement of two separate of backronym/acronym pairs.",
                "text": "Amazon Web Services (AWS) has recently promised to "
                "provide the World Wildlife Fund (WWF) with free AWS "
                "credits to use on conservation projects.",
                "acronym_dictionaries": {
                    "Amazon Web Services (AWS)": "Amazon Web Services",
                    "AWS": "Amazon Web Services",
                    "World Wildlife Fund (WWF)": "World Wildlife Fund",
                    "WWF": "World Wildlife Fund",
                },
                "resolved_text": "Amazon Web Services has recently promised to "
                "provide the World Wildlife Fund with free "
                "Amazon Web Services credits to use on "
                "conservation projects.",
            },
            {
                "id": 3,
                "purpose": "Identification and replacement of lower cased backronym.",
                "text": "The fear of missing out (FOMO) is causing tech "
                "companies to make a number of their employees "
                "redundant.",
                "acronym_dictionaries": {
                    "fear of missing out (FOMO)": "fear of missing out",
                    "FOMO": "fear of missing out",
                },
                "resolved_text": "The fear of missing out is causing tech "
                "companies to make a number of their employees"
                " redundant.",
            },
            {
                "id": 4,
                "purpose": "Test to demonstrate that lower cased acronym with "
                "capitalized backronym will not be identified.",
                "text": "Amazon Web Services (aws) are planning to build a data center in the UK.",
                "acronym_dictionaries": {},
                "resolved_text": "Amazon Web Services (aws) are planning to build a data center in the UK.",
            },
            {
                "id": 5,
                "purpose": "Test to demonstrate that lower case acronym will not be identified.",
                "text": "The letters in the word laser stand for light "
                "amplification by stimulated emission of radiation "
                "(laser)",
                "acronym_dictionaries": {},
                "resolved_text": "The letters in the word laser stand for light"
                " amplification by stimulated emission of "
                "radiation (laser)",
            },
            {
                "id": 6,
                "purpose": "Test to demonstrate that acronym with very long backronym will not be identified.",
                "text": "A long time ago, people were interested in Accumulating large quantities Corn (AC).",
                "acronym_dictionaries": {},
                "resolved_text": "A long time ago, people were interested in Accumulating large quantities Corn (AC).",
            },
            {
                "id": 7,
                "purpose": "Test the presence of recursive acronyms, if present these will cause potiential issues when subsituting backronyms for acronyms.",
                "text": "GPE Palmtop Environment (GPE) is a really important company selling devices to Amazon Web Services.",
                "acronym_dictionaries": {},
                "resolved_text": "GPE Palmtop Environment (GPE) is a really important company selling devices to Amazon Web Services.",
            },
            {
                "id": 8,
                "purpose": "Test the absence of an acronym/backronym pair in a piece of text.",
                "text": "Amazon Web Services are planning to build a data center in the United Kingdom.",
                "acronym_dictionaries": {},
                "resolved_text": "Amazon Web Services are planning to build a data center in the United Kingdom.",
            },
        ]

    @pytest.mark.parametrize(
        "index, list_of_examples",
        [
            (0, "data"),
            (1, "data"),
            (2, "data"),
            (3, "data"),
            (4, "data"),
            (5, "data"),
            (6, "data"),
            (7, "data"),
            (8, "data"),
        ],
    )
    def test_resolve_acronyms(self, index, list_of_examples, request):
        """
        Test the resolve_acronyms method by passing an example text sentence and its
        associated dictionary of extracted acronym/backronym pairs and compare to the
        expected resolved sentence.
        """

        # extract the test examples
        list_of_examples = request.getfixturevalue(list_of_examples)

        # extract the specific dictionary of interest
        example = list_of_examples[index]

        # test the specific test case
        assert (
            AcronymResolver().resolve_acronyms(example["text"], example["acronym_dictionaries"])
            == example["resolved_text"]
        )

    @pytest.mark.parametrize(
        "acronym_text, expected_result",
        [
            ("123", True),
            ("AWS123", True),
            ("AWS", False),
        ],
    )
    def test_contains_number(self, acronym_text, expected_result):
        """
        Test the contains_number method by passing a set of acronyms and examining if
        any contain numeric values.
        """
        assert AcronymResolver().contains_number(acronym_text) == expected_result

    @pytest.mark.parametrize(
        "acronym_text, expected_result",
        [
            ("AWS Inc.", True),
            ("AWS  ", True),
            ("@IOL", True),
            ("AWS!", True),
            ("AWS", False),
        ],
    )
    def test_contains_special_character(self, acronym_text, expected_result):
        """
        Test the contains_special_character method by passing a set of acronyms and
        examining if any contain a special character value.
        """
        assert AcronymResolver().contains_special_character(acronym_text) == expected_result

    @pytest.mark.parametrize(
        "acronym_text, expected_result",
        [
            ("AWSinc", True),
            ("AWScorp", True),
            ("AWS", False),
            ("AWSs", False),
        ],
    )
    def test_contains_more_lowercase_characters(self, acronym_text, expected_result):
        """
        Test the contains_more_lowercase_characters method by passing a set of acronyms
        and examining if any contain more upper case than lower case characters.
        """
        assert AcronymResolver().contains_more_lowercase_characters(acronym_text) == expected_result

    @pytest.mark.parametrize(
        "acronym, backronym, expected_result",
        [
            ("AWS", "Amazon Web Services", False),
            ("FOMO", "fear of missing out", False),
            ("laser", "light amplification by stimulated emission of radiation", False),
            ("SA", "This backronym is too long", True),
            ("LAC", "This backronym is too long compared to its acronym", True),
        ],
    )
    def test_backronym_is_not_representative_of_acronym(self, acronym, backronym, expected_result):
        """
        Test the backronym_is_not_representative_of_acronym method by passing an
        acronym/backronym pair and checking if the backronym contained twice or more
        words than the number of characters in the acronym.
        """
        assert AcronymResolver().backronym_is_not_representative_of_acronym(acronym, backronym) == expected_result

    @pytest.mark.parametrize(
        "acronym, backronym, expected_result",
        [
            ("AWS", "Amazon Web Services", True),
            ("WWF", "World Wildlife Fund", True),
            ("FOMO", "fear of missing out", True),
            ("laser", "light amplification by stimulated emission of radiation", False),
        ],
    )
    def test_good_acronym(self, acronym, backronym, expected_result):
        """
        Test the good_acronym method by passing an acronym/backronym pair and ensuring
        that each of the following methods is satisfied:

        1. contains_number
        2. contains_special_character,
        3. contains_more_uppercase_characters
        4. backronym_is_not_representative_of_acronym
        """
        assert AcronymResolver().good_acronym(acronym, backronym) == expected_result

    def test_create_acronyms_dictionary1(self, data):
        """
        Test the create_acronyms_dictionary method by passing an acronym_dict and
        acronym/backronym pair to ensure that this pair is correctly added to the
        acronym_dict.

        This test, tests the simple case where the first identified acronym/backronym
        pair is added to the acronym_dictionary.
        """

        assert (
            AcronymResolver().create_acronyms_dictionary({}, "AWS", "Amazon Web Services")
            == data[0]["acronym_dictionaries"]
        )

    def test_create_acronyms_dictionary2(self, data):
        """
        Test the create_acronyms_dictionary method by passing an acronym_dict and
        acronym/backronym pair to ensure that this pair is correctly added to the
        acronym_dict.

        This test ensures that a newly identified acronym/backronym pair is added to
        an existing acronym_dictionary.
        """

        assert (
            AcronymResolver().create_acronyms_dictionary(data[0]["acronym_dictionaries"], "WWF", "World Wildlife Fund")
            == data[2]["acronym_dictionaries"]
        )

    @pytest.mark.parametrize(
        "index, list_of_examples",
        [
            (0, "data"),
            (1, "data"),
            (2, "data"),
            (3, "data"),
            (4, "data"),
            (5, "data"),
            (6, "data"),
            (7, "data"),
            (8, "data"),
        ],
    )
    def test_identify_acronyms(self, index, list_of_examples, request):
        """
        Test the identify_acronyms method by passing a list of test sentence and
        ensuring that the acronyms/backronyms pairs are correctly extracted.
        """

        # extract the test examples
        list_of_examples = request.getfixturevalue(list_of_examples)

        # extract the specific dictionary of interest
        example = list_of_examples[index]

        # test the specific test case
        assert (
            AcronymResolver().identify_acronyms(
                example["text"],
            )
            == example["acronym_dictionaries"]
        )
