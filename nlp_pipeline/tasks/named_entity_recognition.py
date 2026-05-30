import copy
from typing import List

from nlp_pipeline.celery_app import app
from nlp_pipeline.schema import vertexai as model
from nlp_pipeline.schema.named_entity_recognition import NERedArticleBatch
from nlp_pipeline.schema.segmentation import SegmentedArticleBatch
from nlp_pipeline.schema.vertexai.response.named_entity_recognition import Entity
from nlp_pipeline.settings import NAMED_ENTITY_RECOGNITION_ERROR_QUEUE_NAME, NER_BATCH_SIZE, environment
from nlp_pipeline.tasks.vertexai_endpoint import VertexAIEndpoint
from nlp_pipeline.utils.vertexai import Endpoint


class NamedEntityRecognition(VertexAIEndpoint):
    def __init__(self, **kwargs) -> None:
        settings = {
            "name": "Named Entity Recognition",
            "queue": environment("NAMED_ENTITY_RECOGNITION_QUEUE_NAME"),
            "error_queue": NAMED_ENTITY_RECOGNITION_ERROR_QUEUE_NAME,
            "endpoint": Endpoint.named_entity_recognition,
            "endpoint_batch_size": NER_BATCH_SIZE,
            "validation": {
                "payload": True,
                "response": True,
                "batch_input": True,
                "batch_output": True,
                "nuke_if_no_payload": True,
            },
            "models": {
                "task_input": SegmentedArticleBatch,
                "task_output": NERedArticleBatch,
                "endpoint_payload": model.NERPayload,
                "endpoint_response": model.NERResponse,
            },
        }
        super().__init__(settings, **kwargs)

    def payloads_generator(self, article_batch: SegmentedArticleBatch) -> List[model.NERPayload]:
        payloads = []
        payload = {"instances": []}

        for article in article_batch["articles"]:
            sentences = article["sentences"]
            for sentence in sentences:
                payload["instances"].append(sentence)

                if len(payload["instances"]) == self.get_subbatch_size():
                    payloads.append(payload)
                    payload = {"instances": []}

        if len(payload["instances"]) > 0:
            payloads.append(payload)
            payload = {"instances": []}
        return payloads

    def process_response(self, article_batch: SegmentedArticleBatch, response: model.NERResponse) -> NERedArticleBatch:
        """
        Handle endpoint response by optionally validating it and filtering out articles
        that have no entities

        Args:
            article_batch (SegmentedArticleBatch): The article batch being processed
            response (model.NERResponse): The NER Vertex AI endpoint response

        Returns:
            NERedArticleBatch: Processed articles that have NER data.
        """
        # Need to ensure batch data is carried through.
        output = copy.deepcopy(article_batch)

        # But clear the `articles`` in copy as they'll be reconstructed in reaction
        # to the response data
        output["articles"] = []

        predictions = {}
        for prediction in response["predictions"]:
            predictions.update(prediction)

        for article in article_batch["articles"]:
            amended_article = None

            for sentence in article["sentences"]:
                sentence_id = sentence["id"]

                # only keep sentences that have predictions
                if sentence_id in predictions.keys():
                    entities: List[Entity] = predictions[sentence_id]

                    # only keep sentences that have entities
                    if entities:
                        amended_sentence = copy.deepcopy(sentence)
                        amended_sentence["entities"] = entities

                        # only keep articles that have atleast 1 amended sentence
                        if amended_article:
                            amended_article["sentences"].append(amended_sentence)
                        else:
                            amended_article = copy.deepcopy(article)
                            amended_article["sentences"] = [amended_sentence]

            if amended_article and amended_article["sentences"]:
                output["articles"].append(amended_article)
        return output


app.register_task(NamedEntityRecognition())
