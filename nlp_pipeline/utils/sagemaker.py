import json
import time
from enum import Enum
from typing import Dict, List, Tuple, Union

import boto3
import botocore
from celery.utils.log import get_task_logger

from nlp_pipeline.exceptions.sagemaker import EndpointDoesNotExistError
from nlp_pipeline.settings import (
    AWS_CONNECT_TIMEOUT,
    AWS_READ_TIMEOUT,
    DE_ENDPOINT_NAME,
    NEL_ENDPOINT_NAME,
    NER_ENDPOINT_NAME,
    PE_ENDPOINT_NAME,
    RE_ENDPOINT_NAME,
    SAGEMAKER_REGION,
)

logger = get_task_logger(__name__)

config = botocore.client.Config(
    connect_timeout=AWS_CONNECT_TIMEOUT,
    read_timeout=AWS_READ_TIMEOUT,
    retries={"max_attempts": 15, "mode": "adaptive"},
)


class Endpoint(Enum):
    named_entity_recognition = NER_ENDPOINT_NAME
    relation_extraction = RE_ENDPOINT_NAME
    named_entity_linking = NEL_ENDPOINT_NAME
    date_extraction = DE_ENDPOINT_NAME
    product_extraction = PE_ENDPOINT_NAME


class SageMaker:
    def __init__(self, endpoint: Union[str, Endpoint]) -> None:
        self.client = boto3.client("sagemaker-runtime", region_name=SAGEMAKER_REGION, config=config)
        self.sagemaker_client = boto3.client("sagemaker", region_name=SAGEMAKER_REGION)

        if type(endpoint) is Endpoint:
            self.endpoint = endpoint.value
        else:
            self.endpoint = endpoint

    def is_endpoint_up(self) -> bool:
        """
        Returns True if self.endpoint exists on our AWS account, False otherwise
        """
        return (
            True
            if self.endpoint
            in [item["EndpointName"] for item in self.sagemaker_client.list_endpoints(MaxResults=100)["Endpoints"]]
            else False
        )

    def is_aws_credentials_valid(self):
        try:
            sts = boto3.client("sts")
            sts.get_caller_identity()
            return True

        except boto3.exceptions.ClientError:
            logger.error("AWS credentials are NOT valid.")
            return False

    def run(self, payload: Dict) -> Tuple[bool, List[Dict]]:
        body = json.dumps(payload, ensure_ascii=False)
        success = False

        try:
            logger.info(f"Calling endpoint: {self.endpoint}")
            start = time.perf_counter()

            response = self.client.invoke_endpoint(EndpointName=self.endpoint, Body=body)
            result = json.loads(response["Body"].read().decode())

            if "error" in result.keys():
                raise ValueError(result["error"])

            success = True

            end = time.perf_counter()
            time_taken = end - start

            logger.info(f"Success, time taken: {time_taken} seconds")
        except (
            self.client.exceptions.InternalFailure,
            self.client.exceptions.InternalDependencyException,
            self.client.exceptions.ModelError,
            self.client.exceptions.ModelNotReadyException,
            botocore.exceptions.ReadTimeoutError,
        ) as e:
            # Exceptions that are likely to be recoverable if retried with smaller batch

            exception_name = type(e).__name__
            logger.error(f"Failed with exception: {exception_name}.")

            success = False
            result = e
        except (
            self.client.exceptions.ServiceUnavailable,
            self.client.exceptions.ValidationError,
            Exception,  # eh, just in case I guess.
        ) as e:
            # Exceptions that may work with a retry but batch since unlikely to affect the outcome
            if not self.is_endpoint_up():
                logger.error(f"Endpoint {self.endpoint} does not exist")
                raise EndpointDoesNotExistError(self.endpoint)

            exception_name = type(e).__name__
            logger.error(f"Failed with exception: {exception_name}. The payload was: {body}")
            raise (e)
        return success, result
