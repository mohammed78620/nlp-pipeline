import errno
import os
import tarfile
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from shutil import rmtree
from typing import List

import celery
from celery import chain
from celery.utils.log import get_task_logger
from google.cloud import storage

from nlp_pipeline.celery_app import app
from nlp_pipeline.constants import PipelineOutputs
from nlp_pipeline.schema.directory_reader import RawArticle, RawArticleBatch
from nlp_pipeline.settings import GOOGLE_PROJECT_ID, LSH_SEED, MIN_JACCARD_DR, VERSION, environment
from nlp_pipeline.tasks import (
    DateExtraction,
    NamedEntityLinking,
    NamedEntityRecognition,
    Publish,
    RelationExtraction,
    Segmentation,
)
from nlp_pipeline.utils.common import remove_files
from nlp_pipeline.utils.fingerprint import LSHFingerprintStore, fingerprint, hashchars
from nlp_pipeline.utils.process_input_function import process_crawled_html

logger = get_task_logger(__name__)


class DirectoryReader(app.Task):
    name = "Directory Reader News Relations"
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 5}
    retry_backoff = True
    version = VERSION
    source_type = "website"
    extension = ".html"
    pipeline_name = "crawled"
    compression_type = "bz2"

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
            Segmentation().s(input).set(queue=environment("SEGMENTATION_QUEUE_NAME")),
            NamedEntityRecognition().s().set(queue=environment("NAMED_ENTITY_RECOGNITION_QUEUE_NAME")),
            RelationExtraction().s().set(queue=environment("RELATION_EXTRACTION_QUEUE_NAME")),
            NamedEntityLinking().s().set(queue=environment("NAMED_ENTITY_LINKING_QUEUE_NAME")),
            DateExtraction().s().set(queue=environment("DATE_EXTRACTION_QUEUE_NAME")),
            Publish().s(**outputs_config).set(queue=environment("PUBLISH_QUEUE_NAME")),
        ).apply_async()
        return promise

    def download_gcs_object(self, bucket: str, blob_name: str, dir: str) -> str:
        """
        Download an object from a Google Cloud Storage (GCS) bucket.

        Args:
            bucket (str): The name of the GCS bucket.
            blob_name (str): The name of the object (blob).
            dir (str): The directory to file.

        Returns:
            str: The name of the downloaded file.
        """
        storage_client = storage.Client(GOOGLE_PROJECT_ID)
        bucket = storage_client.get_bucket(bucket)
        blob = bucket.blob(blob_name)
        name = blob_name.split("/")[-1]
        blob.download_to_filename(f"{dir}/{name}")
        return name

    def uncompress_file(self, inputfp: str, outdir: str, remove_after: bool = False, compression: str = "bz2") -> None:
        """
        uncompress file to a specified directory

        Args:
            inputfp (str): input file to be uncompressed
            outdir (str): directory location of uncompressed files
            remove_after (bool, optional): after uncompressing file remove if true. Defaults to False.
            compression (str, optional): compression type. Defaults to "bz2".
        """
        logger.info(f"Extracting {inputfp} into --> {outdir}")
        try:
            tar = tarfile.open(inputfp, "r:{}".format(compression))
        except tarfile.ReadError:
            try:
                logger.warning("Archive wasn't expected type. Winging it.")
                tar = tarfile.open(inputfp, "r:*")
            except tarfile.ReadError as e:
                logger.error("Couldn't figure out how to uncompress archive.")
                raise e

        tar.extractall(outdir)  # nosec
        tar.close()

        logger.info(f"creating output dir {outdir}")

        if remove_after:
            os.remove(inputfp)

    def send_batch(
        self, articles: List[RawArticle], file_paths: List[str], file_skipped: int, original_file_path: str
    ) -> celery.Celery.AsyncResult:
        """
        articles with set batch size, version and source is sent to chain of tasks and its file are removed

        Args:
            articles (List[RawArticle]): list of articles
            file_paths (List[str]): list of file paths
            file_skipped (int): number of files skipped
            original_file_path (str): path of where the articles originally came from e.g. bucket key

        Returns:
            celery.Celery.AsyncResult: Celery promise.
        """
        batch_id = str(uuid.uuid4())
        created_on = datetime.now().strftime("%Y-%m-%d")
        batch_articles = RawArticleBatch(
            batch_id=batch_id,
            version=self.version,
            created_on=created_on,
            source_file=original_file_path,
            source_type=self.source_type,
            source=self.name,
            articles=articles,
        ).model_dump(by_alias=True)

        logger.info(f"batching {len(batch_articles['articles'])}, skipped {file_skipped}")

        promise = self.chain_tasks(batch_articles)

        remove_files(file_paths)
        return promise

    def append_article(
        self,
        articles: List[RawArticle],
        article: dict,
        file_name: str,
        file_path: str,
        file_paths: List[str],
        name: str,
    ) -> List[RawArticle]:
        """
        append article to list of articles after creating id, setting file_path and validating against pydantic model

        Args:
            articles (list[RawArticle]):  list of articles
            article (_type_): dictionary returned after crawling html
            file_path (str): the file path to html
            file_paths (List[str]): list of file paths

        Returns:
            List[RawArticle]: list of articles
        """

        article["id"] = fingerprint(article["metadata"]["fingerprint"], hashchars)
        article["original_compressed_filename"] = name
        article["original_html_file"] = file_name
        article["source_type"] = self.source_type

        file_paths.append(file_path)
        article = RawArticle(**article)
        articles.append(article)

        return articles

    def get_name_from_path(self, path: str) -> str:
        """
        get name from path by removing 1 or more suffixes

        Args:
            path (str): file path

        Returns:
            str: return name of file
        """
        whitelist = {
            ".tar",
            ".bz2",
            ".tb2",
            ".tbz",
            ".tbz2",
            ".tz2",
            ".gz",
            ".taz",
            ".tgz",
            ".lz",
            ".lzma",
            ".tlz",
            ".lzo",
            ".xz",
            ".txz",
            ".z",
            ".tz",
            ".zst",
            ".pkg",
        }
        path = Path(path)
        while path.suffix.lower() in whitelist:
            path = path.with_suffix("")

        return path.name

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
                article = process_crawled_html(raw_html, fingerprintstore=fingerprintstore)

                if article is not None:
                    processed = self.append_article(
                        processed, article, file_name, file_path, file_paths, compressed_name
                    )

                else:
                    remove_files([file_path])
                    file_skipped += 1
                    logger.debug(f"Skipping: {file_name}")
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

    def run(self, *args, **kwargs):
        try:
            with tempfile.TemporaryDirectory(prefix=self.name) as tmp_dir:
                bucket, key, batch_size = args

                # check if extracted folder exists
                name = key.split("/")[-1]
                file_path = f"{tmp_dir}/{name}"
                folder_path = f"{tmp_dir}/{self.get_name_from_path(file_path)}"

                if os.path.isdir(folder_path):
                    logger.info("folder exists")
                    self.read(folder_path, batch_size, self.extension, name, original_file_path=key)
                    rmtree(folder_path)
                    return "folder processed"

                if not os.path.isfile(file_path):
                    logger.info("downloading gcs object")
                    name = self.download_gcs_object(bucket, key, tmp_dir)

                self.uncompress_file(file_path, folder_path, True, self.compression_type)

                # read files and process
                batches = self.read(folder_path, batch_size, self.extension, name, original_file_path=key)
                logger.info(f"number of batches processed: {batches}")

                rmtree(folder_path)
        except Exception as e:
            if hasattr(e, "errno") and e.errno == errno.ENOSPC:
                logger.error(f"No space left on disk shutting down worker: {e}")
                app.control.shutdown()
            else:
                logger.error(f"Something went wrong: {e}")
            raise e

        return "folder processed"


app.register_task(DirectoryReader())
