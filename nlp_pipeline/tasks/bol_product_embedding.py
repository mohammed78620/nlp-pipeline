from typing import Dict, List, Tuple

import pydantic
from celery.exceptions import Ignore, MaxRetriesExceededError
from celery.utils.log import get_task_logger
from google.api_core.exceptions import GoogleAPIError, InvalidArgument, ServiceUnavailable

from nlp_pipeline.celery_app import app
from nlp_pipeline.schema.bol_product_embedding import BOLProductEmbeddingBatch
from nlp_pipeline.schema.directory_reader_bol_product_embedding import DRBOLProductEmbeddingArticle
from nlp_pipeline.settings import BOL_PRODUCT_EMBEDDING_ERROR_QUEUE_NAME, environment
from nlp_pipeline.tasks.product_embedding import ProductEmbedding
from nlp_pipeline.utils.common import publish_to_queue

logger = get_task_logger(__name__)


class BolProductEmbedding(ProductEmbedding):
    name = "Bol Product Embedding"
    task_countdown = 60

    def __init__(self, **kwargs) -> None:
        self.error_queue = BOL_PRODUCT_EMBEDDING_ERROR_QUEUE_NAME
        self.queue = environment("BOL_PRODUCT_EMBEDDING_QUEUE_NAME")
        super().__init__(**kwargs)

    def embed(self, items: List) -> Tuple[bool, Dict]:
        """
        Embeds a list of items using the text embedding model.

        Args:
            items (List): A list of items to be embedded.

        Returns:
            Tuple[bool, Dict]: A tuple containing a boolean value indicating the success of the embedding process
            and a dictionary mapping each item to its embedding and the model name.
        """
        try:
            embeddings = self.embedding_model.get_embeddings(items)
            success = True
            result = {}
            for i, item in enumerate(items):
                result[item] = {"embedding": embeddings[i].values}

        except ServiceUnavailable as e:
            exception_name = type(e).__name__
            logger.error(f"Failed with exception: {exception_name}.")

            success = False
            result = e

        except InvalidArgument as e:
            exception_name = type(e).__name__
            logger.error(f"Failed with exception: {exception_name}.")

            success = False
            result = e

        except GoogleAPIError as e:
            exception_name = type(e).__name__
            logger.error(f"Failed with exception: {exception_name}.")

            success = False
            result = e
        except Exception as e:
            exception_name = type(e).__name__
            logger.error(f"Failed with exception: {exception_name}. The products was: {items}")
            raise e

        return success, result

    def process_article(self, article: Dict) -> Dict:
        """
        Generate embeddings for article along with relevant metadata.

        Args:
            article (Dict): DRBOLProductEmbeddingArticle compatible dict.

        Returns:
            Dict: The resulting BOLProductEmbedding compatible dict.
        """
        try:
            DRBOLProductEmbeddingArticle.model_validate(article)
        except pydantic.ValidationError as e:
            msg = f"Invalid article for {self.name}.process_article(). "
            msg += f"{e}"
            logger.error(msg)
            raise e

        article["metadata"]["product_embedding"] = {"model_name": self.model_name}
        article["products_embeddings"] = {}

        for products in self.products_batch(
            article["metadata"]["llm_extracted_products"], self.text_embedding_model_batch_size
        ):
            try:
                success, embeddings = self.embed(products)
            except Exception as e:
                logger.info(self._exec_options)
                try:
                    app.control.cancel_consumer(self.queue)
                except Exception:
                    logger.exception("Problem while cancelling celery consumer")
                raise e

            if success:
                product_embeddings = article["products_embeddings"]
                article["products_embeddings"] = product_embeddings | embeddings

            else:
                try:
                    self.retry(countdown=self.task_countdown)
                except MaxRetriesExceededError as e:
                    message = f"Max retries reached querying Embeddings model {self.model_name} ."
                    if hasattr(self, "request"):
                        self.request.chain = None

                        if self.error_queue is not None:
                            publish_to_queue(app, self.request.args, self.error_queue)
                            message += f" Published failing batch to {self.error_queue}."

                    logger.error(message)
                    raise e
        return article

    def run(self, batch, validate: bool = None):
        if not batch:
            msg = "Nothing to process in incoming batch. Dropping task message."
            logger.debug(msg)
            raise Ignore(msg)
        elif not isinstance(batch, dict):
            msg = "Invalid input: Input batch is of incorrect type. Dropping it."
            logger.error(msg)
            raise Ignore(msg)

        all_have_products = all("llm_extracted_products" in article["metadata"] for article in batch["articles"])
        if not all_have_products:
            msg = "Invalid input: One or more articles missing products field. Dropping it."
            logger.debug(msg)
            raise Ignore(msg)

        for idx, article in enumerate(batch["articles"]):
            batch["articles"][idx] = self.process_article(article)

        if validate:
            batch = BOLProductEmbeddingBatch(**batch).model_dump(by_alias=True)

        return batch


# app.register_task(BolProductEmbedding())
