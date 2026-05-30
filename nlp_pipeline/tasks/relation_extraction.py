from typing import Dict, List

from nlp_pipeline.celery_app import app
from nlp_pipeline.schema import vertexai as model
from nlp_pipeline.schema.named_entity_recognition import NERedArticleBatch
from nlp_pipeline.schema.relation_extraction import REedArticeBatch
from nlp_pipeline.settings import (
    RE_BATCH_SIZE,
    RE_MAX_ENTITIES,
    RE_MAX_TIME_COST,
    RE_TIME_COST,
    RELATION_EXTRACTION_ERROR_QUEUE_NAME,
    environment,
)
from nlp_pipeline.tasks.vertexai_endpoint import VertexAIEndpoint
from nlp_pipeline.utils.vertexai import Endpoint


class RelationExtraction(VertexAIEndpoint):
    def __init__(self, **kwargs) -> None:
        settings = {
            "name": "Relation Extraction",
            "queue": environment("RELATION_EXTRACTION_QUEUE_NAME"),
            "error_queue": RELATION_EXTRACTION_ERROR_QUEUE_NAME,
            "endpoint": Endpoint.relation_extraction,
            "endpoint_batch_size": RE_BATCH_SIZE,
            "validation": {
                "payload": True,
                "response": True,
                "batch_input": True,
                "batch_output": True,
                "nuke_if_no_payload": True,
            },
            "models": {
                "task_input": NERedArticleBatch,
                "task_output": REedArticeBatch,
                "endpoint_payload": model.REPayload,
                "endpoint_response": model.REResponse,
            },
        }

        # Max number entities a sentence may have otherwise it is skipped
        self.max_num_entities = RE_MAX_ENTITIES
        # How long it takes for RE endpoint to determine a relation between 2 entities
        self.base_time_cost = RE_TIME_COST
        # The max permitted estimated time value to compute a payload i.e. how long it takes for
        # the endpoint to timeout. Payloads will try to sub-batch to stay under this but if a sentence's
        # time cost is higher it will be skipped.
        self.max_time_cost = RE_MAX_TIME_COST

        super().__init__(settings, **kwargs)

    def get_empty_payload(self) -> Dict:
        payload = {"instances": []}
        return payload

    def estimate_time_cost(self, num_entities: int) -> int:
        """
        Estimate how long it would take RE to complete based on the number of entities in the sentence.

        Args:
            num_entities (int): Number of entities in the sentence being estimated.

        Returns:
            int: The estimated time to complete (in milliseconds)
        """
        num_checks = (num_entities * (num_entities - 1)) / 2
        cost = self.base_time_cost * num_checks
        return cost

    def payloads_generator(self, article_batch: NERedArticleBatch) -> List[model.REPayload]:
        running_cost = 0
        payloads = []
        payload = self.get_empty_payload()

        for article in article_batch["articles"]:
            sentences = article["sentences"]
            for sentence in sentences:
                num_entities = len(sentence["entities"])

                # Skip if sentence has too many entities or too few
                if num_entities > self.max_num_entities or num_entities < 2:
                    continue

                estimated_cost = self.estimate_time_cost(num_entities)

                # Skip if sentence would cause a timeout.
                if estimated_cost > self.max_time_cost:
                    continue

                annotation = {
                    "annotation": {
                        "entities": sentence["entities"],
                    },
                    "id": sentence["id"],
                    "text": sentence["text"],
                }

                # If adding annotation to batch would put it above the time cost limit,
                # Start a new batch
                if running_cost + estimated_cost > self.max_time_cost:
                    payloads.append(payload)
                    payload = self.get_empty_payload()
                    running_cost = 0

                running_cost += estimated_cost
                payload["instances"].append(annotation)

                # Alternatively, payload complete if is batch size reached
                if len(payload["instances"]) == self.get_subbatch_size():
                    payloads.append(payload)
                    payload = self.get_empty_payload()
                    running_cost = 0

        if len(payload["instances"]) > 0:
            payloads.append(payload)
            payload = self.get_empty_payload()
            running_cost = 0

        return payloads

    def process_response(self, article_batch: NERedArticleBatch, response: model.REResponse) -> REedArticeBatch:
        """
        Handle endpoint response by optionally validating it and filtering out articles
        that have no entities

        Args:
            article_batch (NERedArticleBatch): The article batch being processed
            response (REResponse): The RE Vertex AI endpoint response

        Returns:
            REedArticeBatch: Processed articles that have RE data.
        """
        predictions = {}
        for prediction in response["predictions"]:
            predictions.update(prediction)

        # Append results to original data
        for article_index, article in enumerate(article_batch["articles"]):
            # index throught sentences in reverse to avoid skipping element after deletion
            for sentence_index in range(len(article["sentences"]) - 1, -1, -1):
                try:
                    sentence_id = article["sentences"][sentence_index]["id"]
                    relations = predictions[sentence_id]
                    article_batch["articles"][article_index]["sentences"][sentence_index]["relations"] = relations
                except KeyError:
                    del article_batch["articles"][article_index]["sentences"][sentence_index]

        # Remove articles that lack sentences from end to start of articles list
        # index throught articles in reverse to avoid skipping element after deletion
        for article_index in range(len(article_batch["articles"]) - 1, -1, -1):
            if len(article_batch["articles"][article_index]["sentences"]) == 0:
                del article_batch["articles"][article_index]

        return article_batch


app.register_task(RelationExtraction())
