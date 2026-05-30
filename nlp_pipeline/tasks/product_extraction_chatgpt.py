from typing import Dict

from celery.exceptions import Ignore
from celery.utils.log import get_task_logger

from nlp_pipeline import settings
from nlp_pipeline.celery_app import app
from nlp_pipeline.schema.product_extraction_chatgpt import PEedArticleBatch
from nlp_pipeline.utils.openai import ProductExtraction
from nlp_pipeline.utils.products import Products

logger = get_task_logger(__name__)


class ProductExtractionChatGPT(app.Task):
    name = "Product Extraction ChatGPT"
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 5}
    retry_backoff = True
    product_extractor = ProductExtraction(
        api_key=settings.OPENAI_API_KEY,
        model=settings.PE_OPENAI_MODEL,
        prompt_template=settings.PE_OPENAI_PROMPT,
        timeout=settings.OPENAI_TIMEOUT,
        max_product_str_tokens=settings.PE_OPENAI_MAX_PRODUCT_STR_TOKENS,
        min_product_str_tokens=settings.PE_OPENAI_MIN_PRODUCT_STR_TOKENS,
        max_product_length=settings.PE_OPENAI_MAX_PRODUCT_LENGTH,
        bad_response_length=settings.PE_OPENAI_BAD_RESPONSE_LENGTH,
        min_num_products=settings.PE_OPENAI_MIN_NUM_PRODUCTS,
        retry_attempts=settings.PE_OPENAI_RETRY_ATTEMPTS,
    )

    def process(self, article: Dict) -> Dict:
        settings = self.product_extractor.get_settings()
        truncated_text = self.product_extractor.clean_product_str(article["text"])

        if not self.product_extractor.has_min_num_tokens(truncated_text):
            article["products"] = []
            return article

        products = self.product_extractor.products_for_company(truncated_text)

        # apply non-task specific product processing rules
        products = Products.process(products)

        if "metadata" not in article.keys():
            article["metadata"] = {}

        article["metadata"]["product_extraction"] = settings
        article["metadata"]["product_extraction"]["text"] = truncated_text
        article["products"] = products
        return article

    def run(self, batch, validate: bool = None):
        if not batch:
            msg = "Nothing to process in incoming batch. Dropping task message."
            logger.debug(msg)
            raise Ignore(msg)

        num_incoming = len(batch["articles"])

        articles = []
        for article in batch["articles"]:
            # drop if no text to process
            if not article["text"]:
                continue

            article = self.process(article)

            # drop if no products extracted
            if not article["products"]:
                continue

            articles.append(article)

        if not articles:
            msg = "No articles to pass on. Dropping task message."
            logger.info(msg)
            raise Ignore(msg)

        batch["articles"] = articles
        if validate:
            batch = PEedArticleBatch(**batch).model_dump(by_alias=True)

        num_outgoing = len(batch["articles"])
        logger.info(f"Number of articles dropped: {num_incoming-num_outgoing}")
        logger.info(f"Number of articles output: {num_outgoing}")
        return batch


app.register_task(ProductExtractionChatGPT())
