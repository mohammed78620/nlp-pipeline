import tempfile
import uuid
from datetime import datetime
from typing import Any, Dict, List, Union

from celery.utils.log import get_task_logger
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

from nlp_pipeline.celery_app import app
from nlp_pipeline.schema.named_entity_linking import NELedArticleBatch
from nlp_pipeline.settings import GOOGLE_PROJECT_ID
from nlp_pipeline.utils.common import create_compressed_file

logger = get_task_logger(__name__)


class Publish(app.Task):
    name = "Publish"

    partition_by_day = True

    autoretry_for = (GoogleCloudError,)
    retry_kwargs = {"max_retries": 5}
    retry_backoff = True

    def determine_batch_id(self, articles: Any) -> str:
        """
        Try get a batch_id from that data, if can't find one, make one.

        Args:
            articles (Any): The data to check

        Returns:
            str: A batch_id, potentially tied to the data, but might not be.
        """
        batch_id = None

        # Check if traditional article batch
        if isinstance(articles, dict):
            batch_id = articles.get("batch_id")

        # Might be a batch of BOLProductExtractedArticle
        if not batch_id and isinstance(articles, list):
            try:
                batch_id = articles[-1]["processes"][-1]["batch_id"]
            except (IndexError, KeyError):
                # if it failed... well, clearly it's not. No worries, fallback.
                pass

        # Failsafe
        if not batch_id:
            batch_id = uuid.uuid4()
        return batch_id

    def run(self, articles: Union[List, Dict, NELedArticleBatch], bucket: str, path: str, region: str) -> str:
        """
        Task to compress and upload a batch to to a gcs bucket.

        If articles is a List, will be saved as compressed JSONL.
        If articles is a Dict saved as compressed JSON.

        Args:
            articles (Union[List, Dict, NELedArticleBatch]): Data to be published.
            bucket (str): GCS bucket to upload to.
            path (str): Path within bucket
            region (str): GCS Region. [UNUSED?]

        Returns:
            str: compressed file name
        """
        as_jsonl = False

        # dont upload any files if they have no articles
        if not articles:
            return articles
        elif isinstance(articles, list):
            # Non-empty lists output as JSONL
            as_jsonl = True

            if len(articles) == 0:
                logger.info("List has nothing to publish.")
                return articles
        elif isinstance(articles, dict) and len(articles["articles"]) == 0:
            # nothing for this task to process
            logger.info("No articles. Doing nothing.")
            return articles

        # Set up file names via unique identifier
        batch_id = self.determine_batch_id(articles)

        with tempfile.TemporaryDirectory() as tmp_dir:
            compressed_file_path, compressed_file_name = create_compressed_file(
                articles, batch_id, tmp_dir, as_jsonl=as_jsonl
            )
            destination = self.get_publish_path(compressed_file_name, path)

            # Save compressed file to gcs
            try:
                self.upload_to_gcs(bucket, compressed_file_path, destination)
                logger.info(f"Uploaded batch {batch_id} to {bucket}:{destination}")
            except GoogleCloudError as e:
                logger.error(e)
                raise GoogleCloudError

            return destination

    @staticmethod
    def format_date(date: datetime = None) -> str:
        if date is None:
            date = datetime.now()

        date = date.strftime("%Y%m%d")
        return date

    def get_publish_path(self, filename: str, path: str = "/", date: datetime = None) -> str:
        if path[-1] != "/":
            path += "/"

        if self.partition_by_day:
            date = self.format_date(date)
            path += date + "/"

        path += filename
        return path

    def upload_to_gcs(self, bucket_name, file_path, gcs_key=None):
        """
        Uploads a file to a GCS bucket using the given file path. If a GCS key is not specified, the key
        will be set to the file name of the given file path.

        Parameters:
        bucket_name (str): The name of the GCS bucket to upload the file to.
        file_path (str): The path to the file to upload.
        gcs_key (Optional[str]): The GCS key to use for the file in the bucket. If None, the file name of
            the given file path will be used.

        """
        storage_client = storage.Client(GOOGLE_PROJECT_ID)
        bucket = storage_client.get_bucket(bucket_name)

        if gcs_key is None:
            gcs_key = file_path.split("/")[-1]

        blob = bucket.blob(gcs_key)
        blob.upload_from_filename(file_path)


app.register_task(Publish())
