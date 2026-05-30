"""
Task: Acronym Resolver

This Celery task resolves acronyms present in a batch of articles.
"""

from celery.utils.log import get_task_logger

from nlp_pipeline.celery_app import app
from nlp_pipeline.utils.acronym_resolver import AcronymResolver as Resolver

logger = get_task_logger(__name__)


class AcronymResolver(app.Task):
    name = "Acronym Resolver"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def run(self, input):
        acronym_resolver = Resolver()

        articles = []
        for article in input["articles"]:
            text = article["text"]

            acronym_dict = acronym_resolver.identify_acronyms(text)
            resolved_text = acronym_resolver.resolve_acronyms(text, acronym_dict)

            article["text"] = resolved_text
            articles.append(article)

        input["articles"] = articles
        logger.info(f"{self.name} batch: {input['batch_id']} done.")
        return input


app.register_task(AcronymResolver())
