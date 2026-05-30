import random
import string
import time
from typing import Dict, List, Optional

import openai
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__).getChild("openai_helper")


def retry_with_exponential_backoff(
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    max_retries: int = 4,
    errors: tuple = (
        openai.APIError,
        Exception,
    ),
):
    """
    Retry decorator with exponential backoff and optional jitter.

    Args:
        initial_delay (float, optional): Initial delay before the first retry, in seconds. Default is 1 second.
        exponential_base (float, optional): The base value for exponential delay growth. Default is 2.
        jitter (bool, optional): jitter acts as a toggle for randomness to the delay. Default is True.
        max_retries (int, optional): Maximum number of retry attempts. Default is 10.
        errors (tuple, optional): Tuple of exception classes that trigger retries. Default includes openai.APIError and Exception.

    Returns:
        callable: A wrapper function that implements the retry mechanism.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            num_retries = 0
            delay = initial_delay

            # Loop until a successful response or max_retries is hit or an exception is raised
            while True:
                try:
                    return func(*args, **kwargs)
                except errors as e:
                    if hasattr(e, "json_body"):
                        # Handle very specific exception from OpenAI - RateLimitError from insufficient_quota
                        error_type = e.json_body.get("error", {}).get("type", None)
                        if error_type == "insufficient_quota":
                            # can't recover from quota issues, just abort.
                            raise e

                    num_retries += 1

                    if num_retries > max_retries:
                        logger.debug(f"Maximum number of retries ({max_retries}) exceeded.")
                        raise e

                    delay *= exponential_base * (1 + jitter * random.random())  # nosec B311
                    time.sleep(delay)

        return wrapper

    return decorator


class OpenAIHelper:
    def __init__(self, api_key: str, model: str, timeout: int = None) -> None:
        self.model = model
        self.timeout = timeout

        self.openai = openai
        self.openai.api_key = api_key

    @retry_with_exponential_backoff()
    def call_gpt(self, command: str) -> str:
        completion = self.openai.ChatCompletion.create(
            model=self.model, messages=[{"role": "user", "content": command}], timeout=self.timeout
        )

        logger.debug(completion)

        response = completion["choices"][0]["message"]["content"]
        return response


class ProductExtraction(OpenAIHelper):
    def __init__(
        self,
        api_key: str,
        model: str,
        timeout: int = None,
        prompt_template: str = "You're a procurement expert, list as bullet points general product categories (say UNKNOWN if you don't know) from the following, don't make up items, do not include: invoice numbers, product HS codes, addresses and postcodes, and emails: '{}'",
        max_product_str_tokens: int = 255,
        min_product_str_tokens: int = 3,
        max_product_length: int = 30,
        bad_response_length: int = 50,
        min_num_products: int = 2,
        retry_attempts: int = 3,
    ) -> None:
        self.prompt_template = prompt_template

        # truncate tokens of product string to this length
        self.max_prod_str_tokens = max_product_str_tokens

        # number of characters in a product for the response to be considered bad
        self.bad_response_length = bad_response_length

        # filter out products that have more this number of characters
        self.max_product_length = max_product_length

        # minimum number of tokens in product string
        self.min_product_str_tokens = min_product_str_tokens

        # minimum number of products for the response to be considered good
        self.min_num_products = min_num_products

        # number of attempts to retry the prompt in order to get a good response
        self.retry_attempts = retry_attempts

        super().__init__(api_key, model, timeout)

    def get_settings(self) -> Dict:
        settings = {
            "prompt_template": self.prompt_template,
            "llm_model": self.model,
            "max_prod_str_tokens": self.max_prod_str_tokens,
            "min_num_products": self.min_num_products,
            "bad_response_length": self.bad_response_length,
            "max_product_length": self.max_product_length,
        }
        return settings

    def is_good_response(self, response: Optional[str]) -> bool:
        if not response:
            return False

        prods = self.get_product_list(response)

        if len(prods) < self.min_num_products:
            return False

        for prod in prods:
            if len(prod) > self.bad_response_length:
                return False
        return True

    @staticmethod
    def clean_product_line(prod_line: str) -> str:
        """
        Clean a prospect extracted product line. Namely strip bulletpoint mark up and
        any trailing whitespace.

        Args:
            prod_line (str): Line to be cleaned.

        Returns:
            str: The resulting cleaned line.
        """
        prod_line = prod_line.strip(string.whitespace + "-")
        return prod_line

    def get_product_list(self, prod_str: str) -> List[Optional[str]]:
        """
        Takes a product string (such as a ChatGPT response), extract the products, and provide
        as a list.

        Expects valid Product String which is Markdown bulletpoint list, meaning each product
        starts with "-" and ends with a newline.

        Args:
            prod_str (str): Product sting that is to be processed.

        Returns:
            List[str]: The result.
        """
        if not prod_str:
            return []

        prods = []
        for line in prod_str.splitlines():
            line = ProductExtraction.clean_product_line(line)
            if line == "":
                continue

            prods.append(line)
        return prods

    def filter_by_length(self, prods: List[str]) -> List[Optional[str]]:
        prods = [prod for prod in prods if len(prod) <= self.max_product_length and len(prod) > 0]
        return prods

    def filter_by_words(self, prods: List[str]) -> List[Optional[str]]:
        # words that if they appear in product cause it to be dropped
        disallow_list = ["unknown"]
        prods = [prod for prod in prods for word in disallow_list if word.lower() not in prod.lower()]
        return prods

    def get_filtered_products(self, prods: List[str]) -> List[Optional[str]]:
        """
        Filter out bad products from list i.e. too long or too short.

        Args:
            prods (List[str]): The products to be filtered.

        Returns:
            List[Optional[str]]: The result.
        """
        prods = self.filter_by_length(prods)
        prods = self.filter_by_words(prods)
        return prods

    def clean_product_str(self, prod_str: str) -> str:
        """
        Truncate to max token length. Ignore successive whitespace.

        Args:
            prod_str (str): Raw product string to be prepped for query

        Returns:
            str: The result
        """
        # tokenize
        tokens = prod_str.split()

        # truncate
        truncated = (" ").join(tokens[: self.max_prod_str_tokens])
        return truncated

    def has_min_num_tokens(self, prod_str: str) -> bool:
        """
        Check if a given product string has at least the minimum required number of tokens.

        Args:
            prod_str (str): The product string to be checked for the minimum number of tokens.

        Returns:
            bool: True if the product string contains at least the minimum required number of tokens,
                False otherwise.
        """
        # tokenize
        tokens = prod_str.split()

        if len(tokens) < self.min_product_str_tokens:
            return False
        return True

    def products_for_company(self, input_text: str) -> List:
        # prepare prompt
        if self.prompt_template is not None:
            input_text = input_text.lower()
            prompt = self.prompt_template.format(input_text)
        else:
            prompt = input_text

        logger.debug(prompt)

        # retry calling a few times to try get a good reponse
        retries = self.retry_attempts
        response = None
        while not self.is_good_response(response):
            if retries <= 0:
                return []

            response = self.call_gpt(prompt)
            logger.debug(response)

            retries -= 1

        products = self.get_product_list(response)
        products = self.get_filtered_products(products)
        return products
