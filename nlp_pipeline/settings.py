import importlib.metadata
import os
from enum import Enum
from pathlib import Path

import environ
import toml
from google.cloud import aiplatform


class Environment(Enum):
    """
    Used to denote the envirnoment the code is running in.
    """

    dev = "development"  # local / dev
    test = "test"  # running test cases
    stage = "staging"
    prod = "production"


# vertexai batching approach
class Approach(Enum):
    soft = "soft"
    conservative = "conservative"
    hard = "hard"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class Plan(Enum):
    soft = {
        "NER_BATCH_SIZE": 100,
        "RE_BATCH_SIZE": 100,
        "NEL_BATCH_SIZE": 100,
        "DE_BATCH_SIZE": 10,
        "PE_BATCH_SIZE": 100,
    }

    conservative = {
        "NER_BATCH_SIZE": 925,
        "RE_BATCH_SIZE": 825,
        "NEL_BATCH_SIZE": 900,
        "DE_BATCH_SIZE": 48,
        "PE_BATCH_SIZE": 900,
    }

    hard = {
        "NER_BATCH_SIZE": 1300,
        "RE_BATCH_SIZE": 1100,
        "NEL_BATCH_SIZE": 1200,
        "DE_BATCH_SIZE": 64,
        "PE_BATCH_SIZE": 1200,
    }


