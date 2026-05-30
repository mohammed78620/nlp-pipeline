from typing import Dict
from unittest.mock import patch

import pytest
from celery.exceptions import Ignore

from nlp_pipeline.tasks.product_extraction_chatgpt import ProductExtractionChatGPT


def mock_openai_response(content: str) -> Dict:
    """
    Dummy representation of what a response from OpenAI looks like.
    """
    return {"choices": [{"message": {"content": content}}]}


@pytest.mark.parametrize(
    "batch, mock_openai_content, expected",
    [
        (
            {"articles": [{"text": "Krusty Krabs is a burger chain restaurant.", "metadata": {}}]},
            "- burgers\n -patties",
            {
                "articles": [
                    {
                        "text": "Krusty Krabs is a burger chain restaurant.",
                        "products": ["burger", "patties"],
                        "metadata": {},
                    }
                ]
            },
        ),
    ],
)
def test_run(batch, mock_openai_content, expected):
    with patch("openai.ChatCompletion.create") as mock_create:
        if mock_openai_content:
            mock_create.side_effect = [mock_openai_response(mock_openai_content)]

        result = ProductExtractionChatGPT().run(batch)

        if mock_openai_content is None:
            mock_create.assert_not_called()
        else:
            mock_create.assert_called_once()

    assert type(result) is type(expected)
    if result is not None:
        for article in result["articles"]:
            assert "products" in article.keys()
            assert "product_extraction" in article["metadata"].keys()


@pytest.mark.parametrize(
    "batch, mock_openai_content, expected",
    [
        (
            None,
            None,
            None,
        ),
        (
            {},
            None,
            None,
        ),
    ],
)
def test_run_ignore_input_task(batch, mock_openai_content, expected):
    """Test input validation of the task."""
    with patch("openai.ChatCompletion.create") as mock_create:
        if mock_openai_content:
            mock_create.side_effect = [mock_openai_response(mock_openai_content)]

        with pytest.raises(Ignore):
            _ = ProductExtractionChatGPT().run(batch)

        if mock_openai_content is None:
            mock_create.assert_not_called()


@pytest.mark.parametrize(
    "batch, mock_openai_content, expected",
    [
        (
            {"articles": [{"text": ""}]},
            None,
            None,
        ),
    ],
)
def test_run_ignore_no_output(batch, mock_openai_content, expected):
    """Test handling of empty article."""
    with patch("openai.ChatCompletion.create") as mock_create:
        if mock_openai_content:
            mock_create.side_effect = [mock_openai_response(mock_openai_content)]

        with pytest.raises(Ignore):
            _ = ProductExtractionChatGPT().run(batch)

        if mock_openai_content is None:
            mock_create.assert_not_called()
