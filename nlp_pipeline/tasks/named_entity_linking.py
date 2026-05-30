from typing import Dict, List

from nlp_pipeline.celery_app import app
from nlp_pipeline.schema import vertexai as model
from nlp_pipeline.schema.named_entity_linking import NELedArticleBatch
from nlp_pipeline.schema.relation_extraction import REedArticeBatch
from nlp_pipeline.settings import NEL_BATCH_SIZE, environment
from nlp_pipeline.tasks.vertexai_endpoint import VertexAIEndpoint
from nlp_pipeline.utils.vertexai import Endpoint


class NamedEntityLinking(VertexAIEndpoint):
    def __init__(self, **kwargs) -> None:
        settings = {
            "name": "Named Entity Linking",
            "queue": environment("NAMED_ENTITY_LINKING_QUEUE_NAME"),
            "endpoint": Endpoint.named_entity_linking,
            "endpoint_batch_size": NEL_BATCH_SIZE,
            "allow_endpoint_failure": True,
            "validation": {
                "payload": True,
                "response": True,
                "batch_input": True,
                "batch_output": True,
                "nuke_if_no_payload": True,
            },
            "models": {
                "task_input": REedArticeBatch,
                "task_output": NELedArticleBatch,
                "endpoint_payload": model.NELPayload,
                "endpoint_response": model.NELResponse,
            },
        }
        super().__init__(settings, **kwargs)

    batch_size: int

    def get_empty_payload(self) -> Dict:
        payload = {"instances": []}
        return payload

    def payloads_generator(self, article_batch: REedArticeBatch) -> List[model.NELPayload]:
        """
        Construct a payload suitable for the NEL Vertex AI endpoint.
        """
        payloads = []
        payload = self.get_empty_payload()

        for article in article_batch["articles"]:
            for sentence in article["sentences"]:
                text_evidence = {}
                text_evidence["id"] = sentence["id"]
                text_evidence["text"] = sentence["text"]
                text_evidence["annotation"] = {"entities": sentence["entities"]}

                payload["instances"].append(text_evidence)

                if len(payload["instances"]) == self.get_subbatch_size():
                    payloads.append(payload)
                    payload = self.get_empty_payload()

        if len(payload["instances"]) > 0:
            payloads.append(payload)
            payload = self.get_empty_payload()

        return payloads

    def process_response(self, article_batch, response: model.NELResponse) -> Dict:
        """
        Handle endpoint response by optionally validating it.

        Args:
            article_batch (REedArticleBatch): The batch of articles being processed.
            response (model.NELResponse): The NEL Vertex AI endpoint response.

        Returns:
            NELedArticleBatch: Processed articles that have NEL data.
        """
        predictions = {}

        if not response:
            return article_batch

        for prediction in response["predictions"]:
            predictions.update(prediction)

        for article_index, article in enumerate(article_batch["articles"]):
            for sentence_index, sentence in enumerate(article["sentences"]):
                pred_ent = predictions[str(sentence["id"])]
                article_batch["articles"][article_index]["sentences"][sentence_index]["entities"] = pred_ent

        return article_batch


app.register_task(NamedEntityLinking())
