import errno
import os
import tempfile
from datetime import datetime
from shutil import rmtree
from typing import Dict, List

import celery
import ujson
from celery import chain
from celery.utils.log import get_task_logger

from nlp_pipeline.celery_app import app
from nlp_pipeline.constants import PipelineOutputs
from nlp_pipeline.settings import LSH_SEED, MIN_JACCARD_DR, environment
from nlp_pipeline.tasks import (
    DateExtraction,
    NamedEntityLinking,
    NamedEntityRecognition,
    Publish,
    RelationExtraction,
    Segmentation,
)
from nlp_pipeline.tasks.directory_reader_lexis_nexis import DirectoryReaderLexisNexis
from nlp_pipeline.utils.common import remove_files, remove_urls
from nlp_pipeline.utils.fingerprint import LSHFingerprintStore
from nlp_pipeline.utils.process_input_function import is_en

logger = get_task_logger(__name__)


class DirectoryReaderBigtableWebz(DirectoryReaderLexisNexis):
    name = "Directory Reader Bigtable Webz"
    source_type = "webz"
    extension = ".jsonl"
    pipeline_name = "bigtable_webz"
    compression_type = "gz"

    def chain_tasks(self, input) -> celery.Celery.AsyncResult:
        """
        Chain all tasks

        Args:
            input (_type_): input to segmentation task

        Returns:
            celery.Celery.AsyncResult: Celery promise.
        """
        outputs_config = getattr(PipelineOutputs, f"{self.pipeline_name}").value.get_config_from_environment()

        promise = chain(
            Segmentation().s(input).set(queue=environment("SEGMENTATION_QUEUE_NAME")),
            NamedEntityRecognition().s().set(queue=environment("NAMED_ENTITY_RECOGNITION_QUEUE_NAME")),
            RelationExtraction().s().set(queue=environment("RELATION_EXTRACTION_QUEUE_NAME")),
            NamedEntityLinking().s().set(queue=environment("NAMED_ENTITY_LINKING_QUEUE_NAME")),
            DateExtraction().s().set(queue=environment("DATE_EXTRACTION_QUEUE_NAME")),
            Publish().s(**outputs_config).set(queue=environment("PUBLISH_QUEUE_NAME")),
        ).apply_async()
        return promise

    def extract_metadata(self, article: Dict) -> Dict:
        """
        add metadata fields to article dict

        Args:
            article (Dict): dict containing fields in webz article

        Returns:
            Dict: returns a dict containing meta data and articles fields
        """
        metajson_obj = {}
        published_date = article.pop("published", None)
        url = article.pop("sourceUrl", None)

        if published_date:

            if isinstance(published_date, str):
                date = datetime.fromisoformat(published_date)
            elif isinstance(published_date, int):
                published_date_seconds = published_date / 1000
                date = datetime.fromtimestamp(published_date_seconds)

            metajson_obj["meta_date"] = date.strftime("%Y-%m-%d")
            metajson_obj["meta_year"] = date.year
            metajson_obj["year"] = metajson_obj["meta_year"]
            metajson_obj["date"] = metajson_obj["meta_date"]

        if url:
            metajson_obj["url"] = url

        return {"metadata": {**metajson_obj, **article}}

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

        fingerprintstore = LSHFingerprintStore(seed=LSH_SEED, min_jaccard=MIN_JACCARD_DR)

        article_obj = {}
        processed = []
        no_batches = 0
        file_paths: List[str] = []
        skipped = 0
        for subdir, _, files in os.walk(input_dir_path):
            for file_name in files:
                if extension is not None:
                    if not file_name.endswith(extension):
                        skipped += 1
                        continue
                file_path = os.path.join(subdir, file_name)
                with open(f"{input_dir_path}/{file_name}", encoding="utf-8", errors="ignore") as file:

                    for line in file:
                        article = ujson.loads(line)
                        no_batches = 0

                        text = article.pop("content", None)

                        if not text:
                            skipped += 1
                            logger.debug("skipping article because empty")
                            continue
                        elif not is_en(text):
                            logger.debug("skipping article due to not being English")
                            skipped += 1
                            continue
                        elif fingerprintstore is not None:
                            fingerprint = fingerprintstore.add_item(text)
                            if not fingerprint:
                                logger.debug("skipping article as matching article in fingerprint store")
                                skipped += 1
                                continue

                        text = remove_urls(text)
                        article_obj = self.extract_metadata(article)

                        if fingerprintstore and fingerprint and article:
                            article_obj["metadata"]["fingerprint"] = fingerprint
                            article_obj["metadata"]["fingerprint_config"] = fingerprintstore.get_config()

                        article_obj["text"] = text
                        article_obj["pre_segmented_text"] = text.split("\n\n")
                        processed = self.append_article(
                            processed, article_obj, file_name, file_path, file_paths, compressed_name
                        )

                        # send batch
                        if len(processed) >= batch_size:
                            self.send_batch(processed, [], skipped, original_file_path)
                            processed = []
                            file_paths = []
                            no_batches += 1
                            skipped = 0

                remove_files([file_path])

        # rather than using file_paths var
        self.send_batch(processed, file_paths, skipped, original_file_path)
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


app.register_task(DirectoryReaderBigtableWebz())
