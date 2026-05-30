from collections import OrderedDict
from typing import Dict

from abbreviations import schwartz_hearst


class AcronymResolver:
    """
    This class identifies acronyms (abbreviations) in a source text. An acronym's
    associated original text is called a backronym and the aim of this class is to
    identify pairs of acronyms/backronyms.

    This class operates as follows:
        1. The schwartz_hearst algorithm is used to extract potential abbreviations from
           a supplied text.
        2. Next, the acronyms are checked to see if they satisfy a certain set of
           rules which aim to ensure that the acronyms are valid.
        3. A dictionary of acronyms/backronyms pairs is created which will be used to
           resolve and remove any identified acronyms with its associated backronyms in
           the extracted text from the HTML.
    """

    def __init__(self):
        pass

    @staticmethod
    def resolve_acronyms(text: str, acronym_dicts: Dict) -> str:
        """
        Replace acronyms identified in the text with their corresponding backronym.
        In the case that no acronym is identified, the same text will be returned.

        Args:
            text (str): A piece of text.
            acronym_dicts (dict): Dictionary containing good quality acronym/backronym
                                  pairs.

        Returns:
            str: A piece of text where if the text contains any acronyms these are
                 replaced with their associated backronyms.
        """

        # ensure that the acronym dict is not empty
        if acronym_dicts:

            # for each acronym/backronym
            for acronym, backronym in acronym_dicts.items():

                # replace the acronym with its backronym
                text = text.replace(acronym, backronym)

        return text

    @staticmethod
    def contains_number(acronym: str) -> bool:
        """
        Identify if an acronym contains a numerical value.

        Args:
            acronym (str): An acronym.

        Returns:
            bool: Boolean value representing if an acronym contains a number.
        """
        return any(char.isdigit() for char in acronym)

    @staticmethod
    def contains_special_character(acronym: str) -> bool:
        """
        Identify if an acronym contains any special symbols.

        Args:
            acronym (str): An acronym.

        Returns:
            bool: Boolean value representing if an acronym contains a special character.
        """

        # define a list of special characters (including whitespace)
        special_characters = "!@#$%^*+?_=,<>/ "

        return any(char in special_characters for char in acronym)

    @staticmethod
    def contains_more_lowercase_characters(acronym: str) -> bool:
        """
        Identify if an acronym contains more lower case characters than upper case
        characters.

        Args:
            acronym (str): An acronym.

        Returns:
            bool: Boolean value representing if an acronym contains more lower case
                  than upper case characters.
        """

        # count the number of letters in the acronym that are upper case
        upper_count = sum(1 for c in acronym if c.isupper())

        # count the number of letters in the acronym that are lower case
        lower_count = sum(1 for c in acronym if c.islower())

        # if the number of lower case letters is less than upper case letters
        return lower_count >= upper_count

    @staticmethod
    def backronym_is_not_representative_of_acronym(acronym: str, backronym: str) -> bool:
        """
        Identify if the backronym contains double or more the number of words than the
        associated number of letters in the acronym.

        Args:
            acronym (str): An acronym.
            backronym (str): A backronym.

        Returns:
            bool: Boolean value representing if a backronym contains double or more
                  words than the number of letters in the associated acronym.
        """

        # identify the number of letters in the acronym
        acronym_length = len(acronym)

        # identify the number of words contained in the backronym
        number_of_words = len(backronym.split(" "))

        # if the number of words in the backronym is double or more the number of
        # letters in the acronym
        return number_of_words >= acronym_length * 2

    def good_acronym(self, acronym: str, backronym: str) -> bool:
        """
        Identify if the acronym/backronym pair satisfies a specific set of rules. These
        set of rules are:

        1. The acronym does not contain a number.
        2. The acronym does not contain a special character.
        3. The acronym contained more upper and lower case characters.
        4. The number of words in the backronym is less than twice the number of
           letters contained in the acronym.

        Args:
            acronym (str): An acronym.
            backronym (str): A backronym.

        Returns:
            bool: Boolean value representing if the acronym/backronym pair satisfies
                  the specific set of rules.
        """

        # identify if the acronym contains any numbers
        if self.contains_number(acronym):
            return False

        # identify if the acronym contains any special characters
        if self.contains_special_character(acronym):
            return False

        # identify if the acronym contains more lower case than upper case letters
        if self.contains_more_lowercase_characters(acronym):
            return False

        # identify if backronym is representative of the acronym
        if self.backronym_is_not_representative_of_acronym(acronym, backronym):
            return False

        return True

    @staticmethod
    def create_acronyms_dictionary(acronym_dic: Dict, acronym: str, backronym: str) -> Dict:
        """
        Add the acronym and associated backronym to a dictionary which will be used to
        resolve the acronym in the text documents. The acronym/backronym will be added
        in the following format:

        1. Amazon Web Services (AWS) -> Amazon Web Services
        2. AWS -> Amazon Web Services

        These need to be added in the above order to ensure that the acronym and
        associated backronym in brackets are removed first from the text.

        Args:
            acronym_dic (dict): Dictionary containing good quality acronym/backronym
                                pairs.
            acronym (str): An acronym.
            backronym (str): A backronym.

        Returns:
            bool: Dictionary containing good quality acronym/backronym pairs.
        """

        # create the full string including acronym and backronym
        backronym_and_acronym = f"{backronym} ({acronym})"

        # add the fully identified string to the dictionary
        acronym_dic[backronym_and_acronym] = backronym

        # add the acronym/backronym pair to the dictionary
        acronym_dic[acronym] = backronym

        return acronym_dic

    def identify_acronyms(self, text: str) -> Dict:
        """
        Identify any acronyms contained in the supplied text string, check that these
        acronyms are valid before returning a dictionary of acronym/backronym pairs.

        Args:
            text (str): A piece of text.

        Returns:
            bool: Dictionary containing good quality acronym/backronym pairs.
        """

        # create a dictionary to store the acronyms
        acronym_dic = OrderedDict()

        # identify each acronym and its associated backronym (phrase associated with acronym)
        potential_acronym_pairs = schwartz_hearst.extract_abbreviation_definition_pairs(doc_text=text)

        # for each acronym and its associated backronym
        for acronym, backronym in potential_acronym_pairs.items():

            # identify if the acronym/backronym pair are a good candidate
            if not self.good_acronym(acronym, backronym):
                continue

            # add the acronym/backronym pair to the dictionary
            acronym_dic = self.create_acronyms_dictionary(acronym_dic, acronym, backronym)

        return acronym_dic