environment = environ.FileAwareEnv(
    ENV=(str),
    USER=(str),
    OVERRIDE_NLP_OUTPUT_PATH=(str, None),
    CELERY_BROKER_URL=(str),
    LSH_SEED=(int, 1),
    LSH_FINGERPRINT_MEMORY_LIMIT=(int, 8182),
    MIN_JACCARD_DR=(float, 0.9),
    MIN_JACCARD_SEG=(float, 0.9),
    APPROACH=(str, None),
    NER_BATCH_SIZE=(int, Plan.soft.value["NER_BATCH_SIZE"]),
    # Relation Extraction
    RE_BATCH_SIZE=(int, Plan.soft.value["RE_BATCH_SIZE"]),
    RE_MAX_ENTITIES=(int, 30),
    RE_TIME_COST=(int, 100),
    RE_MAX_TIME_COST=(int, 5900),
    NEL_BATCH_SIZE=(int, Plan.soft.value["NEL_BATCH_SIZE"]),
    DE_BATCH_SIZE=(int, Plan.soft.value["DE_BATCH_SIZE"]),
    PE_BATCH_SIZE=(int, Plan.soft.value["PE_BATCH_SIZE"]),
    NER_ENDPOINT_NAME=(str, None),
    RE_ENDPOINT_NAME=(str, None),
    NEL_ENDPOINT_NAME=(str, None),
    DE_ENDPOINT_NAME=(str, None),
    PE_ENDPOINT_NAME=(str, None),
    EXCLUDE_LEXISNEXIS_TOPICS=(list, []),
    PE_VERTEXAI_MODEL=(str, "text-embedding-004"),
    PE_OPENAI_PROMPT=(
        str,
        "You're a procurement expert, list as bullet points general product categories (say UNKNOWN if you don't know) from the following, don't make up items, do not include: invoice numbers, product HS codes, addresses and postcodes, and emails: '{}'",
    ),
    PE_OPENAI_MODEL=(str, "gpt-3.5-turbo"),
    PE_OPENAI_MAX_PRODUCT_STR_TOKENS=(int, 255),
    PE_OPENAI_MIN_PRODUCT_STR_TOKENS=(int, 3),
    PE_OPENAI_MAX_PRODUCT_LENGTH=(int, 30),
    PE_OPENAI_RETRY_ATTEMPTS=(int, 3),
    PE_OPENAI_BAD_RESPONSE_LENGTH=(int, 50),
    PE_OPENAI_MIN_NUM_PRODUCTS=(int, 2),
    GOOGLE_APPLICATION_CREDENTIALS=(str, None),
    GOOGLE_PROJECT_ID=(str, None),
    OPENAI_API_KEY=(str),
    OPENAI_TIMEOUT=(int, 20),
    SUPABASE_SERVICE_KEY=(str, None),
    POSTGRES_DATABASE_PASSWORD=(str, None),
    SQLALCHEMY_DATABASE_URL=(str, "postgresql+pg8000://"),
    # BoL Product Embedding Settings
    BOL_PRODUCT_EMBEDDING_PRODUCT_BLACKLIST=(list, []),
    # BoL Product Extraction Settings
    BOL_PRODUCT_EXTRACTION_EXTRACTION_BLOCK_TERMS=(
        list,
        ["UNKNOWN", "BOXES", "BOX", "CARTONS", "CARTON", "PALLETS", "PALLET"],
    ),
    BOL_PRODUCT_EXTRACTION_EXTRACTION_PROMPT=(
        str,
        "You are a procurement expert, please apply the following rules in chronological order: 1. Extract very specific products contained in the following sentence (only return text contained in the sentence) 2. Only return products not peoples names or company names. 3. Return UNKNOWN if the text is not a physical product. 4. If no products are identified return the word: UNKNOWN. 5. Please remove un-necessary additional words associated with the identified products. 6. Delete duplicated extracted products. 7. Please output the products separated by a comma. 8. Keep the text uppercase.: ",
    ),
    BOL_PRODUCT_EXTRACTION_GCP_LOCATION=(str, "us-central1"),
    BOL_PRODUCT_EXTRACTION_LLM_MODEL=(str, "text-bison@002"),
    BOL_PRODUCT_EXTRACTION_PRECLEANING_PROMPT=(
        str,
        "You are the chief editor for the New York Times newspaper, please apply the following rules in chronological order: 1. Correct spelling mistakes in the sentence. 2. Delete product codes, material numbers, invoice numbers and HS codes from the sentence. 3. Remove any irrelevant digits or numbers from the sentence. 4. Remove any mention of quantities of a product from the sentence. 5. Keep the sentence in upper case. \n To the following text: ",
    ),
    BOL_PRODUCT_EXTRACTION_PRECLEANING_STRIP_TERMS=(list, ["SLAC", "SHIPPER S LOAD, COUNT & SEAL", "FREIGHT PREPAID"]),
    # BoL Product Extraction Hyperparameters
    BOL_PRODUCT_EXTRACTION_HYPER_TEMP=(float, 0.1),
    BOL_PRODUCT_EXTRACTION_HYPER_MAX_TOKENS=(int, 256),
    BOL_PRODUCT_EXTRACTION_HYPER_TOP_P=(float, 0.8),
    BOL_PRODUCT_EXTRACTION_HYPER_TOP_K=(int, 40),
    # Task Queue Names
    ACRONYM_RESOLVER_QUEUE_NAME=(str, "acronym-resolver"),
    BASIC_COREFERENCE_QUEUE_NAME=(str, "basic-coreference"),
    BOL_PRODUCT_EMBEDDING_QUEUE_NAME=(str, "bol-product-embedding"),
    BOL_PRODUCT_EXTRACTION_PRECLEANING_QUEUE_NAME=(str, "bol-product-extraction-precleaning"),
    BOL_PRODUCT_EXTRACTION_QUEUE_NAME=(str, "bol-product-extraction"),
    BOL_PRODUCT_PUBLISH_QUEUE_NAME=(str, "bol-product-publish"),
    DATE_EXTRACTION_QUEUE_NAME=(str, "date-extraction"),
    DIRECTORY_READER_QUEUE_NAME=(str, "directory-reader"),
    NAMED_ENTITY_LINKING_QUEUE_NAME=(str, "named-entity-linking"),
    NAMED_ENTITY_RECOGNITION_QUEUE_NAME=(str, "named-entity-recognition"),
    PRODUCT_EMBEDDING_QUEUE_NAME=(str, "product-embedding"),
    PRODUCT_EXTRACTION_CHATGPT_QUEUE_NAME=(str, "product-extraction-chatgpt"),
    PRODUCT_EXTRACTION_QUEUE_NAME=(str, "product-extraction"),
    PUBLISH_PRODUCT_QUEUE_NAME=(str, "publish-product"),
    PUBLISH_QUEUE_NAME=(str, "publish"),
    RELATION_EXTRACTION_QUEUE_NAME=(str, "relation-extraction"),
    SEGMENTATION_QUEUE_NAME=(str, "segmentation"),
    # Task Error Queue Names
    BOL_PRODUCT_EMBEDDING_ERROR_QUEUE_NAME=(str, "bol-product-embedding-errors"),
    BOL_PRODUCT_EXTRACTION_ERROR_QUEUE_NAME=(str, "bol-product-extraction-errors"),
    BOL_PRODUCT_EXTRACTION_PRECLEANING_ERROR_QUEUE_NAME=(str, "bol-product-extraction-precleaning-errors"),
    BOL_PRODUCT_PUBLISH_ERROR_QUEUE_NAME=(str, "bol-product-publish-errors"),
    NAMED_ENTITY_RECOGNITION_ERROR_QUEUE_NAME=(str, "named-entity-recognition-errors"),
    RELATION_EXTRACTION_ERROR_QUEUE_NAME=(str, "relation-extraction-errors"),
)

