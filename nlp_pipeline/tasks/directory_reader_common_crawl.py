from celery.utils.log import get_task_logger

from nlp_pipeline.celery_app import app
from nlp_pipeline.tasks.directory_reader import DirectoryReader

logger = get_task_logger(__name__)


class DirectoryReaderCommonCrawl(DirectoryReader):
    name = "Directory Reader Common Crawl Relations"
    source_type = "CommonCrawl"
    extension = ".html"
    pipeline_name = "common_crawl"


app.register_task(DirectoryReaderCommonCrawl())
