import statistics


# TODO: Refactor unicode threshold in a macro
def contains_mostly_numbers(text: str) -> bool:
    """
    Uses mean of unicode values of string to roughly determine numeral frequency in string.
    Imperfect/Fuzzy solution e.g. 'AAAA' considered containing many numbers.

    Args:
        (text: str): A string

    Returns:
        Wether text contains mostly number or not

    Raises:
        TypeError: When text is not a str
        ValueError: When text is empty
    """
    if type(text) is not str:
        raise TypeError(f"Invalid type {type(text)} for {str}")

    text = text.replace(" ", "").replace("\n", "")

    if len(text) == 0:
        raise ValueError(f"Invalid literal {text}. Cannot be empty.")

    return statistics.mean([ord(char) for char in text]) < 80
