from nlp_pipeline.settings import CELERY_BROKER_URL, environment

"""
This is a production ready celery configuration that overrides some base celery configurations.
Some configurations have been omitted in this document, and fallback to default celery's configuration

Check celery configurations here https://docs.celeryq.dev/en/stable/userguide/configuration.html
"""
# TASK SETTINGS #
# Task compression. Can be bzip2 or gzip. Enables Rabbit to handle more messages at the price of
# CPU time to compress/uncompress.
task_compression = "bzip2"
# Task serializer. Can be json, pickle or others.
task_serializer = "json"

# TASK EXECUTION SETTINGS #
# Tracks that a task has started.
task_track_started = True
# The worker processing the task will be killed and replaced with a new one when this is exceeded. Time in seconds.
# None disables time limits.
task_time_limit = None
# The SoftTimeLimitExceeded exception will be raised when this is exceeded. Time in seconds.
task_soft_time_limit = None
# When enabled, task messages will only be acknowledged after the task has been executed. Disabling this option
# will result in odd behaviour, DO NOT CHANGE IT.
task_acks_late = True
# Whether to ignore storing the task return values or not.
task_ignore_result = True

# TASK ROUTING #
# Custom task routing. Directory Reader taks will be routed to queue 'dr', while all other tasks will be routed
# to the default 'celery' queue
task_routes = {
    "nlp_pipeline.tasks.acronym_resolver": {"queue": environment("ACRONYM_RESOLVER_QUEUE_NAME")},
    "nlp_pipeline.tasks.basic_coreference": {"queue": environment("BASIC_COREFERENCE_QUEUE_NAME")},
    "nlp_pipeline.tasks.bol_product_embedding": {"queue": environment("BOL_PRODUCT_EMBEDDING_QUEUE_NAME")},
    "nlp_pipeline.tasks.bol_product_extraction_precleaning": {
        "queue": environment("BOL_PRODUCT_EXTRACTION_PRECLEANING_QUEUE_NAME")
    },
    "nlp_pipeline.tasks.bol_product_extraction": {"queue": environment("BOL_PRODUCT_EXTRACTION_QUEUE_NAME")},
    "nlp_pipeline.tasks.bol_product_publish": {"queue": environment("BOL_PRODUCT_PUBLISH_QUEUE_NAME")},
    "nlp_pipeline.tasks.date_extraction": {"queue": environment("DATE_EXTRACTION_QUEUE_NAME")},
    "nlp_pipeline.tasks.directory_reader_bol_evidence_descriptions": {
        "queue": environment("DIRECTORY_READER_QUEUE_NAME")
    },
    "nlp_pipeline.tasks.directory_reader_bol_product_embedding": {"queue": environment("DIRECTORY_READER_QUEUE_NAME")},
    "nlp_pipeline.tasks.directory_reader_bol_product_extraction": {"queue": environment("DIRECTORY_READER_QUEUE_NAME")},
    "nlp_pipeline.tasks.directory_reader_bigtable_lexisnexis": {"queue": environment("DIRECTORY_READER_QUEUE_NAME")},
    "nlp_pipeline.tasks.directory_reader_bigtable_webz": {"queue": environment("DIRECTORY_READER_QUEUE_NAME")},
    "nlp_pipeline.tasks.directory_reader_common_crawl": {"queue": environment("DIRECTORY_READER_QUEUE_NAME")},
    "nlp_pipeline.tasks.directory_reader_company_mentions": {"queue": environment("DIRECTORY_READER_QUEUE_NAME")},
    "nlp_pipeline.tasks.directory_reader_edgar": {"queue": environment("DIRECTORY_READER_QUEUE_NAME")},
    "nlp_pipeline.tasks.directory_reader_homepage": {"queue": environment("DIRECTORY_READER_QUEUE_NAME")},
    "nlp_pipeline.tasks.directory_reader_lexis_nexis": {"queue": environment("DIRECTORY_READER_QUEUE_NAME")},
    "nlp_pipeline.tasks.directory_reader": {"queue": environment("DIRECTORY_READER_QUEUE_NAME")},
    "nlp_pipeline.tasks.named_entity_linking": {"queue": environment("NAMED_ENTITY_LINKING_QUEUE_NAME")},
    "nlp_pipeline.tasks.named_entity_recognition": {"queue": environment("NAMED_ENTITY_RECOGNITION_QUEUE_NAME")},
    "nlp_pipeline.tasks.product_embedding": {"queue": environment("PRODUCT_EMBEDDING_QUEUE_NAME")},
    "nlp_pipeline.tasks.product_extraction_chatgpt": {"queue": environment("PRODUCT_EXTRACTION_CHATGPT_QUEUE_NAME")},
    "nlp_pipeline.tasks.product_extraction": {"queue": environment("PRODUCT_EXTRACTION_QUEUE_NAME")},
    "nlp_pipeline.tasks.publish_product_to_gcp": {"queue": environment("PUBLISH_PRODUCT_QUEUE_NAME")},
    "nlp_pipeline.tasks.publish": {"queue": environment("PUBLISH_QUEUE_NAME")},
    "nlp_pipeline.tasks.relation_extraction": {"queue": environment("RELATION_EXTRACTION_QUEUE_NAME")},
    "nlp_pipeline.tasks.segmentation": {"queue": environment("SEGMENTATION_QUEUE_NAME")},
}

# BROKER SETTINGS #
# Default broker URL
broker_url = CELERY_BROKER_URL


# TASK RESULT BACKEND #
# The backend used to store task results
# result_backend = CELERY_RESULT_BACKEND
# When enabled, backend will try to retry on the event of recoverable exceptions instead of propagating the exception.
# result_backend_always_retry = True
# The maximum sleep time between two backend operation retry. Time in millis.
# result_backend_max_sleep_between_retries_ms = 3000
# Task result serializer format
# result_serializer = "json"
# Task result compression
# result_compression = "bzip2"
# Enables extended task result attributes (name, args, kwargs, worker, retries, queue, delivery_info)
# to be written to backend.
# result_extended = True
# Task result TTL in seconds. Results will be erased from the backend after the TTL.
# result_expires = timedelta(hours=1)

# WORKER SETTINGS #
# How many messages to prefetch at a time multiplied by the number of concurrent processes. A value of 1
# disables prefetching.
worker_prefetch_multiplier = 1
worker_cancel_long_running_tasks_on_connection_loss = True
