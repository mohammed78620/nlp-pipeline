import os
from typing import List

import celery
from celery import chain
from celery.utils.log import get_task_logger

from nlp_pipeline.celery_app import app
from nlp_pipeline.constants import PipelineOutputs
from nlp_pipeline.schema.directory_reader import RawArticle
from nlp_pipeline.settings import LSH_SEED, MIN_JACCARD_DR, environment
from nlp_pipeline.tasks import ProductEmbedding, ProductExtractionChatGPT, Publish, PublishProductToGcp
from nlp_pipeline.tasks.directory_reader import DirectoryReader
from nlp_pipeline.utils.common import remove_files
from nlp_pipeline.utils.fingerprint import LSHFingerprintStore
from nlp_pipeline.utils.process_input_function import process_crawled_html_meta

logger = get_task_logger(__name__)


class DirectoryReaderHomepage(DirectoryReader):
    name = "Directory Reader Company Websites Products"
    extension = ".html"
    pipeline_name = "product"

    def chain_tasks(self, input) -> celery.Celery.AsyncResult:
        """
        Chain all tasks

        Args:
            input (_type_): input to segmentation task

        Returns:
            celery.Celery.AsyncResult: Celery promise.
        """
        outputs_config = getattr(PipelineOutputs, self.pipeline_name).value.get_config_from_environment()
        promise = chain(
            ProductExtractionChatGPT().s(input).set(queue=environment("PRODUCT_EXTRACTION_CHATGPT_QUEUE_NAME")),
            ProductEmbedding().s().set(queue=environment("PRODUCT_EMBEDDING_QUEUE_NAME")),
            PublishProductToGcp().s().set(queue=environment("PUBLISH_PRODUCT_QUEUE_NAME")),
            Publish().s(**outputs_config).set(queue=environment("PUBLISH_QUEUE_NAME")),
        ).apply_async()
        return promise

    def read(
        self,
        input_dir_path: str,
        batch_size: int,
        extension: str,
        compressed_name: str,
        original_file_path: str,
        **kwargs,
    ) -> int:
        """
        read all files in directory and sub directories and start tasks for every batch processed

        Args:
            input_dir_path (str): input directory to articles
            batch_size (int): number of articles to be sent to next task
            extension (str): file type of articles
            compressed_name (str): name of gcs object
            original_file_path (str): path of where the articles originally came from e.g. bucket key

        Returns:
            int: number of batches processed
        """
        logger.info(f"input_dir_path: {input_dir_path}")
        logger.info(f"batch_size: {batch_size}")

        fingerprintstore = LSHFingerprintStore(seed=LSH_SEED, min_jaccard=MIN_JACCARD_DR)

        processed: List[RawArticle] = []
        no_batches = 0
        file_skipped = 0
        file_paths: List[str] = []

        for subdir, _, files in os.walk(input_dir_path):
            files.sort()
            for file_name in files:
                if extension is not None:
                    if not file_name.endswith(extension):
                        file_skipped += 1
                        continue

                file_path = os.path.join(subdir, file_name)
                raw_html = open(file_path, encoding="utf-8", errors="ignore").read().strip()
                article = process_crawled_html_meta(raw_html, fingerprintstore=fingerprintstore)

                if article is not None:
                    processed = self.append_article(
                        processed, article, file_name, file_path, file_paths, compressed_name
                    )
                else:
                    remove_files([file_path])
                    file_skipped += 1
                    continue

                if len(processed) >= batch_size:
                    self.send_batch(processed, file_paths, file_skipped, original_file_path)
                    processed: List[RawArticle] = []
                    no_batches += 1
                    file_skipped = 0
                    file_paths = []

        self.send_batch(processed, file_paths, file_skipped, original_file_path)
        no_batches += 1
        return no_batches


app.register_task(DirectoryReaderHomepage())
