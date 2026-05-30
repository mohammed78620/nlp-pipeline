import os
from typing import List

from celery.utils.log import get_task_logger

from nlp_pipeline.celery_app import app
from nlp_pipeline.schema.directory_reader import RawArticle
from nlp_pipeline.settings import LSH_SEED, MIN_JACCARD_DR
from nlp_pipeline.tasks.directory_reader import DirectoryReader
from nlp_pipeline.utils.common import remove_files
from nlp_pipeline.utils.fingerprint import LSHFingerprintStore
from nlp_pipeline.utils.process_input_function import process_crawled_html

logger = get_task_logger(__name__)


class DirectoryReaderCompanyMentions(DirectoryReader):
    name = "Directory Reader Company Websites Relations"
    extension = ".html"
    pipeline_name = "company_mentions"

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


app.register_task(DirectoryReaderCompanyMentions())
