import os
from datetime import datetime
from typing import Dict, List

import ujson
from celery.utils.log import get_task_logger

from nlp_pipeline.celery_app import app
from nlp_pipeline.settings import EXCLUDE_LEXISNEXIS_TOPICS, LSH_SEED, MIN_JACCARD_DR
from nlp_pipeline.tasks.directory_reader import DirectoryReader
from nlp_pipeline.utils.fingerprint import LSHFingerprintStore

logger = get_task_logger(__name__)


class DirectoryReaderLexisNexis(DirectoryReader):
    name = "Directory Reader Lexis Nexis Relations"
    source_type = "LexisNexis"
    extension = ".json"
    pipeline_name = "ln"

    def extract_metadata(self, article: Dict, article_obj: Dict) -> Dict:
        """
        add metadata fields to article dict

        Args:
            article (Dict): dict containing fields in lexis nexis article
            metajson_obj (Dict): dict article fields and metadata

        Returns:
            Dict: returns a dict containing meta data and articles fields
        """
        metajson_obj = {}
        published_date = article.pop("publishedDate", None)
        url = article.pop("url", None)

        if published_date:
            date = datetime.fromisoformat(published_date[:-1])
            metajson_obj["meta_date"] = date.strftime("%Y-%m-%d")
            metajson_obj["meta_year"] = date.year
            metajson_obj["year"] = metajson_obj["meta_year"]
            metajson_obj["date"] = metajson_obj["meta_date"]

        if url:
            metajson_obj["url"] = url

        return {**article_obj, "metadata": {**metajson_obj, "extra_lexis_nexis_info": {**article}}}

    def has_excluded_topic(self, topics_groups: List[Dict], exclude_list: List[str]) -> bool:
        """
        go through a list of topics and check if any topics are in the exclude list

        Args:
            exclude_list (List[str]): list of topics to exclude
            topics_groups (List[Dict]): list of topics

        Returns:
            bool: return true if in the exclude list
        """

        if not topics_groups:
            return False

        topics = [t.get("group") for t in topics_groups]
        if any(topic in exclude_list for topic in topics):
            return True
        return False

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
                raw_json = open(f"{input_dir_path}/{file_name}", encoding="utf-8", errors="ignore").read().strip()
                articles = ujson.loads(raw_json).get("articles", None)
                no_batches = 0

                for article in articles:
                    text = article.pop("content", None)
                    language = article.get("language", None)
                    topics = article.get("topics", None)

                    if self.has_excluded_topic(topics, EXCLUDE_LEXISNEXIS_TOPICS):
                        skipped += 1
                        continue

                    if not text or language != "English":
                        skipped += 1
                        continue

                    if fingerprintstore is not None:
                        fingerprint = fingerprintstore.add_item(text)
                        if not fingerprint:
                            continue

                    article_obj = self.extract_metadata(article, article_obj)

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
                        self.send_batch(processed, file_paths, skipped, original_file_path)
                        processed = []
                        file_paths = []
                        no_batches += 1
                        skipped = 0

        # TODO: Check if this is suppose to be using an empty list for the file paths
        # rather than using file_paths var
        self.send_batch(processed, [], skipped, original_file_path)
        no_batches += 1
        return no_batches


app.register_task(DirectoryReaderLexisNexis())
