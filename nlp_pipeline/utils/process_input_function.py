from statistics import mean
from typing import Dict, List, Optional

from polyglot.detect import Detector

from nlp_pipeline.utils import htmlutils
from nlp_pipeline.utils.acronym_resolver import AcronymResolver
from nlp_pipeline.utils.fingerprint import FingerprintStore, LSHFingerprintStore


def unicode_avg(s: str) -> float:
    """
    strip text to 3000 words and get average character

    Args:
        s (str): cleaned text

    Returns:
        int: the average character
    """
    if not s:
        return None

    s = s.strip()
    if len(s) > 3000:
        s = s[0:3000]

    s = s.replace(" ", "").replace("\n", "")
    return mean([ord(c) for c in s])


def is_latin_by_codepoint(s: str) -> bool:
    """
    check if text is latin by checking if averge character is below 180
    Args:
        s (str): is the cleaned text

    Returns:
        bool: return true if latin
    """
    if not s:
        return None

    return unicode_avg(s) < 180


def is_en(s: str) -> bool:
    """
    is string english

    Args:
        s (str): string to classify

    Returns:
        bool: return true if english
    """

    try:
        detector = Detector(s)
        if detector.language.confidence < 0.9:
            return False

        return detector.language.code == "en"
    except BaseException:
        return False


def get_meta_desc(metas: List) -> str:
    """
    iterate throught metas and set meta description to content
    and return meta_desc

    Args:
        metas (List): list of metas

    Returns:
        str: return meta description
    """
    meta_desc = None
    for meta in metas:
        if "name" in meta.attrs and meta.attrs["name"] == "description":
            if "content" not in meta.attrs:
                continue

            if meta.attrs["content"].strip() == "":
                meta_desc = None
            else:
                meta_desc = meta.attrs["content"].strip()
    return meta_desc


def is_raw_html_empty(raw_html: str) -> bool:
    """
    check if raw html is empty

    Args:
        raw_html (str): the html

    Returns:
        bool: returns true if html is empty
    """
    if raw_html is None or len(raw_html) == 0:
        return True

    return False


def get_meta_json(raw_html: str, cleaned_text: str, pre_segmented_text: List[str], meta_json: Dict) -> Dict:
    """
    Get just the body text from the HTML document

    Args:
        raw_html (str): raw html
        cleaned_text (str): text data and content from meta desc
        pre_segmented_text (List[str]): List of pre segmented sentences
        meta_json (Dict): text and html data

    Returns:
        Dict: meta data with text and html field
    """

    if not is_latin_by_codepoint(cleaned_text):
        return None

    if not is_en(cleaned_text):
        return None

    result = {"text": cleaned_text, "pre_segmented_text": pre_segmented_text, "html": raw_html, "metadata": meta_json}

    return result


def prepare_text(raw_html: str, ignore_non_english: bool = True, use_acronym_resolver: bool = True) -> Optional[Dict]:

    if is_raw_html_empty(raw_html):
        return None

    meta_json, soup = htmlutils.process(raw_html)

    # skip if not english
    if ignore_non_english:
        try:
            lang = soup.findAll(attrs={"name": "language"})[0]["content"]
        except BaseException:
            lang = None

        if lang and not lang.lower().startswith("en"):
            # English is often identified as "en" or "English".
            return None  # It was explicitly marked as not English.

    # clean
    cleaned_text = soup.get_text().strip()
    pre_segmented_text = [text for text in soup.stripped_strings]

    if use_acronym_resolver:

        acronym_resolver = AcronymResolver()

        # identify all acronym/backronym pairs contained in the cleaned text
        acronym_dict = acronym_resolver.identify_acronyms(cleaned_text)

        # replace any of the identified acronyms in the pre-segmented text
        pre_segmented_text = [acronym_resolver.resolve_acronyms(text, acronym_dict) for text in pre_segmented_text]

    if cleaned_text == "":
        return None

    metas = soup.find_all("meta")
    meta_desc = get_meta_desc(metas)

    result = {
        "meta_json": meta_json,
        "cleaned_text": cleaned_text,
        "pre_segmented_text": pre_segmented_text,
        "meta_desc": meta_desc,
    }
    return result


def process_crawled_html(
    raw_html: str,
    ignore_non_english: bool = True,
    fingerprintstore: FingerprintStore | LSHFingerprintStore | None = None,
) -> Dict:
    """
    get metadata, clean html and finger print text

    Args:
        raw_html (str): the html as a string
        ignore_non_english (bool, optional): _description_. Defaults to True.
        fingerprintstore (LSH_cache, optional): _description_. Defaults to None.

    Returns:
        Dict: return dict containing metadata cleaned text and html text
    """
    prepared = prepare_text(raw_html, ignore_non_english)
    if prepared is None:
        return None

    meta_json = prepared["meta_json"]
    cleaned_text = prepared["cleaned_text"]
    pre_segmented_text = prepared["pre_segmented_text"]

    # de-dupe
    if fingerprintstore is not None:
        fingerprint = fingerprintstore.add_item(cleaned_text)
        if not fingerprint:
            return None

    # create article
    article = get_meta_json(raw_html, cleaned_text, pre_segmented_text, meta_json)

    if fingerprintstore and fingerprint and article:
        article["metadata"]["fingerprint"] = fingerprint
        article["metadata"]["fingerprint_config"] = fingerprintstore.get_config()

    return article


def process_crawled_html_meta(
    raw_html: str,
    ignore_non_english: bool = True,
    fingerprintstore: FingerprintStore | LSHFingerprintStore | None = None,
) -> Dict:

    if is_raw_html_empty(raw_html):
        return None

    meta_json, soup = htmlutils.process(raw_html)

    # skip if not english
    if ignore_non_english:
        try:
            lang = soup.findAll(attrs={"name": "language"})[0]["content"]
        except BaseException:
            lang = None

        if lang and not lang.lower().startswith("en"):
            # English is often identified as "en" or "English".
            return None  # It was explicitly marked as not English.

    # clean
    metas: List[str] = []
    for attr in [{"name": "description"}, {"name": "keywords"}]:
        metas += htmlutils.find_meta_content(soup, attrs=attr, type=attr["name"])

    if metas is None:
        return None

    pre_segmented_text = metas
    cleaned_text = ". ".join(pre_segmented_text)

    # de-dupe
    if fingerprintstore is not None:
        fingerprint = fingerprintstore.add_item(cleaned_text)
        if not fingerprint:
            return None

    # create article
    article = get_meta_json(raw_html, cleaned_text, pre_segmented_text, meta_json)

    if fingerprintstore and fingerprint and article:
        article["metadata"]["fingerprint"] = fingerprint
        article["metadata"]["fingerprint_config"] = fingerprintstore.get_config()

    return article
