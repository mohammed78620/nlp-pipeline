import time
import traceback
from enum import Enum
from typing import Dict, List, Tuple, Union

from celery.utils.log import get_task_logger
from google.api_core import exceptions
from google.cloud import aiplatform

from nlp_pipeline.exceptions.vertexai import EndpointDoesNotExistError
from nlp_pipeline.settings import (
    DE_ENDPOINT_NAME,
    NEL_ENDPOINT_NAME,
    NER_ENDPOINT_NAME,
    PE_ENDPOINT_NAME,
    RE_ENDPOINT_NAME,
)

logger = get_task_logger(__name__)


class Endpoint(Enum):
    named_entity_recognition = NER_ENDPOINT_NAME
    relation_extraction = RE_ENDPOINT_NAME
    named_entity_linking = NEL_ENDPOINT_NAME
    date_extraction = DE_ENDPOINT_NAME
    product_extraction = PE_ENDPOINT_NAME


class VertexAI:
    def __init__(self, endpoint: Union[str, Endpoint], validate_endpoint: bool = False) -> None:
        self.validate_endpoint = validate_endpoint

        if type(endpoint) is Endpoint:
            self.endpoint_id = self.get_endpoint_id(endpoint.value)
            self.endpoint_name = endpoint.value
        else:
            self.endpoint_id = self.get_endpoint_id(endpoint)
            self.endpoint_name = endpoint

        if self.endpoint_id:
            self.client = aiplatform.Endpoint(self.endpoint_id)
        else:
            logger.warning(f"Endpoint {endpoint} not available. Assuming OK")

    def get_endpoint_id(self, endpoint_name):
        """
        Get endpoint id using endpoint display name
        Returns:
        str: the endpoint id
        """
        try:
            endpoints = aiplatform.Endpoint.list(filter=f"display_name={endpoint_name}")
            endpoint_id = endpoints[0].name
        except Exception:
            if self.validate_endpoint:
                raise EndpointDoesNotExistError(endpoint_name)
            return
        return endpoint_id

    def is_endpoint_up(self) -> bool:
        """
        Check if an endpoint exists in VertexAI.
        Returns:
        bool: True if the endpoint exists, False otherwise.
        """

        try:
            endpoints = aiplatform.Endpoint.list(filter=f"endpoint={self.endpoint_id}")

            if endpoints:
                return True
        except Exception:
            return False
        return False

    def run(self, payload: Dict) -> Tuple[bool, Union[List[Dict], Exception]]:
        success = False
        result = []

        try:
            logger.info(f"Calling endpoint: {self.endpoint_name}")
            start = time.perf_counter()

            response = self.client.predict(instances=payload["instances"])
            predictions = response.predictions
            result = {"predictions": predictions}
            success = True

            end = time.perf_counter()
            time_taken = end - start

            logger.info(f"Success, time taken: {time_taken} seconds")
        except (
            exceptions.DeadlineExceeded,
            exceptions.InternalServerError,
            exceptions.TooManyRequests,
        ) as e:
            # Exceptions that are potentially recoverable if retried with smaller batch
            exception_name = type(e).__name__
            traceback_msg = traceback.format_exc()
            message = f"Endpoint Problem. Failed with exception: {exception_name}.\n\nPayload:\n{payload}"
            message += f"\n\n{traceback_msg}"

            logger.error(message)

            success = False
            result = e
        except KeyError as e:
            # Exceptions that are potentially recoverable if retried with smaller batch
            # keyerror potentially indicates the endpoint returned bad response, which can happen under some
            # error conditions
            exception_name = type(e).__name__
            traceback_msg = traceback.format_exc()
            message = f"Failed with exception: {exception_name}.\n{traceback_msg}"
            logger.error(message)

            success = False
            result = e
        except (exceptions.ServiceUnavailable, Exception) as e:
            if not self.is_endpoint_up():
                logger.error(f"Endpoint {self.endpoint_name} ({self.endpoint_id}) does not exist")
                raise EndpointDoesNotExistError(self.endpoint_id)

            exception_name = type(e).__name__
            logger.error(f"Failed with exception: {exception_name}. The payload was: {payload}")
            raise e
        return success, result
