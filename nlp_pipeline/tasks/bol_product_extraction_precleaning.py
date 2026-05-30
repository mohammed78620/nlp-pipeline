"""
Task: BoL Product Extraction Precleaning

Take BoL product descriptions that are intended to be passed to BolProductExtraction
and clean with the aid of a LLM.
"""

from typing import Dict, List, Optional

import pydantic
import ujson
from celery.utils.log import get_task_logger

from nlp_pipeline.celery_app import app
from nlp_pipeline.schema.directory_reader_bol_product_extraction import (
    BOLProductArticle,
    BOLProductPrecleanedArticle,
)
from nlp_pipeline.settings import (
    BOL_PE_GCP_LOCATION,
    BOL_PE_HYPERPARAMETERS,
    BOL_PE_LLM_MODEL,
    BOL_PE_PRECLEANING_PROMPT,
    BOL_PE_PRECLEANING_STRIP_TERMS,
    GOOGLE_PROJECT_ID,
)
from nlp_pipeline.utils.vertexai_text_generation import LLMPrediction

logger = get_task_logger(__name__)


class BolProductExtractionPrecleaning(app.Task):
    """
    Use LLM and simple rules to clean BOL Product Descriptions.
    """

    name = "BoL Product Extraction Precleaning"

    def __init__(
        self,
        gcp_project: str = GOOGLE_PROJECT_ID,
        gcp_location: str = BOL_PE_GCP_LOCATION,
        llm_model: str = BOL_PE_LLM_MODEL,
        base_prompt: str = BOL_PE_PRECLEANING_PROMPT,
        hyperparams: Dict = BOL_PE_HYPERPARAMETERS,
        strip_terms: List[str] = BOL_PE_PRECLEANING_STRIP_TERMS,
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

        # How many attempts to clean product description
        self.num_retries = 3

        self.strip_terms = [term.upper().strip() for term in strip_terms]
        super().__init__(**kwargs)

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

    def clean_product_description(self, text: str) -> Optional[str]:
        """
        Perform simple cleaning on product description i.e. uppercase and strip defined terms.

        Args:
            text (str): A product description e.g. "nuts, BOLTS"

        Returns:
            Optional[str]: The resulting cleaned product description
        """
        text = text.upper()

        for strip_term in self.strip_terms:
            text = text.replace(strip_term, "")

        text = text.strip()
        if not text:
            return

        return text

    def perform_query(self, text: str) -> Optional[str]:
        """
        Send text off to LLM for product cleaning.

        Args:
            text (str): Text containing product description(s)

        Returns:
            Optional[str]: Resulting cleaned product description, if any.
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
            product_description = self.llm_model_caller.get_result_text(result)

            # apply simple post cleaning to the LLM cleaning
            product_description = self.clean_product_description(product_description)
            if product_description:
                return product_description

    def update_record(self, record: Dict, cleaned_text: str) -> Optional[Dict]:
        """
        Update record with appropriate metadata and cleaned text.

        Args:
            record (Dict): BOLProductArticle compatible record
            cleaned_text (str): The text this task cleaned

        Returns:
            Optional[Dict]: The resulting BOLProductPrecleanedArticle compatible record
        """
        if not cleaned_text:
            return

        record["llm_cleaned_text"] = cleaned_text

        # apply metadata
        metadata = record["processes"][-1]
        metadata["intermediary_texts"] = {"text_cleaning": record["text"]}
        metadata["prompts"] = {"text_cleaning_prompt": self.base_prompt}
        metadata["llm_model"] = self.llm_model
        record["processes"][-1] = metadata

        # Validate
        try:
            BOLProductPrecleanedArticle.model_validate(record)
        except pydantic.ValidationError as e:
            msg = "Invalid output article for BOL Product Precleaning. "
            msg += f"article: {ujson.dumps(record)}\n"
            msg += f"{e}"
            logger.error(msg)
            return
        return record

    def run(self, batch: List[Dict]) -> List[Dict]:
        """
        Preclean a batch of articles to be ready for extraction.

        Args:
            batch (List[Dict]): List of BOLProductArticle compatible dicts to process.

        Returns:
            List[Dict]: Resulting articles that are BOLProductPrecleanedArticle compatible.
        """
        output = []

        for record in batch:
            # Validate
            try:
                BOLProductArticle.model_validate(record)
            except pydantic.ValidationError as e:
                msg = "Invalid incoming article for BOL Product Precleaning. "
                msg += f"article: {ujson.dumps(record)}\n"
                msg += f"{e}"
                logger.error(msg)
                continue

            # perform cleaning
            text = record["text"]
            cleaned_text = self.perform_query(text)
            if not cleaned_text:
                continue

            # update record
            record = self.update_record(record, cleaned_text)

            if record:
                output.append(record)

        return output


# app.register_task(BolProductExtractionPrecleaning())