if environment("APPROACH"):
    if not environment("APPROACH") in Approach.list():
        raise Exception("Improperly configured. Given approach is not valid.")

    APPROACH = getattr(Plan, environment("APPROACH"))
    NER_BATCH_SIZE = APPROACH.value["NER_BATCH_SIZE"]
    RE_BATCH_SIZE = APPROACH.value["RE_BATCH_SIZE"]
    NEL_BATCH_SIZE = APPROACH.value["NEL_BATCH_SIZE"]
    DE_BATCH_SIZE = APPROACH.value["DE_BATCH_SIZE"]
    PE_BATCH_SIZE = APPROACH.value["PE_BATCH_SIZE"]


# Environment Variables
try:
    # If pyproject.toml exists then likely a dev env so not working from installed package
    # thus, pull VERSION from the toml
    meta = toml.load("pyproject.toml")
    VERSION = meta["tool"]["poetry"]["version"]
except FileNotFoundError:
    # Else, it surely exists as a package, right?
    try:
        # what the name should be
        VERSION = importlib.metadata.version(__package__)
    except importlib.metadata.PackageNotFoundError:
        # what it might actually be (due to bad dir structure)
        VERSION = importlib.metadata.version("nlp_pipeline")


ENV = Environment(environment("ENV"))
USER = environment("USER")

OVERRIDE_NLP_OUTPUT_PATH = environment("OVERRIDE_NLP_OUTPUT_PATH")

CELERY_BROKER_URL = environment("CELERY_BROKER_URL")

LSH_SEED = environment("LSH_SEED")
LSH_FINGERPRINT_MEMORY_LIMIT = environment("LSH_FINGERPRINT_MEMORY_LIMIT")
MIN_JACCARD_DR = environment("MIN_JACCARD_DR")
MIN_JACCARD_SEG = environment("MIN_JACCARD_DR")

NER_BATCH_SIZE = environment("NER_BATCH_SIZE")
RE_BATCH_SIZE = environment("RE_BATCH_SIZE")
RE_MAX_ENTITIES = environment("RE_MAX_ENTITIES")
RE_TIME_COST = environment("RE_TIME_COST")
RE_MAX_TIME_COST = environment("RE_MAX_TIME_COST")
NEL_BATCH_SIZE = environment("NEL_BATCH_SIZE")
DE_BATCH_SIZE = environment("DE_BATCH_SIZE")
PE_BATCH_SIZE = environment("PE_BATCH_SIZE")
NER_ENDPOINT_NAME = environment("NER_ENDPOINT_NAME")
RE_ENDPOINT_NAME = environment("RE_ENDPOINT_NAME")
NEL_ENDPOINT_NAME = environment("NEL_ENDPOINT_NAME")
DE_ENDPOINT_NAME = environment("DE_ENDPOINT_NAME")
PE_ENDPOINT_NAME = environment("PE_ENDPOINT_NAME")


if ENV.value != ENV.prod:
    if not NER_ENDPOINT_NAME:
        NER_ENDPOINT_NAME = "NamedEntityRecognitionDev"

    if not RE_ENDPOINT_NAME:
        RE_ENDPOINT_NAME = "RelationExtractionDev"

    if not NEL_ENDPOINT_NAME:
        NEL_ENDPOINT_NAME = "NamedEntityLinkingDev"

    if not DE_ENDPOINT_NAME:
        DE_ENDPOINT_NAME = "DateExtractionDev"

    if not PE_ENDPOINT_NAME:
        PE_ENDPOINT_NAME = "Endpoint doesnt exist"
else:
    if not all([NER_ENDPOINT_NAME, RE_ENDPOINT_NAME, NEL_ENDPOINT_NAME, DE_ENDPOINT_NAME, PE_ENDPOINT_NAME]):
        raise Exception("Improperly configured. VertexAI Endpoint Names ENV variables are missing.")

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent

# Directoriess
TMP_DIR = BASE_DIR / "tmp/"
LOGS_DIR = BASE_DIR / "logs/"

for DIR in [TMP_DIR, LOGS_DIR]:
    if not os.path.exists(DIR):
        os.makedirs(DIR)

# Lexis Nexis topic filtering
EXCLUDE_LEXISNEXIS_TOPICS = environment.list("EXCLUDE_LEXISNEXIS_TOPICS")

# supabase
SUPABASE_SERVICE_KEY = environment("SUPABASE_SERVICE_KEY")

# openai
OPENAI_API_KEY = environment("OPENAI_API_KEY")
OPENAI_TIMEOUT = environment("OPENAI_TIMEOUT")

