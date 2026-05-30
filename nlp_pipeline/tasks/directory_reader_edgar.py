import os
import uuid
from typing import List, Optional

import celery
from celery import chain
from celery.utils.log import get_task_logger

from nlp_pipeline.celery_app import app
from nlp_pipeline.constants import PipelineOutputs
from nlp_pipeline.schema.directory_reader import RawArticle
from nlp_pipeline.schema.input.edgar import SecFiling
from nlp_pipeline.settings import LSH_SEED, MIN_JACCARD_DR, environment
from nlp_pipeline.tasks import (
    AcronymResolver,
    BasicCoreference,
    NamedEntityLinking,
    NamedEntityRecognition,
    Publish,
    RelationExtraction,
    Segmentation,
)
from nlp_pipeline.tasks.directory_reader import DirectoryReader
from nlp_pipeline.utils.fingerprint import LSHFingerprintStore, fingerprint, hashchars
from nlp_pipeline.utils.htmlutils import clean_html, html_to_text

logger = get_task_logger(__name__)


class DirectoryReaderEdgar(DirectoryReader):
    name = "Directory Reader Edgar Relations"
    source_type = "edgar"
    extension = ".jsonl"
    pipeline_name = "edgar"

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
            BasicCoreference().s(input).set(queue=environment("BASIC_COREFERENCE_QUEUE_NAME")),
            AcronymResolver().s().set(queue=environment("ACRONYM_RESOLVER_QUEUE_NAME")),
            Segmentation().s().set(queue=environment("SEGMENTATION_QUEUE_NAME")),
            NamedEntityRecognition().s().set(queue=environment("NAMED_ENTITY_RECOGNITION_QUEUE_NAME")),
            RelationExtraction().s().set(queue=environment("RELATION_EXTRACTION_QUEUE_NAME")),
            NamedEntityLinking().s().set(queue=environment("NAMED_ENTITY_LINKING_QUEUE_NAME")),
            Publish().s(**outputs_config).set(queue=environment("PUBLISH_QUEUE_NAME")),
        ).apply_async()
        return promise

    def process_article(
        self,
        edgar_article: SecFiling,
        file_name: str,
        compressed_name: str,
        fingerprintstore: Optional[LSHFingerprintStore] = None,
    ) -> Optional[RawArticle]:
        """
        Process an Edgar  SEC filing. Transforming it into pipeline format.

        Args:
            edgar_article (SecFiling): The Edgar filing
            file_name (str): The name of the file the report was in
            compressed_name (str): The name of the archive the file was in
            fingerprintstore Optional[LSHFingerprintStore]: If provided the article text will be fingerprinted.

        Returns:
            Optional[RawArticle]: The result
        """
        article_html = edgar_article.filing_text
        article_html = clean_html(article_html)
        if not article_html:
            # Invalid content
            return None

        article_text = html_to_text(article_html)
        if not article_text:
            # No content
            return None

        id = str(uuid.uuid4())
        fingerprint_config = None
        article_fingerprint = None

        if fingerprintstore:
            article_fingerprint = fingerprintstore.add_item(article_text)
            if not article_fingerprint:
                # Already processed something similar
                return None

            id = fingerprint(article_fingerprint, hashchars)
            fingerprint_config = fingerprintstore.get_config()

        article = {
            "id": id,
            "source_type": self.source_type,
            "html": article_html,
            "text": article_text,
            "original_compressed_filename": compressed_name,
            "metadata": {
                "extra_edgar_info": {
                    "version": edgar_article.version,
                    "worker_query": edgar_article.worker_query.model_dump(by_alias=True),
                    "query_result": edgar_article.query_result.model_dump(by_alias=True),
                },
                "extra_header_info": {"vid": edgar_article.worker_query.vid},
                "fingerprint": article_fingerprint,
                "fingerprint_config": fingerprint_config,
                "original_file": file_name,
            },
            "pre_segmented_text": [],
        }

        article = RawArticle(**article)
        return article

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
            input_dir_path (str): input directory to articles i.e. local path
            batch_size (int): number of articles to be sent to next task
            extension (str): file type of articles
            compressed_name (str): name of gcs object
            original_file_path (str): path of where the articles originally came from e.g. bucket key

        Returns:
            int: number of batches processed
        """
        logger.info(f"batch_size= {batch_size}")

        fingerprintstore = LSHFingerprintStore(seed=LSH_SEED, min_jaccard=MIN_JACCARD_DR)

        file_paths: List[str] = []
        batch: List[RawArticle] = []
        num_batches = 0  # number of batches sent through pipeline
        num_skipped = 0  # number of skipped articles per batch

        for subdir, _, files in os.walk(input_dir_path):
            files.sort()
            for file_name in files:
                if extension and not file_name.endswith(extension):
                    num_skipped += 1
                    continue

                file_path = os.path.join(subdir, file_name)
                with open(file_path, "r", encoding="utf-8") as file:
                    for idx, line in enumerate(file):
                        line = line.strip()
                        if not line:
                            continue

                        try:
                            edgar_article = SecFiling.parse_raw(line)
                        except Exception:
                            logger.error(f"Problem loading Edgar Report. Line {idx} in file: {file_path}")
                            num_skipped += 1
                            continue

                        article = self.process_article(edgar_article, file_name, compressed_name, fingerprintstore)
                        if not article:
                            num_skipped += 1
                            logger.debug("Skipping article")
                            continue

                        batch.append(article)

                        if file_path not in file_paths:
                            file_paths.append(file_path)

                        if len(batch) >= batch_size:
                            self.send_batch(batch, file_paths, num_skipped, original_file_path)
                            batch = []
                            file_paths = []
                            num_batches += 1
                            num_skipped = 0
        if batch:
            self.send_batch(batch, file_paths, num_skipped, original_file_path)
            num_batches += 1

        return num_batches


app.register_task(DirectoryReaderEdgar())
