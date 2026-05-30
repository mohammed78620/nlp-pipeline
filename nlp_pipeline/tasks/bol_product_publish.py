from typing import Dict, List

import pydantic
from celery.exceptions import Ignore
from celery.utils.log import get_task_logger
from sqlalchemy.orm.session import Session

from nlp_pipeline.celery_app import app
from nlp_pipeline.db import session_scope
from nlp_pipeline.models.node_product import NodeProductV2
from nlp_pipeline.schema.bol_product_embedding import BOLProductEmbeddingArticle
from nlp_pipeline.schema.directory_reader_bol_product_embedding import DRBOLProductEmbeddingBatch
from nlp_pipeline.settings import BOL_PRODUCT_PUBLISH_ERROR_QUEUE_NAME, environment
from nlp_pipeline.tasks.publish_product_to_gcp import GcpTablePublisher
from nlp_pipeline.utils.common import publish_to_queue

logger = get_task_logger(__name__)


class BolProductGcpTablePublisher(GcpTablePublisher):
    def _get_existing_product(self, session: Session, vid: str, product: str):
        """
        Retrieves an existing product from the database if it exists.

        Args:
            vid (str): The VID (Vendor ID) of the product.
            product (str): The product keyword.

        Returns:
            NodeProduct or None: An existing NodeProduct instance or None if not found.
        """

        existing_product = None
        existing_product = (
            session.query(self.model)
            .filter(
                self.model.vid == vid,
                self.model.product == product,
            )
            .first()
        )
        return existing_product

    def get_vid(self, article: Dict) -> str:
        return article["supplier_vid"]

    def format_data(self, article: Dict) -> List[Dict]:
        """
        Formats the provided article data into a list of dictionaries with the required fields.

        Args:
            article (Dict): A dictionary containing the article data.

        Returns:
            List[Dict]: A list of dictionaries, each representing a formatted data item.

        """
        vid: str = self.get_vid(article)

        product_embeddings = article["products_embeddings"].items()
        data = []
        for product, embedding in product_embeddings:
            item = {
                "vid": vid,
                "product": product,
                "emb": embedding["embedding"],
            }

            data.append(item)
        return data


class BolProductPublish(app.Task):
    name = "Bol Publish Products"

    def __init__(self):
        self.publisher = BolProductGcpTablePublisher(session_scope=session_scope, model=NodeProductV2)
        self.error_queue = BOL_PRODUCT_PUBLISH_ERROR_QUEUE_NAME
        self.queue = environment("BOL_PRODUCT_PUBLISH_QUEUE_NAME")

    def process_article(self, article: Dict, dry_run: bool = False) -> Dict:
        """
        Publish an article embeddings and drop embedding data.

        Args:
            article (Dict): BOLProductEmbedding compatible article.
            dry_run (bool, Optional): Whether or not to actually execute on database. (Defaul: False)

        Returns:
            Dict: The resulting DRBOLProductEmbedding compatible article.
        """
        try:
            BOLProductEmbeddingArticle.model_validate(article)
        except pydantic.ValidationError as e:
            msg = f"Invalid article for {self.name}.process_article(). "
            msg += f"{e}"
            logger.error(msg)
            raise e

        logger.debug("formatting products")
        data = self.publisher.format_data(article)

        try:
            if not dry_run:
                logger.debug("publishing products")
                self.publisher.publish(data)
            else:
                logger.debug("Dry run. Skipped publishing bol product embeddings")
        except Exception as e:
            logger.info(self._exec_options)
            try:
                app.control.cancel_consumer(self.queue)
                if hasattr(self, "request"):
                    self.request.chain = None

                    if self.error_queue is not None:
                        publish_to_queue(app, self.request.args, self.error_queue)
                        message = f"Published failing batch to {self.error_queue}."
                        logger.error(message)

            except Exception:
                logger.exception("Problem while canceling celery consumer")
                raise e

        # drop data that's no longer needed
        article.pop("products_embeddings", None)
        article["metadata"].pop("product_embedding", None)

        return article

    def run(self, batch, validate: bool = None):
        # validate
        if not batch:
            msg = "Nothing to process in incoming batch. Dropping task message."
            logger.debug(msg)
            raise Ignore(msg)
        elif not isinstance(batch, dict) or "articles" not in batch.keys():
            msg = "Invalid input: Input batch is of incorrect type. Dropping it."
            logger.error(msg)
            raise Ignore(msg)

        for idx, article in enumerate(batch["articles"]):
            batch["articles"][idx] = self.process_article(article)

        # validate
        try:
            DRBOLProductEmbeddingBatch.model_validate(batch)
        except pydantic.ValidationError as e:
            msg = f"Invalid output batch for {self.name}. "
            msg += f"{e}"
            logger.error(msg)
            raise e

        return batch


app.register_task(BolProductPublish())
