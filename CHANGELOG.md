
# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

For more information, please read [CONTRIBUTING.md](CONTRIBUTING.md)

# [2.6.0] - 2024-12-2
- TASK - [SCI-5334](https://atlassian.net/browse/SCI-5334)
    - A pipeline to process bigtable webz data
-  BUG - fix bigtable lexisnexis pipeline to properly extract metadata from article
- TASK - improve bigtable lexisnexis logging

# [2.5.0] - 2024-11-17
- TASK - [SCI-5361](https://atlassian.net/browse/SCI-5361)
    - A pipeline to process bigtable lexisnexis info

# [2.4.1] - 2024-11-01
- TASK - [SCI-5382](https://atlassian.net/browse/SCI-5382)
    - Update model of Node Products DB model to use less columns i.e. now only vid, product, emb
    - Apply fitering and normalization rules to products across product pipelines i.e. uppercase, strip, filter
    - Switch embedding model default to text-embedding-004

# [2.4.0] - 2024-10-02
- TASK -  [SCI-328](https://atlassian.net/browse/SCI-328)
    - RelationExtraction: Filter sentences with too many entities or estimated to take too long
    - RelationExtraction: As well as split batches based on sentence count, split based on estimated time cost
    - New EnvVars: RE_MAX_ENTITIES, RE_MAX_TIME_COST, RE_TIME_COST

# [2.3.7] - 2024-09-19
- TASK - [SCI-5330](https://atlassian.net/browse/SCI-5330)
    - BUG - Fix bol pipelines to accept commerce_evidence source type

# [2.3.6] - 2024-09-03
- TASK - [SCI-5250](https://atlassian.net/browse/SCI-5250)
    - BUG - retry inserting products to products db when deadlock error appears

# [2.3.5] - 2024-08-28
- TASK - [SCI-5243](https://atlassian.net/browse/SCI-5243)
    - BUG - Fix race condition when inserting the same row into node_products tables

# [2.3.4] - 2024-08-22
- TASK - [ENG-6379](https://atlassian.net/browse/ENG-6379)
    - BOL Product Extraction
        - Unique and sort product list
        - Don't attempt to retry prompt if response was ["UNKNOWN"]
        - Add test case to BOL Product Publish to make check DB has result

# [2.3.3] - 2024-08-16
- TASK - [ENG-6379](https://atlassian.net/browse/ENG-6379)
    - BUG - Fix shadowing of BOLProductPrecleaning schema elements
    - IMPROVEMENT - Only show error for last LLM failed attempt
    - Python 3.10 -> 3.11

# [2.3.2] - 2024-08-16
- TASK - [ENG-6379](https://atlassian.net/browse/ENG-6379)
    - IMPROVEMENT - Rework BOLProductEmbedding and BOLProductEmbeddingPublish to be easier to test and validate.

# [2.3.1] - 2024-08-15
- TASK - [ENG-6379](https://atlassian.net/browse/ENG-6379)
    - BUG - Fix filtering of extracted products to exact match in BOL Product Extraction
    - BUG - Fix strip terms not stripping in BOL Product Extraction Precleaning
    - BUG - Fix incorrect keys in intermediary_text in the BOL Product Extraction pipeline
    - IMPROVEMENT - Add retries to BOL Product Extraction and BOL Product Extraction Precleaning in the event of no products in a non-errored query
    - IMPROVEMENT - Add more unit tests
    - IMPROVEMENT - Update BOL Product Extraction default block
    - IMPROVEMENT - Change test_chain integration tests to polling

# [2.3.0] - 2024-07-18
- TASK - [ENG-6379](https://atlassian.net/browse/ENG-6379)
    - Pipelines
        - Rename DirectoryReaderBolProductExtraction (DRBPE) to DirectoryReaderBolProductEmbedding (DRBPEmbed) as it only did embeddings.
        - Create new pipeline for Bol Extraction: DirectoryReaderBolProductExtraction (DRBPExtract). Only extracts, no embedding.
            - New tasks: BOLProductExtraction, BOLProductExtractionPrecleaning
    - Pipeline Tasks
        - Modify Publish task to output data as compressed JSONL if given a list rather than a dict. Still outputs JSON if dict
        - Fix DirectoryReaderBolProductEmbedding from prematurely deleting file before it has finished processing.
        - Modify DirectoryReaderBolProductEmbedding to handle new schema as well as previous
    - Misc
        - Upgrade pydantic for v1 to v2.3.0. If using Optional, you now need to give the default value
    - Env Vars:
        - Rename Env Var BLACKLISTED_BOL_PRODUCTS to BOL_PRODUCT_EMBEDDING_PRODUCT_BLACKLIST
        - New Env Vars:
            - BOL_PRODUCT_EXTRACTION_EXTRACTION_BLOCK_TERMS
            - BOL_PRODUCT_EXTRACTION_EXTRACTION_PROMPT
            - BOL_PRODUCT_EXTRACTION_GCP_LOCATION
            - BOL_PRODUCT_EXTRACTION_LLM_MODEL
            - BOL_PRODUCT_EXTRACTION_PRECLEANING_PROMPT
            - BOL_PRODUCT_EXTRACTION_PRECLEANING_STRIP_TERMS
            - BOL_PRODUCT_EXTRACTION_HYPER_TEMP
            - BOL_PRODUCT_EXTRACTION_HYPER_MAX_TOKENS
            - BOL_PRODUCT_EXTRACTION_HYPER_TOP_P
            - BOL_PRODUCT_EXTRACTION_HYPER_TOP_K
            - BOL_PRODUCT_EMBEDDING_QUEUE_NAME
            - BOL_PRODUCT_EXTRACTION_PRECLEANING_QUEUE_NAME
            - BOL_PRODUCT_EXTRACTION_QUEUE_NAME
            - BOL_PRODUCT_PUBLISH_QUEUE_NAME
            - BOL_PRODUCT_EXTRACTION_ERROR_QUEUE_NAME
            - BOL_PRODUCT_EXTRACTION_PRECLEANING_ERROR_QUEUE_NAME

# [2.2.0] - 2024-06-17
- TASK - [ENG-6078](https://atlassian.net/browse/ENG-6078)
    - Bol products pipeline can blacklist products via env var and update embedding error handling.
    - Bol products pipeline node_products models updated and insertion logic updated.

# [2.1.0] - 2024-05-22
- TASK - [ENG-6078](https://atlassian.net/browse/ENG-6078)
    - A pipeline to publish bol product to gcp and different vector table.
        - update run.py script to trigger new pipeline

# [2.0.2] - 2024-05-03
- TASK - [ENG-6216](https://atlassian.net/browse/ENG-6216)
    - Update vertex_ai error handling
        - NER and RE task publishes errors to error queues when max retries have exceeded limit.
        - NEL task setting allow for endpoint to fail.

# [2.0.1] - 2024-04-19
- TASK - [ENG-6118](https://atlassian.net/browse/ENG-6118)
    - Improve endpoint error handling
        - No longer using raw_predict feature for predict calls to endpoints so that correct
          exceptions / more detailed errors are raised.
        - Added `allow_endpoint_failure` parameter to tasks. Default behaviour is False.
          Currentlyy only used by DateExtraction so that when max retries is exceeded it falls back to
          alternative data source i.e. meta. In the instance reaches this condition the response is {} which triggers
          a KeyError in the task's `process_response` method.
        - Include traceback on some endpoint errors.
- TASK - Update dependencies. Including pre-commit. Added bandit to dev dependencies (used by pre-commit)
- TASK - [ENG-6098](https://atlassian.net/browse/ENG-6098)
    - celery worker shutdown when disk is full.
    - directory reader task and publish task use tempfile module.
    - script to send payloads to endpoints.

# [2.0.0] - 2024-02-09
- TASK - [ENG-5876](https://atlassian.net/browse/ENG-5876)
    - Change Edgar Directory Reader to handle filing text being HTML
    - Refactor Edgar Directory Reader to tidy up code and add input article validator
    - Changed schema for Edgar so filing text doesn't appear in the meta data
    - Modify Segmentation's handling of Edgar articles to improve "pre-segmenting"

# [1.1.40] - 2024-01-23
- TASK - [ENG-5802](https://atlassian.net/browse/ENG-5802)
    - Add header containing subfolder path to rabbitMQ messages
- Switch over to new Versed Basic Coref package

# [1.1.39] - 2024-01-15
- TASK - [ENG-5833](https://atlassian.net/browse/ENG-5833)
    - nlp pipeline does not raises expection if postgres db password env var is empty
- TASK - [ENG-5826](https://atlassian.net/browse/ENG-5826)
    - rename directory reader tasks
- TASK - [ENG-5794](https://atlassian.net/browse/ENG-5794)
    - seperate company mention crawls to news crawls
- TASK - [ENG-5820](https://atlassian.net/browse/ENG-5820)
    - env var to override pipelines output path

# [1.1.38] - 2024-01-05
- TASK - [ENG-5681](https://atlassian.net/browse/ENG-5681)
    - Pipeline to process edgar input.
- TASK - [ENG-5705](https://atlassian.net/browse/ENG-5705)
    - Add ability to override queue names with envvar
    - Update poetry version for CI/CD
    - Correct private repo call for coref library

# [1.1.36] - 2023-12-08
- TASK - Update DE to send new payload format for endpoint

# [1.1.35] - 2023-12-07
- TASK - [ENG-5625](https://atlassian.net/browse/ENG-5625)
    - Make DE Task favour meta_date.
- FIX - Change how responses from VertexAI are handled to be the new batched predictions format.

# [1.1.34] - 2023-08-29
- TASK - [ENG-5278](https://atlassian.net/browse/ENG-5278)
    - update pipeline to upload products to postgres db
    - unit test and integration test added
# [1.1.29] - 2023-08-25
- TASK - reset lsh cache when limit reached in segmentation task.

# [1.1.27] - 2023-08-25
- TASK - Change empty batch handling in the product description pipeline to reduce misleading error messages.

# [1.1.26] - 2023-08-24
- TASK - Update Supabase details to point to the new Pro Plan project.

# [1.1.25] - 2023-08-21
- FIX - [ENG-5179](https://atlassian.net/browse/ENG-5179)
    - Fix handling of source field during export to supabase
- TASK - Make embedding task's input validation more explicit regarding the issue it encounters.
- TASK - Rework the Docker compose scripts to be more explicit about the environment it interacts with.
- FIX - Correct name of Publish Product unittest file
- TASK - Make settings file callable so as to reveal certain setup values.

# [1.1.24] - 2023-08-18
- FIX - [ENG-5169](https://atlassian.net/browse/ENG-5169)
    - Fix source_type handling in DR BoL Evidence Descriptions
    - Added script to run a file through the DR BoL Evidence Description pipeline
- TASK - [ENG-5103](https://atlassian.net/browse/ENG-5103)Add script for investigating homepages invalid VIDs issue
- TASK - [ENG-5176](https://atlassian.net/browse/ENG-5176)
    - Add better handling of insufficient quota error in chatgpt code
    - Reduce number of retries on OpenAI caller
- TASK - [ENG-5177](https://atlassian.net/browse/ENG-5177)
    - Add filtering to products to exclude instance of "Unknown"
- TASK - [ENG-5178](https://atlassian.net/browse/ENG-5178)
    - Change ChatGPT Product Extraction prompt

# [1.1.23] - 2023-08-09
- FIX - [ENG-5084](https://atlassian.net/browse/ENG-5084)
    - add retrying with exponential backoff for openai
- TASK - minimum number of tokens in product string.
- TASK - lowercase the product string in queries.

# [1.1.22] - 2023-07-26
- FIX - [ENG-5101](https://atlassian.net/browse/ENG-5101)
    - Remove leading " - " from product output.
- TASK - Modify OpenAI test case in attempt for it to be less likely to fail.

# [1.1.21] - 2023-07-26
- FIX - [ENG-5091](https://atlassian.net/browse/ENG-5091)
    - product_source_type is incorrect in supabase.
# [1.1.20] - 2023-07-26
- TASK - [ENG-5091](https://atlassian.net/browse/ENG-5091)
    - directory reader to read bol evidence descriptions.
# [1.1.19] - 2023-07-10
- TASK - [ENG-5058](https://atlassian.net/browse/ENG-5058)
    - Modify Product Extraction pipeline (Directory Reader Homepages) to use ChatGPT.

# [1.1.18] - 2023-06-14
- TASK - [ENG-4981](https://atlassian.net/browse/ENG-4981)
    - modify nlp-pipeline to use gcp services

# [1.1.17] - 2023-05-17
- FIX - [ENG-4916](https://atlassian.net/browse/ENG-4916)
    - home pages directory reader gets meta json error.

# [1.1.16] - 2023-05-10
- FIX - [ENG-4844](https://atlassian.net/browse/ENG-4844)
    - Check if extra_header_info is not None before loading as json string.

# [1.1.15] - 2023-04-26
- TASK - [ENG-4782](https://atlassian.net/browse/ENG-4782)
    - Directory reader for common crawl source type.

# [1.1.14.2] - 2023-04-25
- TASK - [RD-530](https://atlassian.net/browse/RD-530)
    - Remove meta descriptions from NLP pipeline.

# [1.1.14] - 2023-03-10
- TASK - [ENG-4012](https://atlassian.net/browse/ENG-4012)
    - Add an acronym resolver to the pipeline which identifies acronym and replaces them with their backronyms.

# [1.1.12] - 2023-02-10
- TASK - [ENG-4407](https://atlassian.net/browse/ENG-4459)
    - update the segmentation of a sentence.

# [1.1.11] - 2023-01-30
- TASK - [ENG-4407](https://atlassian.net/browse/ENG-4407)
    - Allow overriding of NLP / Crawl output path via environment variable.
    - Small change to no endpoint existing error handling

# [1.1.10] - 2023-01-17
- TASK - [RD-412](https://atlassian.net/browse/RD-412) Improve segmentation

# [1.1.9] - 2022-12-12
- TASK - [QA-3847](https://atlassian.net/browse/QA-3847) Add new Pipleine Company Mentions

# [1.1.8] - 2022-10-28
- TASK - [QA-2474](https://atlassian.net/browse/QA-2474) Reduce batch size for certain retry attempts
- TASK - [QA-3465](https://atlassian.net/browse/QA-3465) Exclude articles based on topics
- TASK - [QA-3394](https://atlassian.net/browse/QA-3394) Handle Endpoint not Found in Account

# [1.1.7] - 2022-10-10
- TASK - [QA-3321](https://atlassian.net/browse/QA-3321) Add all remaining LexisNexis fields into article metadata

# [1.1.6] - 2022-10-06
- TASK - [QA-3262](https://atlassian.net/browse/QA-3262) Skip DE if article provides date

# [1.1.5] - 2022-10-05
- FIX - [QA-3290](https://atlassian.net/browse/QA-3220) ExtraHeaderInfo Pydantic Model must allow a vid field

# [1.1.4] - 2022-10-04
- TASK - [QA-3220](https://atlassian.net/browse/QA-3220) Configure SM endpoint names via env varibles
- TASK - [QA-3112](https://atlassian.net/browse/QA-3112) Disable nuking for unpredictable product metas

# [1.1.3] - 2022-09-29
- TASK - [QA-3194](https://atlassian.net/browse/QA-3194) Add Endpoint versions to pipeline data
- TASK - [QA-3188](https://atlassian.net/browse/QA-3188) Refactor sentence structure

# [1.1.2] - 2022-09-23
- TASK - [QA-3178](https://atlassian.net/browse/QA-3178) Refactor article id
- TASK - [QA-3118](https://atlassian.net/browse/QA-3118) Refactor Publish Task
- TASK - [QA-3158](https://atlassian.net/browse/QA-3158) Eval Metadata

# [1.1.1] - 2022-09-21
## Added
- TASK - [QA-3074](https://atlassian.net/browse/QA-3074) Fix version handling

# [1.1.0] - 2022-09-21
## Added
- TASK - [QA-2941](https://atlassian.net/browse/QA-2941) Homepage Directory Reader
- TASK - [QA-2056](https://atlassian.net/browse/QA-2956) Homepage NER
- TASK - [QA-3075](https://atlassian.net/browse/QA-3075) Refactor Metadata
