"""
Task: Basic Coreference Resolution

This Celery task performs coreference resolution on a batch of articles.
It uses the Versed Basic Coreference library to resolve coreferences within each article's text,
focusing on company names extracted from metadata. The resolved text is updated in the articles' content.
"""

from celery.utils.log import get_task_logger

from nlp_pipeline.celery_app import app
from nlp_pipeline.schema.directory_reader import RawArticleBatch

logger = get_task_logger(__name__)


class BasicCoreference(app.Task):
    name = "Basic Coreference"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def get_company_name(self, article):
        company_name = article["metadata"]["extra_edgar_info"]["query_result"]["companyName"]
        return company_name

    def run(self, input: RawArticleBatch) -> RawArticleBatch:
        articles = []
        for article in input["articles"]:
            # TODO: replace basic coreference
            company_name = "company A"
            article["text"] = f"{company_name}"
            articles.append(article)

        input["articles"] = articles
        logger.info(f"{self.name} batch: {input['batch_id']} done.")
        return input


app.register_task(BasicCoreference())
