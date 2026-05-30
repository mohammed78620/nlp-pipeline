import html
import re
import unicodedata
from typing import Dict, List, Optional, Tuple

import inscriptis
import ujson
from bs4 import BeautifulSoup
from date_guesser import guess_date


def get_metajson(firstline: str) -> Dict:
    """
    get meta data from a string

    Args:
        firstline (str): a string containing metadata

    Returns:
        Dict : returns a dict with metadata
    """
    metajson = {}
    if not firstline:
        metajson["metajson_extraction_error"] = "first line in html is empty"
        return metajson
    try:
        jstr = firstline.split("<!--")[1].split("-->")[0].strip()
        metajson = ujson.loads(jstr)
        extra_header_info = metajson.get("extra_header_info", None)

        if extra_header_info is not None:
            metajson["extra_header_info"] = ujson.loads(metajson["extra_header_info"])

    except Exception as e:
        return {"metajson_extraction_error": str(e)}
    return metajson


def process(text: str) -> Tuple[Dict, BeautifulSoup]:
    """
    get meta data from text, extract date, year and scrape from html

    Args:
        text (str): string html

    Returns:
        Tuple[Dict, BeautifulSoup]: meta data and scraped html
    """
    if len(text) == 0:
        return None, None
    firstline = text.split("\n")[0]

    metajson = get_metajson(firstline)

    url = metajson.get("url", None)
    if url is not None:
        date_guess = guess_date(metajson["url"], text)

        if date_guess.date is not None:
            metajson["meta_date"] = date_guess.date.strftime("%Y-%m-%d")
            metajson["meta_year"] = date_guess.date.year
            metajson["guess_method"] = date_guess.method
            metajson["year"] = metajson["meta_year"]

    text = re.sub(r"<(a|/a).*?>", "", text)
    soup = BeautifulSoup(text, features="lxml")

    return metajson, soup


def find_meta_content(soup, attrs: Dict, type) -> Optional[List[str]]:
    """
    Finds metadata content based on attribute search

    Args:
        attrs (Dict): A dictionary of attributes key-value pairs.

    Returns:
        Optional[List[str]]: A list of contents scraped from metadata tags with the given attributes, if any.
    """
    tags = soup.find_all("meta", attrs=attrs)

    metas: List[str] = []
    for tag in tags:
        text = tag.get("content")
        if text:
            metas.append(text)

    return metas


def clean_html(html_text: str) -> str:
    """
    Clean (X)HTML text.

    - Unescape HTML entities
    - Standardize whitespace and remove excess spaces
    - Normalize unicode
    - Normalize apostrophes
    - Prettify. This has the by product effect of:
        - wrapping with html and body tags if not present
        - word wrapping text

    Args:
        html_text (str): HTML string

    Returns:
        str: The result
    """
    # unescape HTML entities to UTF-8 equivalents
    html_text = html.unescape(html_text)

    # replace 1 or more whitespace (e.g. Non-breaking whitespace character "\xa0") with a space
    html_text = re.sub(r"\s+", " ", html_text)

    # normalize the unicode
    html_text = html_text.encode("utf-8", "ignore").decode("utf-8", "ignore")
    html_text = unicodedata.normalize("NFKC", html_text)

    # standardize apostrophes
    # TODO: Consider using unicode's preference of ’ for apostrophes
    html_text = html_text.replace("’", "'")
    html_text = html_text.replace("`", "'")

    soup = BeautifulSoup(html_text, "html5lib")
    html_text = soup.prettify()

    html_text = html_text.strip()
    return html_text


def html_to_text(html_text: str) -> str:
    """
    Basic extraction of text from HTML intended for simple
    documents like Edgar reports which have very clear block
    tags and use of inline tags that would break up the meaning
    of a sentence.

    Args:
        html_text (str): HTML data.

    Returns:
        str: The resulting text.
    """
    text = inscriptis.get_text(html_text)

    # get rid of any funny inscriptis indenting
    text = re.sub(r"\n\s+", "\n", text)
    text = text.strip()
    return text
