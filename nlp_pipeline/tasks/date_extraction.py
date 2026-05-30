from typing import Dict, List

from nlp_pipeline.celery_app import app
from nlp_pipeline.schema import vertexai as model
from nlp_pipeline.schema.date_extraction import DEedArticleBatch
from nlp_pipeline.schema.named_entity_linking import NELedArticleBatch
from nlp_pipeline.settings import DE_BATCH_SIZE, environment
from nlp_pipeline.tasks.vertexai_endpoint import VertexAIEndpoint
from nlp_pipeline.utils.vertexai import Endpoint


class DateExtraction(VertexAIEndpoint):
    def __init__(self, **kwargs) -> None:
        settings = {
            "name": "Date Extraction",
            "queue": environment("DATE_EXTRACTION_QUEUE_NAME"),
            "endpoint": Endpoint.date_extraction,
            "endpoint_batch_size": DE_BATCH_SIZE,
            "allow_endpoint_failure": True,
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
        payload = {"instances": []}
        return payload

    def payloads_generator(self, article_batch: NELedArticleBatch) -> List[model.DEPayload]:
        payloads = []
        payload = self.get_empty_payload()

        for idx, article in enumerate(article_batch["articles"]):
            meta_date = article["metadata"].get("meta_date", None)
            meta_year = article["metadata"].get("meta_year", None)
            if meta_date:
                # article has a good date, so not gonna be queried so apply meta date
                article_batch["articles"][idx]["metadata"].update({"date": meta_date, "year": meta_year})
                continue

            entry = {"id": article["id"], "text": article["text"]}
            payload["instances"].append(entry)

            if len(payload["instances"]) == self.get_subbatch_size():
                payloads.append(payload)
                payload = self.get_empty_payload()

        if len(payload["instances"]) > 0:
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
            response (model.DEResponse): The DE Vertex AI endpoint response

        Returns:
            DEedArticleBatch: Processed articles that have NER data.
        """
        for article_index, article in enumerate(article_batch["articles"]):
            meta_date = article["metadata"].get("meta_date", None)
            meta_year = article["metadata"].get("meta_year", None)
            if not meta_date:
                meta_date = None
                meta_year = None

            try:
                predictions = {}
                for prediction in response["predictions"]:
                    predictions.update(prediction)

                res = predictions[str(article["id"])]
            except KeyError:
                # article likely wasn't queried so use metadata we already had
                article_batch["articles"][article_index]["metadata"].update({"date": meta_date, "year": meta_year})
            else:
                if "score" in res:
                    # rename field in response
                    res["date_score"] = res.pop("score")

                if res["date"]:
                    article_batch["articles"][article_index]["metadata"].update(res)
                else:
                    # DE failed, use metadata from article
                    if meta_date:
                        article_batch["articles"][article_index]["metadata"].update(
                            {"date": meta_date, "year": meta_year}
                        )
                    else:
                        # if no useful article metadata use the response anyway
                        article_batch["articles"][article_index]["metadata"].update(res)

        return article_batch


app.register_task(DateExtraction())
