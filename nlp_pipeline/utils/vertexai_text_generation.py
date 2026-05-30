import logging
import random
import time
from typing import Dict, Union

from google.api_core.exceptions import ResourceExhausted
from google.cloud import aiplatform
from google.cloud.aiplatform.jobs import BatchPredictionJob
from pydantic import BaseModel
from vertexai.language_models._language_models import MultiCandidateTextGenerationResponse
from vertexai.preview.language_models import TextGenerationModel

# define the logger
logger = logging.getLogger(__name__)


def retry_with_exponential_backoff(
    func,
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    max_retries: int = 3,
    errors: tuple = (
        ResourceExhausted,
        Exception,
    ),
):
    """
    Retry decorator with exponential backoff and optional jitter.

    Args:
        func (callable): The function to be retried.
        initial_delay (float, optional): Initial delay before the first retry, in
            seconds. Default is 1 second.
        exponential_base (float, optional): The base value for exponential delay growth.
            Default is 2.
        jitter (bool, optional): jitter acts as a toggle for randomness to the delay.
            Default is True.
        max_retries (int, optional): Maximum number of retry attempts. Default is 3.
        errors (tuple, optional): Tuple of exception classes that trigger retries.
            Default includes ResourceExhausted and Exception.

    Returns:
        callable: A wrapper function that implements the retry mechanism.
    """

    def wrapper(*args, **kwargs):

        # define the number of retries and the initial delay
        num_retries = 0
        delay = initial_delay

        # loop until a successful response or max_retries is hit or an exception raised
        while True:
            try:
                return func(*args, **kwargs)
            except errors as e:
                if hasattr(e, "json_body"):

                    # handle very specific exception from GCP from insufficient_quota
                    error_type = e.json_body.get("error", {}).get("type", None)
                    if error_type == "RESOURCE_EXHAUSTED":

                        # can not recover from quota issues, just abort.
                        raise e

                # increase the number of retries
                num_retries += 1

                # raise error if max retries exceeded
                if num_retries > max_retries:
                    logger.debug("Maximum number of retries %s exceeded.", max_retries)
                    raise e

                # update the delay
                delay *= exponential_base * (1 + jitter * random.random())  # nosec B311 , not security critical

                # sleep for the defined delay
                time.sleep(delay)

    return wrapper


class LLMHyperparameters(BaseModel):
    temperature: float
    max_output_tokens: int
    top_p: float
    top_k: int


class LLMPrediction:
    """
    Class that prepares the LLM batch processing job.
    """

    def __init__(self, project: str, location: str, llm_model: str, hyperparams: Union[Dict, LLMHyperparameters]):
        """
        Init

        Args:
            project (str): Google Project ID
            location (str): Project location/region e.g. us-central1
            llm_model (str): Model name e.g. text-bison@001
            hyperparams (Dict): The hyperparameters to use
        """
        # define the project and location
        aiplatform.init(project=project, location=location)

        self.llm_model_name = llm_model
        self.llm_model = TextGenerationModel.from_pretrained(self.llm_model_name)

        if isinstance(hyperparams, LLMHyperparameters):
            self.model_parameters = hyperparams.model_dump(by_alias=True)
        elif type(hyperparams) is dict:
            self.model_parameters = {
                "temperature": hyperparams["temperature"],
                "max_output_tokens": hyperparams["max_output_tokens"],
                "top_p": hyperparams["top_p"],
                "top_k": hyperparams["top_k"],
            }
        else:
            raise ValueError("Invalid hyperparams.")

    @retry_with_exponential_backoff
    def batch_prediction(
        self,
        gcp_bucket_name: str,
        gcp_input_prompt_jsonl_file_path: str,
        gcp_output_prediction_jsonl_file_path: str,
    ) -> BatchPredictionJob:
        """
        Use batch prediction to predict run a set of prompts stored in a JSONL file on
        GCP.
        """

        # define the input folder uri
        source_uri = f"gs://{gcp_bucket_name}/{gcp_input_prompt_jsonl_file_path}"

        # define the output folder uri
        destination_uri_prefix = f"gs://{gcp_bucket_name}/{gcp_output_prediction_jsonl_file_path}"

        # define the text bison batch prediction
        batch_prediction_job = self.llm_model.batch_predict(
            dataset=[source_uri],
            destination_uri_prefix=destination_uri_prefix,
            instanceConfig={"excludedFields": ["bol_record"]},
            model_parameters=self.model_parameters,
        )

        return batch_prediction_job

    @retry_with_exponential_backoff
    def text_prediction(
        self,
        prompt: str,
    ) -> MultiCandidateTextGenerationResponse:
        """
        Send a text for prediction against the configured model.

        Args:
            prompt (str): The prompt to be sent.

        Returns:
            MultiCandidateTextGenerationResponse: The resulting response
        """

        # define the text bison batch prediction
        result = self.llm_model.predict(
            prompt=prompt,
            temperature=self.model_parameters["temperature"],
            max_output_tokens=self.model_parameters["max_output_tokens"],
            top_k=self.model_parameters["top_k"],
            top_p=self.model_parameters["top_p"],
        )

        return result

    def is_good_result(self, result: MultiCandidateTextGenerationResponse) -> bool:
        """
        Return whether or not a result was successful i.e. not blocked and no errors.

        Args:
            result (MultiCandidateTextGenerationResponse): The result to check

        Returns:
            bool: Whether or not it was successful
        """
        # example check result from endpoint is good
        if len(result.errors) != 0 or result.is_blocked:
            return False
        return True

    def get_result_text(self, result: MultiCandidateTextGenerationResponse) -> str:
        """
        Extract the text of a result response

        Args:
            result (MultiCandidateTextGenerationResponse): The response to select the text from

        Returns:
            str: The result
        """
        result_text = result.candidates[0].text
        return result_text
