import math
from typing import Callable, Dict, List, Union

from celery.exceptions import MaxRetriesExceededError
from celery.utils.log import get_task_logger
from pydantic import BaseModel

from nlp_pipeline.celery_app import app
from nlp_pipeline.exceptions.vertexai import EndpointDoesNotExistError
from nlp_pipeline.schema import vertexai as model
from nlp_pipeline.schema.named_entity_linking import NELedArticleBatch
from nlp_pipeline.schema.named_entity_recognition import NERedArticleBatch
from nlp_pipeline.schema.relation_extraction import REedArticeBatch
from nlp_pipeline.schema.segmentation import SegmentedArticleBatch
from nlp_pipeline.utils.common import publish_to_queue
from nlp_pipeline.utils.vertexai import Endpoint, VertexAI

default_validation_settings = {"payload": True, "response": True, "batch_input": False, "batch_output": True}


class ValidationSettings(BaseModel):
    payload: bool = True
    reponse: bool = True
    batch_input: bool = False
    batch_output: bool = True
    nuke_if_no_payload: bool = True


class ValidationModels(BaseModel):
    task_input: Union[SegmentedArticleBatch, NERedArticleBatch, REedArticeBatch, NELedArticleBatch]
    task_output: Union[SegmentedArticleBatch, NERedArticleBatch, REedArticeBatch, NELedArticleBatch]
    endpoint_payload: Union[model.DEPayload, model.NERPayload, model.NELPayload, model.REPayload]
    endpoint_response: Union[model.DEResponse, model.NERResponse, model.NELResponse, model.REResponse]


class Settings(BaseModel):
    name: str
    endpoint: Endpoint
    validation: ValidationSettings
    models: ValidationModels
    get_payload: Callable[[Dict], Dict]
    response_processor: Callable[[Dict, Dict], Dict]
    endpoint_batch_size: int = 20


class VertexAIEndpoint(app.Task):
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 7}
    retry_backoff = True

    def __init__(self, settings: Settings, **kwargs) -> None:
        # validate settings
        self.name = settings["name"]
        self.queue = settings["queue"]
        self.error_queue = settings.get("error_queue", None)
        self.logger = get_task_logger(settings["name"])

        self.vertexai = VertexAI(settings["endpoint"])
        self.endpoint_batch_size = settings["endpoint_batch_size"]
        self.allow_endpoint_failure = settings.get("allow_endpoint_failure", False)

        validation = settings["validation"]
        self.validate_payload = validation["payload"]
        self.validate_response = validation["response"]
        self.validate_batch_input = validation["batch_input"]
        self.validate_batch_output = validation["batch_output"]
        self.nuke = validation["nuke_if_no_payload"]

        models = settings["models"]
        self.task_input_model = models["task_input"]
        self.task_output_model = models["task_output"]
        self.endpoint_payload_model = models["endpoint_payload"]
        self.endpoint_response_model = models["endpoint_response"]

        super().__init__(**kwargs)

    def get_subbatch_size(self) -> int:
        """
        Determine the sub-batch size to hit an endpoint with. Based on whether retries
        have been attempted the sub-batch size will be smaller.

        Returns:
            int: The sub-batch size
        """
        try:
            num_retries = self.request.retries
        except Exception:
            # This is a work around for unittests that don't strictly run tasks correctly
            # causing the request object to not initialise properly
            self.logger.error("Problem getting the number of retries from the Task request.")
            num_retries = 0

        if self.endpoint_batch_size == 1:
            # no point trying to reduce further
            return self.endpoint_batch_size

        size = math.floor(self.endpoint_batch_size // (2**num_retries))

        if size < 1:
            size = 1
            self.logger.warning("Endpoint batch size can't be reduced any further.")

        return size

    def run(self, batch, validate: bool = None):
        if validate is not None:
            self.validate_payload = validate
            self.validate_response = validate
            self.validate_batch_input = validate
            self.validate_batch_output = validate

        # Handle input
        if self.validate_batch_input:
            batch = self.task_input_model(**batch).model_dump(by_alias=True)

        if len(batch["articles"]) == 0:
            self.logger.info("No articles. Doing nothing.")
            return batch

        # Generate payloads
        payloads = self.payloads_generator(batch)

        if not payloads:
            if self.nuke:
                self.logger.info("No payload to send. Nuking articles.")
                batch["articles"] = []
            else:
                self.logger.info("No payload to send. Doing nothing.")
            return batch

        # Hit endpoint
        response = self.batch_query(payloads)

        # Process endpoint response
        output = self.process_response(batch, response)

        # Handle output
        if self.validate_batch_output:
            output = self.task_output_model(**output).model_dump(by_alias=True)

        return output

    def batch_query(self, payloads):
        result = {}

        for payload in payloads:
            if self.validate_payload:
                payload = self.endpoint_payload_model(**payload).model_dump(by_alias=True)

            try:
                successful, response = self.vertexai.run(payload)
            except EndpointDoesNotExistError as e:
                self.logger.info(self._exec_options)
                try:
                    app.control.cancel_consumer(self.queue)
                except Exception:
                    # This throws an exception if celery isnt running
                    self.logger.exception("Problem while canceling celery consumer due to missing Vertex AI endpoint")
                raise e

            if successful:
                if self.validate_response:
                    response = self.endpoint_response_model(**response).model_dump(by_alias=True)

                result = self.merge_response(result, response)
            else:
                try:
                    self.retry()
                except MaxRetriesExceededError as e:
                    message = f"Max retries reached querying Endpoint {self.vertexai.endpoint_name} ({self.vertexai.endpoint_id})."
                    if self.allow_endpoint_failure:
                        message += " But allowed to fail as considered optional..."
                        self.logger.warning(message)
                        return {}
                    else:
                        # stop all subsequent tasks in the chain
                        if hasattr(self, "request"):
                            self.request.chain = None

                            if self.error_queue is not None:
                                publish_to_queue(app, self.request.args, self.error_queue)
                                message += f" Published failing batch to {self.error_queue}."

                        self.logger.error(message)
                        raise e

        return result

    def payloads_generator(self, batch: List):
        # Override in derived class
        raise NotImplementedError()

    def process_response(self, batch: List, response):
        # Override in derived class
        raise NotImplementedError()

    def merge_response(self, responses, response):
        if not responses:
            return response

        if type(responses["predictions"]) is dict and type(response["predictions"]) is dict:
            responses["predictions"] = responses["predictions"] | response["predictions"]
        elif type(responses["predictions"]) is list and type(response["predictions"]) is list:
            responses["predictions"] += response["predictions"]
        else:
            raise TypeError("Unexpected type in predictions.")

        return responses
