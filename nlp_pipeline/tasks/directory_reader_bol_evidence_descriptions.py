import os
from typing import List
from uuid import uuid4

import ujson
from celery.utils.log import get_task_logger

from nlp_pipeline.celery_app import app
from nlp_pipeline.schema.directory_reader import RawArticle
from nlp_pipeline.tasks.directory_reader_homepage import DirectoryReaderHomepage
from nlp_pipeline.utils.common import remove_files

logger = get_task_logger(__name__)


class DirectoryReaderBolEvidenceDescriptions(DirectoryReaderHomepage):
    name = "Directory Reader Bol Evidence Products"
    extension = ".jsonl"
    pipeline_name = "product"
    source_type = "bol_evidence"
    compression = "gz"

    def process_article(
        self,
        article: dict,
        file_name: str,
        name: str,
    ) -> RawArticle:
        """
        process article by creating id, setting file_path and validating against pydantic model

        Args:
            article (dict): dictionary returned after crawling html
            file_name (str): name of the file the article came from
            name (str): name of the archive the article came from

        Returns:
            RawArticle: The resulting article
        """

        vid = article.pop("supplier_vid")
        article["id"] = str(uuid4())
        article["pre_segmented_text"] = []
        article["original_compressed_filename"] = name
        article["original_html_file"] = file_name
        article["metadata"] = {"extra_header_info": {"vid": vid}}

        if "source_type" not in article.keys():
            article["source_type"] = self.source_type

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
        logger.info(f"input_dir_path: {input_dir_path}")
        logger.info(f"batch_size: {batch_size}")

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
                with open(file_path) as jsonl_file:
                    for line in jsonl_file:
                        article = ujson.loads(line)

                        if article is not None:
                            processed_article = self.process_article(article, file_name, compressed_name)
                            processed.append(processed_article)
                            file_paths.append(file_path)
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


app.register_task(DirectoryReaderBolEvidenceDescriptions())
