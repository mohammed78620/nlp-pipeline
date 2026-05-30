# NLP Pipeline
The NLP Pipeline is a tool used to extract evidences from craweled articles. It leverages concurrency and high throughout via a distributed orchestration of tasks and jobs managed by [Celery](https://docs.celeryq.dev/en/stable/) and [RabbitMQ](https://www.rabbitmq.com/).


# Table of Contents
- [⚙️ Development](#development)
- [🥑 Celery Configuration](#celery-configuration)
- [🖋️ Scripts](#scripts)
- [Environment Variables](#environment-variables)
- [🧪 Testing](#testing)
- [Scripts](#scripts)


# Development
The NLP  is configured with an **out-of-the-box** development environment via [docker](https://www.docker.com/) and managed with [docker compose](https://docs.docker.com/compose/). Before continuing, **make sure you have docker available in your system**.

To run the development server, you need to copy your GCP filekey and then docker compose in your preferred cli:

```bash
cp ~/.config/gcloud/application_default_credentials.json .application_default_credentials.json
docker-compose -f docker-compose.dev.yaml up -d
```

If you receive a permission error trying to install dependencies with poetry try:

```bash
poetry self add keyrings.google-artifactregistry-auth
poetry config http-basic.versed-pip oauth2accesstoken $(gcloud auth print-access-token)
```

Docker will orchestrate the following containers

- ⛏️ A Celery Worker
- ✉️ A Rabbit MQ Server at http://localhost:5672
- 📊 A Rabbit MQ Management Panel at http://localhost:15672
- ⏳ A Redis Server at http://localhost:6379

You're all set now! Go to http://localhost:15672, you should see the Rabbit UI. Happy coding!

Check live logs coming from the Celery Worker

```bash
docker logs nlp-pipeline-worker-1 --follow
```


# Celery Configuration
Be aware of the celery configuration at `celery_config.py`. This configuration overrides default values set by celery and leaves some of the configurations untouched. To get more details on each option, check the full docs [here](https://docs.celeryq.dev/en/latest/userguide/configuration.html#configuration-directives). Be very careful when updating the celery configuration, since changing some settings can result in odd behaviour.


# Scripts
At `nlp_pipeline/scripts` you will find a collection of scripts that you might need to use. Here is a short overview of them.


## Running the Pipeline
If you ever need to manually trigger a pipeline job, you may do so via the `run.py` script located at `nlp_pipeline/scripts/run.py`. You will need to specify the file key to be processed as well as the batch size.

```bash
poetry run python -m nlp_pipeline.scripts.run -k <file_key> -s <batch_size>
```


# Environment Variables

## Setup
Define envvars in a `.env` file. The file `.env.test` contains envvars that are intended to overwrite `.env` during pytest tests and MUST NOT contain secrets since it is committed.

For values that are a list type, in the .env file they need to be provided as a comma separated string with no whitespace after the commas. When the value is loaded it will be converted into a list

IMPORTANT NOTE: The values in the env file need to match [Django Environ conventions](https://django-environ.readthedocs.io/en/latest/types.html). Noted below are the expected types and defaults. If a list type is expected the value in env file should be comma seperated and not appear as a list with brackets. For example, a BLACKLIST may have a default value of `["UNKNOWN", "FLAGS"]` but the value in the env file would need be `BLACKLIST=UNKNOWN,FLAGS`

## Variables
    ENV (str): Used for environment specific checks e.g. making sure tests aren't being run on dev or prod. See `settings.py` for options.
    USER (str): Used for segregating test run results. Set to own company username or thing running the code.

    BASIC_COREF_NLTK_DIR (str, Optional): Can be used to optionally override the download location of NLTK data. [Default: "/usr/local/share/nltk_data/"]

    OVERRIDE_NLP_OUTPUT_PATH (str, Optional): override the output path to pipelines for one-off tasks. [Default: None]

    DESTINATION_BUCKET (str, Optional): gcs bucket to publish to. Overwritten when ENV = test. [Default: development bucket]
    DESTINATION_PATH (str, Optional): Path in DESTINATION_BUCKET. Overwritten when ENV = test. [Default: development]
    DESTINATION_REGION (str, Optional): Region of gcs buckets. Overwritten when ENV = test. [Default: development]

    GOOGLE_APPLICATION_CREDENTIALS (str, Optional): Path of the Google Cloud service account credentials file on your system [Default: None]
    GOOGLE_PROJECT_ID (str, Optional): The project ID is a unique identifier for a project in the Google Cloud Platform (GCP) [Default: None]

    CELERY_BROKER_URL (str): URL with credentials
    CELERY_RESULT_BACKEND (str): URL with credentials

    EXCLUDE_LEXISNEXIS_TOPICS (list, Optional) = topics to exclude e.g. Finance,Media,Society [Default: []]

    # Relation Extraction
    RE_MAX_ENTITIES (int, Optional): Max entities a sentence may have for RE otherwise gets skipped. [Default: 30]
    RE_MAX_TIME_COST (int, Optional): Max estimated time cost of a RE payload based on number of entities (in milliseconds). [Default: 5900]
    RE_TIME_COST (int, Optional): How long it takes to perform a RE between 2 entities (in milliseconds). [Default: 100]

    # Product Extraction
    PE_VERTEXAI_MODEL (str, Optional): VertexAI Text Embedding model to use for Product Extraction. [Default: textembedding-gecko@001]
    PE_OPENAI_PROMPT (str, Optional): Prompt to be used for ChatGPT Product Extraction. Include one {} instance. [Default: "List as bullet points products and services in the following: '{}'"],
    PE_OPENAI_MODEL (str, Optional): ChatGPT model to use for Product Extraction. [Default: gpt-3.5-turbo]
    PE_OPENAI_MAX_PRODUCT_STR_TOKENS (int, Optional): Number of tokens/words product string can have before it gets truncated. [Default: 255]
    PE_OPENAI_MIN_PRODUCT_STR_TOKENS (int, Optional): Minimum number of tokens/words products string can have. [Default: 3]
    PE_OPENAI_MAX_PRODUCT_LENGTH (int, Optional): Threshold at which number of characters in product would cause it to be filtered. [Default: 30]
    PE_OPENAI_RETRY_ATTEMPTS (int, Optional): Number of retries when a bad response is received. [Default: 3]
    PE_OPENAI_BAD_RESPONSE_LENGTH (int, Optional): Number of characters in a product that would cause response to be considered bad. [Default: 50]
    PE_OPENAI_MIN_NUM_PRODUCTS (int, Optional): Minimun number of products to be present for a response to be considered good. [Default: 2]

    OPENAI_API_KEY (str): API key for OpenAI / ChatGPT.
    OPENAI_TIMEOUT (int, Optional): Timeout OpenAI queries after duration. Use None to have no timeout. [Default: 20]
    SUPABASE_SERVICE_KEY (str): Service key for Supabase project.

    LSH_FINGERPRINT_MEMORY_LIMIT (int): The memory limit before resetting lsh cache [Default: 8182]

    POSTGRES_DATABASE_PASSWORD (str, Optional): Password to postgres db [Default: None]
    SQLALCHEMY_DATABASE_URL (str, Optional): URI string used to specify a database connection [Default: None]

    # BOL Product Embedding
    BOL_PRODUCT_EMBEDDING_PRODUCT_BLACKLIST (list, Optional) products to exclude during BoL embedding (occurs only in it's associated DR) e.g. "['screw']" [Default: []]

    # BOL Product Extraction Settings
    BOL_PRODUCT_EXTRACTION_EXTRACTION_BLOCK_TERMS (list, Optional) Terms that are to be dropped out. [Default: ["UNKNOWN", "BOXES", "BOX", "CARTONS", "CARTON", "PALLETS", "PALLET"]]
    BOL_PRODUCT_EXTRACTION_EXTRACTION_PROMPT (str, Optional) The prompt to use for extraction.
    BOL_PRODUCT_EXTRACTION_GCP_LOCATION (str, Optional) Region of LLM. [Default: "us-central1"]
    BOL_PRODUCT_EXTRACTION_LLM_MODEL (str, Optional) The LLM model to use [Default: "text-bison@002"]
    BOL_PRODUCT_EXTRACTION_PRECLEANING_PROMPT (str, Optional) The prompt to use for precleaning.
    BOL_PRODUCT_EXTRACTION_PRECLEANING_STRIP_TERMS (list[str], Optional) Terms that are to be removed from product descriptions during precleaning. [Default: ["SLAC", "SHIPPER S LOAD, COUNT & SEAL", "FREIGHT PREPAID"]]

    # BOL Product Extraction Hyperparameters
    BOL_PRODUCT_EXTRACTION_HYPER_TEMP (float, Optional) [Default: 0.1]
    BOL_PRODUCT_EXTRACTION_HYPER_MAX_TOKENS (int, Optional) [Default: 256]
    BOL_PRODUCT_EXTRACTION_HYPER_TOP_P (float, Optional) [Default: 0.8]
    BOL_PRODUCT_EXTRACTION_HYPER_TOP_K (int, Optional) [Default: 40]

    # Queue Name overrides
    ACRONYM_RESOLVER_QUEUE_NAME (str, Optional): [Default: "acronym-resolver"]
    BASIC_COREFERENCE_QUEUE_NAME (str, Optional): [Default: "basic-coreference"]
    BOL_PRODUCT_EMBEDDING_QUEUE_NAME (str, Optional): [Default: "bol-product-embedding"]
    BOL_PRODUCT_EXTRACTION_PRECLEANING_QUEUE_NAME  (str, Optional): [Default: "bol-product-extraction-precleaning"]
    BOL_PRODUCT_EXTRACTION_QUEUE_NAME  (str, Optional): [Default: "bol-product-extraction"]
    BOL_PRODUCT_PUBLISH_QUEUE_NAME (str, Optional): [Default: "bol-product-publish"]
    DATE_EXTRACTION_QUEUE_NAME (str, Optional): [Default: "date-extraction"]
    DIRECTORY_READER_QUEUE_NAME (str, Optional): [Default: "directory-reader"]
    NAMED_ENTITY_LINKING_QUEUE_NAME (str, Optional): [Default: "named-entity-linking"]
    NAMED_ENTITY_RECOGNITION_QUEUE_NAME (str, Optional): [Default: "named-entity-recognition"]
    PRODUCT_EMBEDDING_QUEUE_NAME (str, Optional): [Default: "product-embedding"]
    PRODUCT_EXTRACTION_CHATGPT_QUEUE_NAME (str, Optional): [Default: "product-extraction-chatgpt"]
    PRODUCT_EXTRACTION_QUEUE_NAME (str, Optional): [Default: "product-extraction"]
    PUBLISH_PRODUCT_QUEUE_NAME (str, Optional): [Default: "publish-product"]
    PUBLISH_QUEUE_NAME (str, Optional): [Default: "publish"]
    RELATION_EXTRACTION_QUEUE_NAME (str, Optional): [Default: "relation-extraction"]
    SEGMENTATION_QUEUE_NAME (str, Optional): [Default: "segmentation"]

    # Error Queue Name overrides
    BOL_PRODUCT_EMBEDDING_ERROR_QUEUE_NAME (str, Optional) [Default: "bol-product-embedding-errors"]
    BOL_PRODUCT_EXTRACTION_ERROR_QUEUE_NAME (str, Optional) [Default: "bol-product-extraction-errors"]
    BOL_PRODUCT_EXTRACTION_PRECLEANING_ERROR_QUEUE_NAME (str, Optional) [Default: "bol-product-extraction-precleaning-errors"]
    BOL_PRODUCT_PUBLISH_ERROR_QUEUE_NAME (str, Optional) [Default: "bol-product-publish-errors"]
    NAMED_ENTITY_RECOGNITION_ERROR_QUEUE_NAME (str, Optional): [Default: "named-entity-recognition-errors"]
    RELATION_EXTRACTION_ERROR_QUEUE_NAME (str, Optional): [Default: "relation-extraction-errors"]

# Testing
NLP Pipeline runs tests via the [pytest](https://docs.celeryq.dev/en/stable/userguide/testing.html) library and implements unit testing for Celery Tasks, as well as integration tests.

To run the tests from a docker container, simply run
```bash
docker exec -it <container-id> bash -c 'poetry run pytest'
```

Alternatively, tests can be run from source ( prior to having a poetry environment installed )
```bash
poetry run pytest
```

# starting celery worker
to start worker run command below
```
python3.11 -m celery -A nlp_pipeline.celery_app:app worker --loglevel=INFO --concurrency=<number of workers> -Q <queue name> -n <queue name>@<hostname>
```
# task and task queues
 left is task and right is queue

- `acronym_resolver`                           -> acronym-resolver
- `basic_coreference`                          -> basic-coreference
- `bol_product_embedding`                      -> bol-product-embedding
- `bol_product_extraction`                     -> bol-product-extraction
- `bol_product_extraction_precleaning`         -> bol-product-extraction-precleaning
- `bol_product_publish`                        -> bol-product-publish
- `date_extraction`                            -> date-extraction
- `directory_reader_bol_evidence_descriptions` -> directory-reader
- `directory_reader_bol_product_embedding`     -> directory-reader
- `directory_reader_bol_product_extraction`    -> directory-reader
- `directory_reader_common_crawl`              -> directory-reader
- `directory_reader_company_mentions`          -> directory-reader
- `directory_reader_edgar`                     -> directory-reader
- `directory_reader_homepage`                  -> directory-reader
- `directory_reader_lexis_nexis`               -> directory-reader
- `directory_reader`                           -> directory-reader
- `named_entity_linking`                       -> named-entity-linking
- `named_entity_recognition`                   -> named-entity-recognition
- `product_embedding`                          -> product-embedding
- `product_extraction_chatgpt`                 -> product-extraction
- `product_extraction` (LEGACY)                -> product-extraction
- `publish_product_to_gcp`                     -> publish-product
- `publish_product` (LEGACY)                   -> publish-product
- `publish`                                    -> publish
- `relation_extraction`                        -> relation-extraction
- `segmentation`                               -> segmentation

# Pipelines
list of tasks in order for each pipeline
## Default Pipeline
1. Segmentation
2. Named Entity Recognition
3. Relation Extraction
4. Named Entity Linking
5. Date Extraction
## Homepages
1. Segmentation
2. Product Extraction ChatGPT
3. Product Embedding
4. Publish Products to GCP
## BOL evidence
1. Segmentation
2. Product Extraction ChatGPT
3. Product Embedding
4. Publish Products to GCP
## BOL Product Embedding
1. BoL Product Embedding
2. BoL Product Publish
3. Publish to GCP
## BOL Product Extract
1. BOL Product Extraction Precleaning
2. BOL Product Extraction
3. Publish to GCP
## Company mentions
1. Segmentation
2. Named Entity Recognition
4. Named Entity Linking
## Common crawl
1. Segmentation
2. Named Entity Recognition
3. Relation Extraction
4. Named Entity Linking
5. Date Extraction
## Lexis nexis
1. Segmentation
2. Named Entity Recognition
3. Relation Extraction
4. Named Entity Linking
5. Date Extraction
## Edgar
1. Basic Coreference
2. Acronymn Resolver
3. Segmentation
4. Named Entity Recognition
5. Relation Extraction
6. Named Entity Linking


## Running Tests in VSCode

- Compose up `docker-compose.test.yaml`
- In your `tasks.json` add:
```json
		{
			"label": "coverage-off",
			"type": "shell",
			"command": "sed -i 's/addopts = \"--cov/#addopts = \"--cov/' pyproject.toml",
			"problemMatcher": []
		},
		{
			"label": "coverage-on",
			"type": "shell",
			"command": "sed -i 's/#addopts = \"--cov/addopts = \"--cov/' pyproject.toml",
			"problemMatcher": []
		}
```
- In your `launch.json` add:
```json
        {
            "name": "Python: Remote Attach",
            "type": "python",
            "request": "attach",
            "port": 5678,
            "host": "localhost",
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}",
                    "remoteRoot": "/app"
                }
            ]
        },
        {
            "name": "Python: Debug Tests",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "purpose": [
                "debug-test"
            ],
            "preLaunchTask": "coverage-off",
            "postDebugTask": "coverage-on",
            "console": "integratedTerminal",
            "justMyCode": false
        },
```
- If wanting to debug test Docker code, Launch `Python: Remote Attach` to connect debugger to Docker instance of the worker.
- Run task in Discovery. It will use the `Python: Debug Tests` profile.
- Have to re-compose between integration test runs due to Fingerprinter.

## Advanced VSCode Test Debugging

Here's a way to auto compose up and down the docker for tests. Still requires manually connecting to the Docker debugging using the `Python: Remote Attach`.

- Have these tasks in your `tasks.json`
```json
		{
			"label": "compose-up-test-docker",
			"type": "docker-compose",
			"dockerCompose": {
				"up": {
					"detached": true,
					"build": true
				},
				"files": [
					"${workspaceFolder}/docker-compose.test.yaml"
				]
			}
		},
		{
			"label": "compose-down-test-docker",
			"type": "docker-compose",
			"dockerCompose": {
				"down": {
					"removeVolumes": true
				},
				"files": [
					"${workspaceFolder}/docker-compose.test.yaml"
				]
			}
		},
		{
			"label": "coverage-off",
			"type": "shell",
			"command": "sed -i 's/addopts = \"--cov/#addopts = \"--cov/' pyproject.toml",
			"problemMatcher": []
		},
		{
			"label": "coverage-on",
			"type": "shell",
			"command": "sed -i 's/#addopts = \"--cov/addopts = \"--cov/' pyproject.toml",
			"problemMatcher": []
		},
		{
			"label": "start-testing",
			"dependsOn": [
				"coverage-off",
				"compose-up-test-docker"
			]
		},
		{
			"label": "end-testing",
			"dependsOn": [
				"coverage-on",
				"compose-down-test-docker"
			]
		}
```
- Change `Python: Debug Tests` to:
```json
        {
            "name": "Python: Debug Tests",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "purpose": [
                "debug-test"
            ],
            "preLaunchTask": "start-testing",
            "postDebugTask": "end-testing",
            "console": "integratedTerminal",
            "justMyCode": false
        }
```
