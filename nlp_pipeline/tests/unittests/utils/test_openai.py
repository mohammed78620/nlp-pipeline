from typing import Dict
from unittest.mock import patch

import pytest
from openai.error import RateLimitError

from nlp_pipeline.settings import OPENAI_API_KEY, PE_OPENAI_MODEL, PE_OPENAI_PROMPT
from nlp_pipeline.utils.openai import OpenAIHelper, ProductExtraction


def mock_openai_response(content: str) -> Dict:
    """
    Dummy representation of what a response from OpenAI looks like.
    """
    return {"choices": [{"message": {"content": content}}]}


class TestOpenAIHelper:
    def test_env_vars(self):
        assert OPENAI_API_KEY is not None

    def test_init(self):
        api_key = "123"
        model = "234"
        timeout = 5

        openai_utility = OpenAIHelper(api_key=api_key, model=model, timeout=timeout)

        assert openai_utility.openai.api_key == api_key
        assert openai_utility.model == model
        assert openai_utility.timeout == timeout

    def test_call_gpt(self):
        openai_utility = OpenAIHelper(api_key=OPENAI_API_KEY, model=PE_OPENAI_MODEL)

        prompt = "What parts (as a bulletpoint list) are used to make a car?"
        openai_rsp = "- Engine\n- Transmission\n- Suspension system\n- Steering system\n- Brake system"

        with patch("openai.ChatCompletion.create") as mock_create:
            mock_create.side_effect = [mock_openai_response(openai_rsp)]
            response = openai_utility.call_gpt(prompt)

        assert response == openai_rsp

    def test_call_gpt_with_retries(self):
        helper = OpenAIHelper(OPENAI_API_KEY, PE_OPENAI_MODEL)

        with patch("openai.ChatCompletion.create") as mock_create:
            mock_create.side_effect = [Exception, mock_openai_response("Retried response")]
            response = helper.call_gpt("Retry me!")

        assert response == "Retried response"

    def test_call_gpt_exceeded_quota_exception(self):
        """
        Test handling of insufficient quota repose calling OpenAI
        """
        helper = OpenAIHelper(OPENAI_API_KEY, PE_OPENAI_MODEL)
        with patch("openai.ChatCompletion.create") as mock_create:
            mock_exception = RateLimitError(
                message="You exceeded your current quota, please check your plan and billing details.",
                code="insufficient_quota",
                json_body={
                    "error": {
                        "message": "You exceeded your current quota, please check your plan and billing details.",
                        "type": "insufficient_quota",
                        "param": None,
                        "code": "insufficient_quota",
                    }
                },
            )

            mock_create.side_effect = mock_exception
            with pytest.raises(RateLimitError):
                helper.call_gpt("Trigger quota error")


