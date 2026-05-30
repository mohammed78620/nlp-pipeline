from typing import List

from nlp_pipeline.celery_app import app
from nlp_pipeline.schema import vertexai as model
from nlp_pipeline.schema.product_extraction import PEedArticleBatch
from nlp_pipeline.schema.segmentation import SegmentedArticleBatch
from nlp_pipeline.schema.vertexai.response.product_extraction import Product
from nlp_pipeline.settings import PE_BATCH_SIZE, environment
from nlp_pipeline.tasks.vertexai_endpoint import VertexAIEndpoint
from nlp_pipeline.utils.vertexai import Endpoint


class ProductExtraction(VertexAIEndpoint):
    def __init__(self, **kwargs):
        settings = {
            "name": "Product Extraction",
            "queue": environment("PRODUCT_EXTRACTION_QUEUE_NAME"),
            "endpoint": Endpoint.product_extraction,
            "endpoint_batch_size": PE_BATCH_SIZE,
            "validation": {
                "payload": True,
                "response": True,
                "batch_input": True,
                "batch_output": True,
                "nuke_if_no_payload": False,
            },
            "models": {
                "task_input": SegmentedArticleBatch,
                "task_output": PEedArticleBatch,
                "endpoint_payload": model.PEPayload,
                "endpoint_response": model.PEResponse,
            },
        }
        super().__init__(settings, **kwargs)

    def payloads_generator(self, article_batch: SegmentedArticleBatch) -> List[model.PEPayload]:
        payloads = []
        payload = {"texts": []}

        for article in article_batch["articles"]:
            sentences = article["sentences"]
            for sentence in sentences:
                payload["texts"].append(sentence)

                if len(payload["texts"]) == self.get_subbatch_size():
                    payloads.append(payload)
                    payload = {"texts": []}

        if len(payload["texts"]) > 0:
            payloads.append(payload)
            payload = {"texts": []}

        return payloads

    def process_response(self, article_batch: SegmentedArticleBatch, response: model.PEResponse) -> PEedArticleBatch:
        predictions = response["predictions"]

        for article in article_batch["articles"]:
            for sentence in article["sentences"]:
                sentence_id = sentence["id"]

                if sentence_id in predictions.keys():
                    sentence["products"]: List[Product] = predictions[sentence_id]
                else:
                    sentence["products"]: List = []

        return article_batch


app.register_task(ProductExtraction())
