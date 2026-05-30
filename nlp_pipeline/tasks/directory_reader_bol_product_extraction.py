import os
import uuid
from datetime import datetime
from functools import cached_property
from typing import Dict, List, Optional

import celery
import pydantic
import ujson
from celery.utils.log import get_task_logger
from pydantic import BaseModel, computed_field

from nlp_pipeline.celery_app import app
from nlp_pipeline.constants import PipelineOutputs
from nlp_pipeline.schema.directory_reader_bol_product_extraction import (
    BOLProductArticle,
    DRBOLProductExtractionProcess,
)
from nlp_pipeline.schema.directory_reader_bol_product_extraction.input_1_0_0 import BOLProductDescription
from nlp_pipeline.settings import (
    BOL_PE_EXTRACTION_BLOCK_TERMS,
    BOL_PE_EXTRACTION_PROMPT,
    BOL_PE_GCP_LOCATION,
    BOL_PE_HYPERPARAMETERS,
    BOL_PE_LLM_MODEL,
    BOL_PE_PRECLEANING_PROMPT,
    BOL_PE_PRECLEANING_STRIP_TERMS,
    GOOGLE_PROJECT_ID,
    environment,
)
from nlp_pipeline.tasks import BolProductExtraction, BolProductExtractionPrecleaning, Publish
from nlp_pipeline.tasks.directory_reader import DirectoryReader
from nlp_pipeline.utils.common import remove_files

logger = get_task_logger(__name__)


class BatchTracker(BaseModel):
    """
    Track information about a batch e.g. ID, articles, current source, etc.
    """

    batch: List = []  # Articles in batch
    current_dir_path: str = None  # Directory of current file being processed
    current_file_name: str = None  # Name of current file being processed
    current_line_idx: int = 0  # Line number of the line being processed (if by line processing)
    num_batches: int = 0  # Number of batches processed
    num_files_skipped: int = 0  # Number of files that had to be skipped in current batch
    num_lines_skipped: int = 0  # Number of lines that had to be skipped in current batch (if by line processing)
    by_line: bool = False  # Whether or not the batch is being processed line by line or by whole file
    compressed_name: str = None  # Name of the remote file object files came from.
    original_file_path: str = None  # Path name where compressed_name file came from e.g. bucket key

    @computed_field
    @cached_property
    def id(self) -> str:
        # ID of batch - Only generate on instantiation, use cache otherwise
        return str(uuid.uuid4())

    @computed_field
    @property
    def current_file_path(self) -> Optional[str]:
        if not self.current_dir_path or not self.current_file_name:
            return
        return os.path.join(self.current_dir_path, self.current_file_name)


