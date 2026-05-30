from typing import Dict, List

from nlp_pipeline.celery_app import app
from nlp_pipeline.schema import vertexai as model
from nlp_pipeline.schema.named_entity_recognition import NERedArticleBatch
from nlp_pipeline.schema.relation_extraction import REedArticeBatch
from nlp_pipeline.settings import RE_BATCH_SIZE
from nlp_pipeline.tasks.vertexai_endpoint import VertexAIEndpoint
from nlp_pipeline.utils.vertexai import Endpoint


class RelationExtraction(VertexAIEndpoint):
    def __init__(self, **kwargs) -> None:
        settings = {
            "name": "Relation Extraction",
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
        super().__init__(settings, **kwargs)

    def get_empty_payload(self) -> Dict:
        payload = {"data": []}
        return payload

    def payloads_generator(self, article_batch: NERedArticleBatch) -> List[model.REPayload]:

        payloads = []
        payload = self.get_empty_payload()

        for article in article_batch["articles"]:
            sentences = article["sentences"]
            for sentence in sentences:
                # RE only cares if there's more than 1 entity
                if len(sentence["entities"]) > 1:
                    annotation = {
                        "annotation": {
                            "entities": sentence["entities"],
                        },
                        "id": sentence["id"],
                        "text": sentence["text"],
                    }
                    payload["data"].append(annotation)

                    if len(payload["data"]) == self.endpoint_batch_size:
                        payloads.append(payload)
                        payload = self.get_empty_payload()

        if len(payload["data"]) > 0:
            payloads.append(payload)
            payload = self.get_empty_payload()

        return payloads

    def process_response(self, article_batch: NERedArticleBatch, response: model.REResponse) -> REedArticeBatch:
        """
        Handle endpoint response by optionally validating it and filtering out articles
        that have no entities

        Args:
            article_batch (NERedArticleBatch): The article batch being processed
            response (REResponse): The RE Sagemaker endpoint response

        Returns:
            REedArticeBatch: Processed articles that have RE data.
        """

        # Append results to original data & Remove empty sentences
        for article_index, article in enumerate(article_batch["articles"]):
            # index throught sentences in reverse to avoid skipping element after deletion
            for sentence_index in range(len(article["sentences"]) - 1, -1, -1):
                try:
                    sentence_id = article["sentences"][sentence_index]["id"]
                    relations = response["predictions"][sentence_id]
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
