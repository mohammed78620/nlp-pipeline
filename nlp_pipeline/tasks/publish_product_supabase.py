import datetime
from typing import Dict, List

from celery.exceptions import Ignore
from celery.utils.log import get_task_logger
from supabase.client import Client, create_client

from nlp_pipeline.celery_app import app
from nlp_pipeline.constants import SUPABASE
from nlp_pipeline.settings import SUPABASE_SERVICE_KEY, ENV

logger = get_task_logger(__name__)


class SupabasePublisher:
    def __init__(self, url: str, service_key: str, table_name: str) -> None:
        supabase: Client = create_client(url, service_key)
        self.table_hdlr = supabase.table(table_name)

    def get_vid(self, article: Dict) -> str:
        """
        get vid from metadata within a article

        Args:
            article (Dict): the article dict

        Returns:
            str: return the identifier for the company
        """
        return article["metadata"]["extra_header_info"]["vid"]

    def format_data(self, article: Dict) -> List[Dict]:
        """
        Formats the provided article data into a list of dictionaries with the required fields.

        Args:
            article (Dict): A dictionary containing the article data.

        Returns:
            List[Dict]: A list of dictionaries, each representing a formatted data item.

        """
        vid: str = self.get_vid(article)
        now = datetime.datetime.now().isoformat()

        # handle source being in different places for bol-like evidence and homepage evidence.
        source = article["metadata"]["url"]
        if (
            article["source_type"] in ["bol_evidence", "ik_us_evidence", "ik_global_evidence"]
            or not article["metadata"]["url"]
        ):
            source = article.get("source", None)

        product_embeddings = article["products_embeddings"].items()
        data = []
        for product, embedding in product_embeddings:
            item = {
                "vid": vid,
                "product": product,
                "emb_model": article["metadata"]["product_embedding"]["model_name"],
                "product_source_type": article["source_type"],
                "product_source": source,
                "modified_on": now,
                "emb": embedding["embedding"],
                "prompt": article["metadata"]["product_extraction"]["prompt_template"],
                "source_text": article["text"],
            }

            data.append(item)
        return data

    def publish(self, data) -> None:
        try:
            self.table_hdlr.upsert(data).execute()
        except Exception as e:
            logger.exception("issue with data or connection to supabase")
            raise e


class PublishProduct(app.Task):
    name = "Publish Product"
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 5}
    retry_backoff = True

    def __init__(self, **kwargs) -> None:
        outputs_config = getattr(SUPABASE, ENV.name).value
        pe_supabase_table_name = outputs_config["pe_table_name"]
        supabase_url = outputs_config["url"]
        self.publisher = SupabasePublisher(supabase_url, SUPABASE_SERVICE_KEY, pe_supabase_table_name)

        super().__init__(**kwargs)

    def run(self, batch, validate: bool = None):
        if not batch:
            msg = "Nothing to process in incoming batch. Dropping task message."
            logger.debug(msg)
            raise Ignore(msg)
        elif not isinstance(batch, dict) or "articles" not in batch.keys():
            msg = "Invalid input: Input batch is of incorrect type. Dropping it."
            logger.error(msg)
            raise Ignore(msg)

        for article in batch["articles"]:
            data = self.publisher.format_data(article)
            try:
                self.publisher.publish(data)
            except Exception as e:
                logger.info(self._exec_options)
                try:
                    app.control.cancel_consumer(self.queue)
                except Exception:
                    logger.exception("Problem while canceling celery consumer")
                    raise e

        return batch


# app.register_task(PublishProduct)