class DirectoryReaderBolProductExtraction(DirectoryReader):
    name = "Directory Reader Bol Product Extraction"
    extension = ".jsonl"
    pipeline_name = "bol_product_extraction"
    source_type = "bol_evidence"
    compression_type = "gz"

    def chain_tasks(self, input) -> celery.Celery.AsyncResult:
        """
        Chain all tasks

        Args:
            input (_type_): input to bol-product-embedding task

        Returns:
            celery.Celery.AsyncResult: Celery promise.
        """
        gcp_project = GOOGLE_PROJECT_ID
        gcp_location = BOL_PE_GCP_LOCATION
        llm_model = BOL_PE_LLM_MODEL
        hyperparameters = BOL_PE_HYPERPARAMETERS

        cleaning_prompt = BOL_PE_PRECLEANING_PROMPT
        cleaning_strip_terms = BOL_PE_PRECLEANING_STRIP_TERMS

        extraction_prompt = BOL_PE_EXTRACTION_PROMPT
        extraction_block_terms = BOL_PE_EXTRACTION_BLOCK_TERMS

        precleaning_args = {
            "gcp_project": gcp_project,
            "gcp_location": gcp_location,
            "llm_model": llm_model,
            "base_prompt": cleaning_prompt,
            "hyperparams": hyperparameters,
            "strip_terms": cleaning_strip_terms,
        }
        extraction_args = {
            "gcp_project": gcp_project,
            "gcp_location": gcp_location,
            "llm_model": llm_model,
            "base_prompt": extraction_prompt,
            "hyperparams": hyperparameters,
            "block_terms": extraction_block_terms,
        }

        outputs_config = getattr(PipelineOutputs, self.pipeline_name).value.get_config_from_environment()

        precleaning_queue = environment("BOL_PRODUCT_EXTRACTION_PRECLEANING_QUEUE_NAME")
        extraction_queue = environment("BOL_PRODUCT_EXTRACTION_QUEUE_NAME")
        publish_queue = environment("PUBLISH_QUEUE_NAME")

        promise = celery.chain(
            BolProductExtractionPrecleaning(**precleaning_args).s(input).set(queue=precleaning_queue),
            BolProductExtraction(**extraction_args).s().set(queue=extraction_queue),
            Publish().s(**outputs_config).set(queue=publish_queue),
        ).apply_async()
        return promise

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

        articles = [article.model_dump(by_alias=True) for article in batch_info.batch]
        promise = self.chain_tasks(articles)
        return promise

    def process_article(self, proto_article: Dict, batch_info: BatchTracker) -> Optional[BOLProductArticle]:
        """
        Process article by creating metadata and validating against pydantic model

        Args:
            proto_article (Dict): The object to turn into an article. Should be BOLProductDescription valid
            batch_info (BatchTracker): Info about the batch the article will be in

        Returns:
            Optional[BOLProductArticle]: The resulting article
        """
        # Validate incoming data
        try:
            BOLProductDescription.model_validate(proto_article)
            article = proto_article
        except pydantic.ValidationError as e:
            repr_proto = ujson.dumps(proto_article, indent=3)

            msg = "Invalid BoL Product Description. "
            msg += f"file '{batch_info.current_file_path}', line {batch_info.current_line_idx}.\n"
            msg += f"Object: {repr_proto}\n"
            msg += f"{e}"
            logger.exception(msg)
            return

        # Create metadata
        created_on = datetime.now().isoformat()
        process = DRBOLProductExtractionProcess(name=self.pipeline_name, created_on=created_on, batch_id=batch_info.id)

        # Transform to article
        try:
            article = BOLProductArticle(processes=[process], **article)
        except pydantic.ValidationError as e:
            repr_proto = ujson.dumps(proto_article, indent=3)

            msg = "Problem turning BoL Product Description into an article. "
            msg += f"file '{batch_info.current_file_path}', line {batch_info.current_line_idx}.\n"
            msg += f"Object: {repr_proto}\n"
            msg += f"{e}"
            logger.exception(msg)
            return

        return article

    def check_batch(self, batch_info: BatchTracker, max_batch_size: int, flush: bool = False) -> BatchTracker:
        """
        Check if batch needs to be sent, if it does then send and update tracker.

        Args:
            batch_info (BatchTracker): The batch to be checked.
            max_batch_size (int): If batch bigger than this value then it is to be sent.
            flush (bool): If True batch is sent regardless of batch size.

        Returns:
            BatchTracker: Updated tracker.
        """
        if len(batch_info.batch) >= max_batch_size or (flush and len(batch_info.batch) != 0):
            self.send_batch(batch_info)

            # Generate new batch ID, reset batch and skip stats
            batch_info = batch_info.model_dump(by_alias=True)
            del batch_info["id"]
            del batch_info["batch"]
            batch_info["num_batches"] += 1
            batch_info = BatchTracker(**batch_info)
        return batch_info

    def _read_by_line(self, batch_info: BatchTracker, max_batch_size: int, is_jsonl: bool = False) -> BatchTracker:
        with open(batch_info.current_file_path) as file:
            for idx, line in enumerate(file):
                batch_info.current_line_idx = idx
                data = None

                if is_jsonl:
                    try:
                        data = ujson.loads(line)
                    except ujson.JSONDecodeError:
                        msg = "Invalid JSON line in file. "
                        msg += f"file '{batch_info.current_file_path}', line {idx}.\n"
                        msg += f"line: {line}\n"
                        logger.exception(msg)

                        batch_info.num_lines_skipped += 1
                        continue
                else:
                    # TODO: add other line by line handling
                    raise NotImplementedError("This particular line-by-line feature not implemented.")

                if not data:
                    batch_info.num_lines_skipped += 1
                    continue

                try:
                    article = self.process_article(data, batch_info)
                except Exception as e:
                    msg = "Problem processing article. "
                    msg += f"file '{batch_info.current_file_path}', line {idx}.\n"
                    msg += f"line: {line}\n"
                    msg += f"error: {e}"
                    logger.exception(msg)

                    batch_info.num_lines_skipped += 1
                    continue

                if not article:
                    batch_info.num_lines_skipped += 1
                    continue

                batch_info.batch.append(article)
                batch_info = self.check_batch(batch_info, max_batch_size)
        return batch_info

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
        msg = f"Starting read. input_dir_path: '{input_dir_path}', batch_size: {batch_size}."
        logger.info(msg)

        batch_info = BatchTracker()
        batch_info.compressed_name = compressed_name
        batch_info.original_file_path = original_file_path

        for sub_dir, _, files in os.walk(input_dir_path):
            files.sort()
            for file_name in files:
                if extension is not None:
                    if not file_name.endswith(extension):
                        batch_info.num_files_skipped += 1
                        continue

                batch_info.current_dir_path = sub_dir
                batch_info.current_file_name = file_name

                if "jsonl" in extension:
                    batch_info.by_line = True
                    batch_info = self._read_by_line(batch_info=batch_info, max_batch_size=batch_size, is_jsonl=True)
                else:
                    # TODO: Add whole file processing
                    raise NotImplementedError("Invalid file type for this pipeline")

                batch_info = self.check_batch(batch_info, batch_size)

            remove_files([file_name])
        batch_info = self.check_batch(batch_info, batch_size, flush=True)
        return batch_info.num_batches


app.register_task(DirectoryReaderBolProductExtraction())
