import datetime
from typing import ContextManager, Dict, List

from celery.exceptions import Ignore
from celery.utils.log import get_task_logger
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import DatabaseError
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.session import Session

from nlp_pipeline.celery_app import app
from nlp_pipeline.db import session_scope
from nlp_pipeline.exceptions.postgres import DeadlockError
from nlp_pipeline.models.node_product import NodeProduct
from nlp_pipeline.utils.openai import retry_with_exponential_backoff

logger = get_task_logger(__name__)


class GcpTablePublisher:
    def __init__(self, session_scope: ContextManager, model: NodeProduct) -> None:
        self.session_scope = session_scope
        self.model = model
        self.primary_keys = self._get_primary_keys()

    def _get_primary_keys(self) -> List:
        """
        get primary keys from sqlalchemy model

        Returns:
            List: return a list of primary keys
        """
        return [key.name for key in inspect(self.model).primary_key]

    def _get_existing_product(self, session: Session, vid: str, product: str, product_source: str):
        """
        Retrieves an existing product from the database if it exists.

        Args:
            vid (str): The VID (Vendor ID) of the product.
            product (str): The product keyword.
            product_source (str): The source URL of the product.

        Returns:
            NodeProduct or None: An existing NodeProduct instance or None if not found.
        """

        existing_product = None
        existing_product = (
            session.query(self.model)
            .filter(
                self.model.vid == vid,
                self.model.product == product,
                self.model.product_source == product_source,
            )
            .first()
        )
        return existing_product

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
                "created_on": now,
                "emb": embedding["embedding"],
                "prompt": article["metadata"]["product_extraction"]["prompt_template"],
                "source_text": article["text"],
            }

            data.append(item)
        return data

    @retry_with_exponential_backoff(
        initial_delay=5, exponential_base=1.2, jitter=False, max_retries=4, errors=(DeadlockError)
    )
    def publish(self, data) -> None:
        try:
            with self.session_scope() as session:
                for product in data:
                    stmt = insert(self.model).values(**product).on_conflict_do_nothing(index_elements=self.primary_keys)
                    session.execute(stmt)
        except DatabaseError as e:
            if "deadlock detected" in str(e.orig):
                logger.warning("deadlock detected retrying.")
                raise DeadlockError(e.statement, e.params, e.orig)
            raise e
        except Exception as e:
            logger.exception("issue with data or connection to database")
            raise e


class PublishProductToGcp(app.Task):
    name = "Publish Product to Gcp"
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 5}
    retry_backoff = True

    def __init__(self, **kwargs) -> None:
        self.publisher = GcpTablePublisher(session_scope, NodeProduct)

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
            logger.debug("formatting products")
            data = self.publisher.format_data(article)
            try:
                logger.debug("publishing products")
                self.publisher.publish(data)
            except Exception as e:
                logger.info(self._exec_options)
                try:
                    app.control.cancel_consumer(self.queue)
                except Exception:
                    logger.exception("Problem while canceling celery consumer")
                    raise e

        return batch


app.register_task(PublishProductToGcp())
