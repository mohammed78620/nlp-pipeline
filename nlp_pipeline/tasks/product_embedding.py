from typing import Dict, Generator, List, Tuple

from celery.exceptions import Ignore
from celery.utils.log import get_task_logger
from google.api_core.exceptions import GoogleAPIError, InvalidArgument, ServiceUnavailable
from vertexai.preview.language_models import TextEmbeddingModel

from nlp_pipeline.celery_app import app
from nlp_pipeline.schema.product_embedding import ProductEmbeddingArticleBatch
from nlp_pipeline.settings import PE_VERTEXAI_MODEL

logger = get_task_logger(__name__)


class ProductEmbedding(app.Task):
    name = "Product Embedding"
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 5}
    retry_backoff = True
    text_embedding_model_batch_size = 5

    def __init__(self, **kwargs) -> None:
        self.model_name = PE_VERTEXAI_MODEL

        self.embedding_model = TextEmbeddingModel.from_pretrained(self.model_name)

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
            logger.error(f"Failed with exception: {exception_name}. The products was: {items}")
            raise e

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

    def products_batch(self, products: List, batch_size=5) -> Generator:
        """
        Generates batches of products from a given list.

        Args:
            products (List): A list of products.
            batch_size (int, optional): The desired batch size. Defaults to 5.

        Yields:
            Generator: A generator that yields batches of products.
        """
        length = len(products)
        for i in range(0, length, batch_size):
            yield products[i : min(i + batch_size, length)]

    def run(self, batch, validate: bool = None) -> ProductEmbeddingArticleBatch:
        if not batch:
            msg = "Nothing to process in incoming batch. Dropping task message."
            logger.debug(msg)
            raise Ignore(msg)
        elif not isinstance(batch, dict):
            msg = "Invalid input: Input batch is of incorrect type. Dropping it."
            logger.error(msg)
            raise Ignore(msg)

        all_have_products = all("products" in article for article in batch["articles"])
        if not all_have_products:
            msg = "Invalid input: One or more articles missing products field. Dropping it."
            logger.debug(msg)
            raise Ignore(msg)

        for article in batch["articles"]:
            article["metadata"]["product_embedding"] = {"model_name": self.model_name}
            article["products_embeddings"] = {}
            for products in self.products_batch(article["products"], self.text_embedding_model_batch_size):
                try:
                    success, embeddings = self.embed(products)
                except Exception as e:
                    logger.info(self._exec_options)
                    try:
                        app.control.cancel_consumer(self.queue)
                    except Exception:
                        logger.exception("Problem while canceling celery consumer")
                    raise e

                if success:
                    product_embeddings = article["products_embeddings"]
                    article["products_embeddings"] = product_embeddings | embeddings

                else:
                    self.retry(exec, embeddings)

        if validate:
            batch = ProductEmbeddingArticleBatch(**batch).model_dump(by_alias=True)

        return batch


# app.register_task(ProductEmbedding())