# product extraction settings
PE_VERTEXAI_MODEL = environment("PE_VERTEXAI_MODEL")
PE_OPENAI_PROMPT = environment("PE_OPENAI_PROMPT")
PE_OPENAI_MODEL = environment("PE_OPENAI_MODEL")
PE_OPENAI_MAX_PRODUCT_STR_TOKENS = environment("PE_OPENAI_MAX_PRODUCT_STR_TOKENS")
PE_OPENAI_MIN_PRODUCT_STR_TOKENS = environment("PE_OPENAI_MIN_PRODUCT_STR_TOKENS")
PE_OPENAI_MAX_PRODUCT_LENGTH = environment("PE_OPENAI_MAX_PRODUCT_LENGTH")
PE_OPENAI_RETRY_ATTEMPTS = environment("PE_OPENAI_RETRY_ATTEMPTS")
PE_OPENAI_BAD_RESPONSE_LENGTH = environment("PE_OPENAI_BAD_RESPONSE_LENGTH")
PE_OPENAI_MIN_NUM_PRODUCTS = environment("PE_OPENAI_MIN_NUM_PRODUCTS")

# BoL Product Extraction
BOL_PE_GCP_LOCATION = environment("BOL_PRODUCT_EXTRACTION_GCP_LOCATION")
BOL_PE_LLM_MODEL = environment("BOL_PRODUCT_EXTRACTION_LLM_MODEL")
BOL_PE_PRECLEANING_PROMPT = environment("BOL_PRODUCT_EXTRACTION_PRECLEANING_PROMPT")
BOL_PE_EXTRACTION_PROMPT = environment("BOL_PRODUCT_EXTRACTION_EXTRACTION_PROMPT")
BOL_PE_PRECLEANING_STRIP_TERMS = environment("BOL_PRODUCT_EXTRACTION_PRECLEANING_STRIP_TERMS")
BOL_PE_EXTRACTION_BLOCK_TERMS = environment("BOL_PRODUCT_EXTRACTION_EXTRACTION_BLOCK_TERMS")
# BoL Product Extraction Hyperparameters
BOL_PE_HYPERPARAMETERS = {
    "temperature": environment("BOL_PRODUCT_EXTRACTION_HYPER_TEMP"),
    "max_output_tokens": environment("BOL_PRODUCT_EXTRACTION_HYPER_MAX_TOKENS"),
    "top_p": environment("BOL_PRODUCT_EXTRACTION_HYPER_TOP_P"),
    "top_k": environment("BOL_PRODUCT_EXTRACTION_HYPER_TOP_K"),
}
# BoL Product Embedding
BOL_PRODUCT_EMBEDDING_PRODUCT_BLACKLIST = environment("BOL_PRODUCT_EMBEDDING_PRODUCT_BLACKLIST")

# google cloud
GOOGLE_APPLICATION_CREDENTIALS = environment("GOOGLE_APPLICATION_CREDENTIALS")
GOOGLE_PROJECT_ID = environment("GOOGLE_PROJECT_ID")
aiplatform.init(project=GOOGLE_PROJECT_ID)

# google cloud postgres db
POSTGRES_DATABASE_PASSWORD = environment("POSTGRES_DATABASE_PASSWORD")
SQLALCHEMY_DATABASE_URL = environment("SQLALCHEMY_DATABASE_URL")

# error queues
BOL_PRODUCT_EMBEDDING_ERROR_QUEUE_NAME = environment("BOL_PRODUCT_EMBEDDING_ERROR_QUEUE_NAME")
BOL_PRODUCT_EXTRACTION_ERROR_QUEUE_NAME = environment("BOL_PRODUCT_EXTRACTION_ERROR_QUEUE_NAME")
BOL_PRODUCT_EXTRACTION_PRECLEANING_ERROR_QUEUE_NAME = environment("BOL_PRODUCT_EXTRACTION_PRECLEANING_ERROR_QUEUE_NAME")
BOL_PRODUCT_PUBLISH_ERROR_QUEUE_NAME = environment("BOL_PRODUCT_PUBLISH_ERROR_QUEUE_NAME")
NAMED_ENTITY_RECOGNITION_ERROR_QUEUE_NAME = environment("NAMED_ENTITY_RECOGNITION_ERROR_QUEUE_NAME")
RELATION_EXTRACTION_ERROR_QUEUE_NAME = environment("RELATION_EXTRACTION_ERROR_QUEUE_NAME")


if __name__ == "__main__":
    print(f"version: {VERSION}")
    print(f"environment: {ENV.value}")
    print(f"openai_api_key: {OPENAI_API_KEY[:7] + '***' + OPENAI_API_KEY[-3:]}")  # censor
    print(f"supabase key: {SUPABASE_SERVICE_KEY[:3] + '***' + SUPABASE_SERVICE_KEY[-3:]}")  # censor
