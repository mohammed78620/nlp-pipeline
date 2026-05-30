"""
Task: BoL Product Extraction

Take BoL product descriptions for extraction with the aid of a LLM.
"""

from typing import Dict, List, Optional

import pydantic
import ujson
from celery.utils.log import get_task_logger

from nlp_pipeline.celery_app import app
from nlp_pipeline.schema.directory_reader_bol_product_extraction import (
    BOLProductExtractedArticle,
    BOLProductPrecleanedArticle,
)
from nlp_pipeline.settings import (
    BOL_PE_EXTRACTION_BLOCK_TERMS,
    BOL_PE_EXTRACTION_PROMPT,
    BOL_PE_GCP_LOCATION,
    BOL_PE_HYPERPARAMETERS,
    BOL_PE_LLM_MODEL,
    GOOGLE_PROJECT_ID,
)
from nlp_pipeline.utils.products import Products
from nlp_pipeline.utils.vertexai_text_generation import LLMPrediction

logger = get_task_logger(__name__)


class BolProductExtraction(app.Task):
    name = "BoL Product Extraction"

    def __init__(
        self,
        gcp_project: str = GOOGLE_PROJECT_ID,
        gcp_location: str = BOL_PE_GCP_LOCATION,
        llm_model: str = BOL_PE_LLM_MODEL,
        base_prompt: str = BOL_PE_EXTRACTION_PROMPT,
        hyperparams: Dict = BOL_PE_HYPERPARAMETERS,
        block_terms: List[str] = BOL_PE_EXTRACTION_BLOCK_TERMS,
        **kwargs,
    ) -> None:

        self.project = gcp_project
        self.location = gcp_location
        self.llm_model = llm_model
        self.base_prompt = base_prompt
        self.hyperparams = hyperparams

        self.llm_model_caller = LLMPrediction(
            project=self.project,
            location=self.location,
            llm_model=self.llm_model,
            hyperparams=self.hyperparams,
        )

        # How many attempts to get a product extraction
        self.num_retries = 3

        self.block_terms = block_terms
        if not block_terms:
            self.block_terms = ["unknown"]
        self.block_terms = [term.upper() for term in self.block_terms]

        super().__init__(**kwargs)

    def format_products(self, products: str) -> Optional[List[str]]:
        """
        Take the text result from query (expected to be a comma seperated list) and convert to
        list of products.

        Args:
            products (str): The text result of a query

        Returns:
            Optional[List[str]]: The result if any products were able to be converted
        """
        if not products:
            return

        products = products.split(",")
        if len(products) == 0:
            return

        products = [product.strip() for product in products]
        return products

    def clean_products(self, products: List[str]) -> List[str]:
        """
        Clean products by normalize to uppercase, drop blacklisted products.

        Args:
            products (List[str]): The products to be cleaned

        Returns:
            List[str]: The result
        """
        clean_products = []

        if not products:
            return clean_products

        for product in products:
            product = product.strip().upper()

            if not product:
                continue
            elif product in self.block_terms:
                # Blocked term, don't add to products list
                continue

            clean_products.append(product)

        # apply non-task specific product processing rules
        clean_products = Products.process(clean_products)

        return clean_products

    def form_query(self, text: str) -> str:
        """
        Form query prompt that's to be sent to LLM by combining text with base_prompt.

        Args:
            text (str): Text individual to the base prompt e.g. comma seperated products to be cleaned.

        Returns:
            str: The result.
        """
        if not self.base_prompt.endswith(" "):
            self.base_prompt += " "

        query_prompt = self.base_prompt + text
        return query_prompt

    def perform_query(self, text: str) -> Optional[List[str]]:
        """
        Send text off to LLM for product extraction.

        Args:
            text (str): Text containing product description(s)

        Returns:
            Optional[List[str]]: Resulting list of products, if any.
        """
        query_prompt = self.form_query(text)

        for attempt_num in range(self.num_retries):
            result = self.llm_model_caller.text_prediction(query_prompt)

            if not self.llm_model_caller.is_good_result(result):
                if attempt_num >= self.num_retries - 1:
                    msg = f"Bad result during extraction: '{text}'. "
                    msg += f"Blocked: {result.is_blocked}, Errors: {result.errors}"
                    logger.warning(msg)
                continue

            # get text from result
            products_str = self.llm_model_caller.get_result_text(result)

            products = self.format_products(products_str)
            if products == ["UNKNOWN"]:
                # Don't retry if no products is just "UNKNOWN".
                return

            clean_products = self.clean_products(products)
            if clean_products:
                # Good result
                return clean_products

    def update_record(self, record: Dict, products: List[str]) -> Optional[Dict]:
        """
        Update record with appropriate metadata and extracted products.

        Args:
            record (Dict): BOLProductPrecleanedArticle compatible record
            products (List[str]): The products extracted from the record

        Returns:
            Optional[Dict]: The resulting BOLProductExtractedArticle compatible record
        """
        if not products:
            return

        record["llm_extracted_products"] = products

        # apply metadata to record
        metadata = record["processes"][-1]
        metadata["intermediary_texts"]["product_extraction"] = record["llm_cleaned_text"]
        metadata["prompts"]["product_extraction_prompt"] = self.base_prompt
        record["processes"][-1] = metadata

        # remove fields no longer needed
        del record["llm_cleaned_text"]

        try:
            BOLProductExtractedArticle.model_validate(record)
        except pydantic.ValidationError as e:
            msg = "Invalid output article for BOL Product Extraction. "
            msg += f"article: {ujson.dumps(record)}\n"
            msg += f"{e}"
            logger.error(msg)
            return
        return record

    def run(self, batch: List[Dict]) -> List[Dict]:
        """
        Extract products from a batch of articles.

        Args:
            batch (List[Dict]): List of BOLProductPrecleanedArticle compatible dicts to process.

        Returns:
            List[Dict]: Resulting articles that are BOLProductExtractedArticle compatible.
        """
        output = []

        for record in batch:
            # Validate
            try:
                BOLProductPrecleanedArticle.model_validate(record)
            except pydantic.ValidationError as e:
                msg = "Invalid incoming article for BOL Product Extraction. "
                msg += f"article: {ujson.dumps(record)}\n"
                msg += f"{e}"
                logger.error(msg)
                continue

            # perform extraction
            text = record["llm_cleaned_text"]
            products = self.perform_query(text)
            if not products:
                continue

            # update record
            record = self.update_record(record, products)

            if record:
                output.append(record)

        return output


# app.register_task(BolProductExtraction())
