import uuid
from datetime import datetime
from typing import Dict, List, Optional

import celery
import pydantic
import ujson
from celery import chain
from celery.utils.log import get_task_logger

from nlp_pipeline.celery_app import app
from nlp_pipeline.constants import PipelineOutputs
from nlp_pipeline.schema.directory_reader_bol_product_embedding import (
    DRBOLProductEmbeddingArticle,
    DRBOLProductEmbeddingBatch,
)
from nlp_pipeline.schema.directory_reader_bol_product_embedding.input_0_0_0 import (
    BOLProductEmbeddingInput as Inputv0Schema,
)
from nlp_pipeline.schema.directory_reader_bol_product_embedding.input_1_0_0 import (
    BOLProductExtractedArticle as Inputv1Schema,
)
from nlp_pipeline.settings import BOL_PRODUCT_EMBEDDING_PRODUCT_BLACKLIST, environment
from nlp_pipeline.tasks import BolProductEmbedding, BolProductPublish, Publish
from nlp_pipeline.tasks.directory_reader_bol_product_extraction import (
    BatchTracker,
    DirectoryReaderBolProductExtraction,
)
from nlp_pipeline.utils.products import Products

logger = get_task_logger(__name__)


class DirectoryReaderBolProductEmbedding(DirectoryReaderBolProductExtraction):
    name = "Directory Reader Bol Product Embedding"
    extension = ".jsonl"
    pipeline_name = "bol_product_embedding"
    source_type = "bol_evidence"
    compression_type = "gz"

    def process_products(self, extracted_products: List[str], blacklisted_products: List[str]) -> List[str]:
        """
        Process products by applying task specific filtering and then non-task specific cleaning and filtering.

        Args:
            extracted_products (List[str]): list of extracted products.
            blacklisted_products (List[str]): list of products to blacklist.

        Returns:
            List(str): filtered list of products.
        """
        if not extracted_products:
            return extracted_products

        # apply non-task specific product processing rules
        extracted_products = Products.process(extracted_products)

        if blacklisted_products:
            blacklisted_products = [product.strip().upper() for product in blacklisted_products]

            extracted_products = [product for product in extracted_products if product not in blacklisted_products]

        return extracted_products

    def chain_tasks(self, input) -> celery.Celery.AsyncResult:
        """
        Chain all tasks

        Args:
            input (_type_): input to bol-product-embedding task

        Returns:
            celery.Celery.AsyncResult: Celery promise.
        """
        outputs_config = getattr(PipelineOutputs, self.pipeline_name).value.get_config_from_environment()
        promise = chain(
            BolProductEmbedding().s(input).set(queue=environment("BOL_PRODUCT_EMBEDDING_QUEUE_NAME")),
            BolProductPublish().s().set(queue=environment("BOL_PRODUCT_PUBLISH_QUEUE_NAME")),
            Publish().s(**outputs_config).set(queue=environment("PUBLISH_QUEUE_NAME")),
        ).apply_async()
        return promise

    def _process_article_v0(self, article: Inputv0Schema) -> Dict:
        article = article.model_dump(by_alias=True)

        article["metadata"] = {
            "prompts": article.pop("prompts"),
            "input_texts": article.pop("input_texts"),
            "llm_extracted_products": article.pop("llm_extracted_products"),
            "llm_model": article.pop("llm_model"),
        }
        return article

    def _process_article_v1(self, proto_article: Inputv1Schema) -> Dict:
        article = proto_article.model_dump(by_alias=True)

        metadata = {
            "prompts": {
                "cleaning_prompt": article["processes"][-1]["prompts"]["text_cleaning_prompt"],
                "product_extraction_prompt": article["processes"][-1]["prompts"]["product_extraction_prompt"],
            },
            "input_texts": {
                "cleaning_input_text": article["processes"][-1]["intermediary_texts"]["text_cleaning"],
                "product_extraction_text": article["processes"][-1]["intermediary_texts"]["product_extraction"],
            },
            "llm_extracted_products": article["llm_extracted_products"],
            "llm_model": article["processes"][-1]["llm_model"],
        }
        article["metadata"] = metadata

        del article["processes"]
        return article

    def process_article(self, proto_article: Dict, batch_info: BatchTracker) -> Optional[Dict]:
        """
        Process article into an BOLProductArticle.

        Args:
            proto_article (Dict): Should be a valid input schema e.g. input_v1_schema / input_v0_schema
            batch_info (BatchTracker): Info about the current batch

        Returns:
            Optional[Dict]: The resulting article, BOLProductEmbeddingArticle compatible
        """
        try:
            # try to process as v1
            proto_article = Inputv1Schema(**proto_article)
            article = self._process_article_v1(proto_article)
        except pydantic.ValidationError:
            try:
                # try to process as v0
                proto_article = Inputv0Schema(**proto_article)
                article = self._process_article_v0(proto_article)
            except pydantic.ValidationError:
                line = ujson.dumps(proto_article)

                msg = "Problem processing article. Unknown schema? "
                msg += f"file '{batch_info.current_file_path}', line {batch_info.current_line_idx}.\n"
                msg += f"line: {line}"
                logger.error(msg)
                return
            except Exception as e:
                line = ujson.dumps(proto_article)

                msg = "Problem processing a v0 article. "
                msg += f"file '{batch_info.current_file_path}', line {batch_info.current_line_idx}.\n"
                msg += f"line: {line}\n"
                msg += f"{e}"
                logger.error(msg)
                return
        except Exception as e:
            line = ujson.dumps(proto_article)

            msg = "Problem processing a v1 article. "
            msg += f"file '{batch_info.current_file_path}', line {batch_info.current_line_idx}.\n"
            msg += f"line: {line}\n"
            msg += f"{e}"
            logger.error(msg)
            return

        products = article["metadata"].get("llm_extracted_products", list())
        products = self.process_products(products, BOL_PRODUCT_EMBEDDING_PRODUCT_BLACKLIST)
        if not products:
            # No products to process
            return
        else:
            article["metadata"]["llm_extracted_products"] = products

        article["id"] = str(uuid.uuid4())
        article["processing_date"] = datetime.now().isoformat()

        if "source_type" not in article.keys():
            article["source_type"] = self.source_type

        try:
            DRBOLProductEmbeddingArticle.model_validate(article)
        except pydantic.ValidationError as e:
            repr_proto = ujson.dumps(article, indent=3)

            msg = "Problem turning BoL Product Description into a BolProduct article. "
            msg += f"file '{batch_info.current_file_path}', line {batch_info.current_line_idx}.\n"
            msg += f"Object: {repr_proto}\n"
            msg += f"{e}"
            logger.exception(msg)
            return
        return article

    def send_batch(self, batch_info: BatchTracker) -> celery.Celery.AsyncResult:
        """
        Send batch of articles to chain for processing.

        Args:
            batch_info (BatchTracker): Info about the batch

        Returns:
            celery.Celery.AsyncResult: Celery promise.
        """
        msg = f"Batch {batch_info.id}: {len(batch_info.batch)} articles, "
        msg += f"num files skipped {batch_info.num_files_skipped}"
        if batch_info.by_line:
            msg += f", num lines skipped {batch_info.num_lines_skipped}."
        else:
            msg += "."
        logger.info(msg)

        if not batch_info.batch:
            logger.info("No articles to send.")
            return

        batch_id = str(uuid.uuid4())
        created_on = datetime.now().strftime("%Y-%m-%d")

        batch_articles = DRBOLProductEmbeddingBatch(
            batch_id=batch_id,
            version=self.version,
            created_on=created_on,
            source_file=batch_info.original_file_path,
            source_type=self.source_type,
            source=self.name,
            articles=batch_info.batch,
        ).model_dump()

        promise = self.chain_tasks(batch_articles)
        return promise


app.register_task(DirectoryReaderBolProductEmbedding())
