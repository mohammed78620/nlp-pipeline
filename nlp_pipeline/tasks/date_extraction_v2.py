from datetime import datetime
from typing import Dict, List

from nlp_pipeline.celery_app import app
from nlp_pipeline.schema import vertexai as model
from nlp_pipeline.schema.date_extraction import DEedArticleBatch
from nlp_pipeline.schema.named_entity_linking import NELedArticleBatch
from nlp_pipeline.settings import DE_BATCH_SIZE
from nlp_pipeline.tasks.vertexai_endpoint import VertexAIEndpoint
from nlp_pipeline.utils.vertexai import Endpoint


class DateExtraction(VertexAIEndpoint):
    max_year = datetime.now().year
    min_year = max_year - 20

    def __init__(self, **kwargs) -> None:
        settings = {
            "name": "Date Extraction",
            "endpoint": Endpoint.date_extraction,
            "endpoint_batch_size": DE_BATCH_SIZE,
            "validation": {
                "payload": True,
                "response": True,
                "batch_input": True,
                "batch_output": True,
                "nuke_if_no_payload": False,
            },
            "models": {
                "task_input": NELedArticleBatch,
                "task_output": DEedArticleBatch,
                "endpoint_payload": model.DEPayload,
                "endpoint_response": model.DEResponse,
            },
        }
        super().__init__(settings, **kwargs)

    def get_empty_payload(self) -> Dict:
        payload = {"texts": [], "min_year": self.min_year, "max_year": self.max_year}
        return payload

    def payloads_generator(self, article_batch: NELedArticleBatch) -> List[model.DEPayload]:
        payloads = []
        payload = self.get_empty_payload()

        for article in article_batch["articles"]:
            entry = {"id": article["id"], "text": article["text"]}
            payload["texts"].append(entry)

            if len(payload["texts"]) == self.endpoint_batch_size:
                payloads.append(payload)
                payload = self.get_empty_payload()

        if len(payload["texts"]) > 0:
            payloads.append(payload)
            payload = self.get_empty_payload()

        return payloads

    def process_response(self, article_batch: NELedArticleBatch, response: model.DEResponse):
        """
        Appends SM predictions back to its article. If the prediction for an article
        is empty, attemt to use HTML meta_date and meta_year (if present), otherwise
        set date and year to None.

        Args:
            article_batch (NELedArticleBatch): The article batch being processed
            response (model.DEResponse): The DE Sagemaker endpoint response

        Returns:
            DEedArticleBatch: Processed articles that have NER data.
        """
        for article_index, article in enumerate(article_batch["articles"]):
            try:
                res = response["predictions"][str(article["id"])]

                if "score" in res:
                    res["date_score"] = res.pop("score")

                if res["date"] is None:
                    if article["metadata"].get("meta_date", None) and article["metadata"].get("meta_year", None):
                        article_batch["articles"][article_index]["metadata"].update(
                            {"date": article["meta_date"], "year": article["meta_year"]}
                        )
                    else:
                        article_batch["articles"][article_index]["metadata"].update(res)
                else:
                    article_batch["articles"][article_index]["metadata"].update(res)
            except KeyError:
                article_batch["articles"][article_index]["metadata"].update({"date": None, "year": None})

        return article_batch


app.register_task(DateExtraction())