class TestProductExtraction:
    def test_env_vars(self):
        assert OPENAI_API_KEY is not None
        assert PE_OPENAI_MODEL is not None
        assert PE_OPENAI_PROMPT is not None

    def test_init(self):
        api_key = "123"
        model = "234"
        timeout = 5
        prompt_template = "testing prompt init"
        min_num_products = 10
        bad_response_length = 11
        max_product_length = 12
        retry_attempts = 5

        openai_utility = ProductExtraction(
            api_key=api_key,
            model=model,
            prompt_template=prompt_template,
            timeout=timeout,
            min_num_products=min_num_products,
            bad_response_length=bad_response_length,
            max_product_length=max_product_length,
            retry_attempts=retry_attempts,
        )

        assert openai_utility.openai.api_key == api_key
        assert openai_utility.model == model
        assert openai_utility.timeout == timeout
        assert openai_utility.prompt_template == prompt_template
        assert openai_utility.min_num_products == min_num_products
        assert openai_utility.bad_response_length == bad_response_length
        assert openai_utility.max_product_length == max_product_length
        assert openai_utility.retry_attempts == retry_attempts

    def test_get_settings(self):
        api_key = "123"
        model = "234"
        openai_utility = ProductExtraction(api_key=api_key, model=model)

        response = openai_utility.get_settings()

        assert type(response) is dict
        assert "api_key" not in response.keys()
        assert response["llm_model"] == model

    @pytest.mark.parametrize(
        "gpt_response, expected_result",
        [
            (None, False),
            ("", False),
            ("Not enough products", False),
            (
                "Just 4 lines\n but one of the lines is really long so has too many characters in it like this\n 3rd line\n 4th line",
                False,
            ),
            ("3 lines\n but this\n time they're all good", True),
        ],
    )
    def test_is_good_response(self, gpt_response, expected_result):
        response = ProductExtraction(api_key=OPENAI_API_KEY, model=PE_OPENAI_MODEL).is_good_response(gpt_response)

        assert response is expected_result

    @pytest.mark.parametrize(
        "prod_line, expected_result",
        [
            ("- Foo ", "Foo"),
            ("", ""),
            (" Foo ", "Foo"),
            (" - Foo ", "Foo"),
            (" - Foo-bar", "Foo-bar"),
            ("  -- Foo-bars  ", "Foo-bars"),
        ],
    )
    def test_clean_product_line(self, prod_line, expected_result):
        response = ProductExtraction.clean_product_line(prod_line)
        assert response == expected_result

    @pytest.mark.parametrize(
        "product_str, expected_result",
        [
            ("- Foos\n- Bars\n- Bazs", ["Foos", "Bars", "Bazs"]),
            ("", []),
            (None, []),
            ("- Alice\n- \n- Bob", ["Alice", "Bob"]),
        ],
    )
    def test_get_product_list(self, product_str, expected_result):
        openai_utility = ProductExtraction(api_key=OPENAI_API_KEY, model=PE_OPENAI_MODEL)

        response = openai_utility.get_product_list(product_str)

        assert response == expected_result

    @pytest.mark.parametrize(
        "products, expected_result",
        [
            ([], []),
            (["Foos", "Bars", "Bazs"], ["Foos", "Bars", "Bazs"]),
            (["This product is too long", "OK Product"], ["OK Product"]),
        ],
    )
    def test_filter_by_length(self, products, expected_result):
        max_prod_length = 12
        openai_utility = ProductExtraction(
            api_key=OPENAI_API_KEY, model=PE_OPENAI_MODEL, max_product_length=max_prod_length
        )

        response = openai_utility.filter_by_length(products)

        assert response == expected_result

    @pytest.mark.parametrize(
        "products, expected_result",
        [
            ([], []),
            (["Foos", "Bars", "Bazs"], ["Foos", "Bars", "Bazs"]),
            (
                ["Foo", "Unknown", "(unknown)", "[unknown]", "- UNKNOWN (category unknown)", "- B (category unknown)"],
                ["Foo"],
            ),
        ],
    )
    def test_filter_by_words(self, products, expected_result):
        max_prod_length = 12
        openai_utility = ProductExtraction(
            api_key=OPENAI_API_KEY, model=PE_OPENAI_MODEL, max_product_length=max_prod_length
        )

        response = openai_utility.filter_by_words(products)

        assert response == expected_result

    @pytest.mark.parametrize(
        "products, expected_result",
        [
            ([], []),
            (["Foos", "Bars", "Bazs"], ["Foos", "Bars", "Bazs"]),
            (["This product is too long", "OK Product"], ["OK Product"]),
            (["Good", "Unknown", "This product is too long"], ["Good"]),
        ],
    )
    def test_get_filtered_products(self, products, expected_result):
        max_prod_length = 12
        openai_utility = ProductExtraction(
            api_key=OPENAI_API_KEY, model=PE_OPENAI_MODEL, max_product_length=max_prod_length
        )

        response = openai_utility.get_filtered_products(products)

        assert response == expected_result

    @pytest.mark.parametrize(
        "prod_str, expected_result",
        [
            ("", ""),
            ("LongTokenShouldBeOk", "LongTokenShouldBeOk"),
            ("Two. tokens", "Two. tokens"),
            ("Two.  tokens", "Two. tokens"),
            ("Too many tokens to get trunc-ed", "Too many tokens to get"),
        ],
    )
    def test_clean_product_str(self, prod_str, expected_result):
        max_prod_str_tokens = 5
        openai_utility = ProductExtraction(
            api_key=OPENAI_API_KEY, model=PE_OPENAI_MODEL, max_product_str_tokens=max_prod_str_tokens
        )

        response = openai_utility.clean_product_str(prod_str)

        assert response == expected_result

    @pytest.mark.parametrize(
        "prod_str, expected_result",
        [
            ("", False),
            ("Two. tokens", False),
            ("This has ThreeTokens", True),
        ],
    )
    def test_has_min_num_tokens(sekf, prod_str, expected_result):
        openai_utility = ProductExtraction(api_key=OPENAI_API_KEY, model=PE_OPENAI_MODEL)

        response = openai_utility.has_min_num_tokens(prod_str)

        assert response == expected_result

    def test_products_for_company(self):
        openai_utility = ProductExtraction(api_key=OPENAI_API_KEY, model=PE_OPENAI_MODEL)

        sentence = "Weyland-Yutani Corporation specialises in AI, xenobiology, and builds androids."
        openai_rsp = "- AI\n- xenobiology\n- Andoids"

        with patch("openai.ChatCompletion.create") as mock_create:
            mock_create.side_effect = [mock_openai_response(openai_rsp)]
            response = openai_utility.products_for_company(sentence)

        assert type(response) is list
        assert response != []
