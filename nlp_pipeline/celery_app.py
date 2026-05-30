import logging
import logging.handlers
import time

import logging_json
from celery import Celery
from celery._state import get_current_task
from celery.app import trace
from celery.signals import after_setup_logger

import nlp_pipeline.celery_config as celery_config
from nlp_pipeline.settings import (
    BOL_PRODUCT_EMBEDDING_ERROR_QUEUE_NAME,
    BOL_PRODUCT_EXTRACTION_ERROR_QUEUE_NAME,
    BOL_PRODUCT_EXTRACTION_PRECLEANING_ERROR_QUEUE_NAME,
    BOL_PRODUCT_PUBLISH_ERROR_QUEUE_NAME,
    LOGS_DIR,
    NAMED_ENTITY_RECOGNITION_ERROR_QUEUE_NAME,
    RELATION_EXTRACTION_ERROR_QUEUE_NAME,
)

trace.LOG_SUCCESS = """Task %(name)s[%(id)s] succeeded in %(runtime)ss"""

app = Celery(
    "nlp_pipeline",
    include=[
        "nlp_pipeline.tasks.directory_reader",
        "nlp_pipeline.tasks.directory_reader_bol_evidence_descriptions",
        "nlp_pipeline.tasks.directory_reader_bol_product_embedding",
        "nlp_pipeline.tasks.directory_reader_bol_product_extraction",
        "nlp_pipeline.tasks.directory_reader_bigtable_lexisnexis",
        "nlp_pipeline.tasks.directory_reader_bigtable_webz",
        "nlp_pipeline.tasks.directory_reader_common_crawl",
        "nlp_pipeline.tasks.directory_reader_company_mentions",
        "nlp_pipeline.tasks.directory_reader_edgar",
        "nlp_pipeline.tasks.directory_reader_homepage",
        "nlp_pipeline.tasks.directory_reader_lexis_nexis",
    ],
)
app.config_from_object(celery_config)

logger = logging.getLogger(__name__)


def declare_queues_with_retry(retries=10, delay=3):
    for attempt in range(retries):
        try:
            with app.connection() as connection:
                channel = connection.channel()
                channel.queue_declare(queue=BOL_PRODUCT_EMBEDDING_ERROR_QUEUE_NAME, durable=True)
                channel.queue_declare(queue=BOL_PRODUCT_EXTRACTION_ERROR_QUEUE_NAME, durable=True)
                channel.queue_declare(queue=BOL_PRODUCT_EXTRACTION_PRECLEANING_ERROR_QUEUE_NAME, durable=True)
                channel.queue_declare(queue=BOL_PRODUCT_PUBLISH_ERROR_QUEUE_NAME, durable=True)
                channel.queue_declare(queue=NAMED_ENTITY_RECOGNITION_ERROR_QUEUE_NAME, durable=True)
                channel.queue_declare(queue=RELATION_EXTRACTION_ERROR_QUEUE_NAME, durable=True)
            logger.info("Queues declared successfully.")
            return
        except Exception as e:
            logger.warning(f"RabbitMQ not ready (attempt {attempt + 1}/{retries}): {e}")
            time.sleep(delay)
    raise Exception("RabbitMQ not available after retries, could not declare queues.")


declare_queues_with_retry()


class TaskFormatter(logging_json.JSONFormatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.get_current_task = get_current_task
        except ImportError:
            self.get_current_task = lambda: None

    def format(self, record):
        task = self.get_current_task()
        if task and task.request:
            try:
                record.__dict__.update(
                    task={"id": task.request.id, "name": task.name}, runtime=record.__dict__["args"]["runtime"]
                )
            except Exception:
                record.__dict__.update(task={"id": task.request.id, "name": task.name}, runtime=None)
        else:
            try:
                record.__dict__.update(
                    task={"id": record.__dict__["args"]["id"], "name": record.__dict__["args"]["name"]}, runtime=None
                )
            except Exception:
                record.__dict__.update(task=None, runtime=None)

        if record.__dict__.get("data", None):
            del record.__dict__["data"]
        return super().format(record)


@after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    formatter = TaskFormatter(
        fields={
            "level.name": "levelname",
            "thread.name": "threadName",
            "process.name": "processName",
            "timestamp": "asctime",
            "task": "task",
            "runtime": "runtime",
        }
    )

    fh = logging.handlers.RotatingFileHandler(LOGS_DIR / "logs.json", maxBytes=1024**3, backupCount=10)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
