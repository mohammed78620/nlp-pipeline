from enum import Enum

from pydantic import BaseModel

from nlp_pipeline.settings import OVERRIDE_NLP_OUTPUT_PATH, ENV, USER


class BucketOutputConfiguration(BaseModel):
    bucket: str
    region: str
    path: str


class Pipeline(Enum):
    @classmethod
    def get_config_from_environment(cls) -> BucketOutputConfiguration:
        """
        Collects the configuration for the selected environment

        Returns:
            BucketOutputConfiguration: The bucket configuration based on the current environment
        """
        try:
            return getattr(cls, ENV.name).value
        except KeyError:
            message = f"{cls.__name__} does not have the environment {ENV.name} configured. Choose one of {cls.list()}."
            raise Exception(message)

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


# Set up output defaults
bucket_dev = "dev-raw-lake-versed-ai"
bucket_test = "dev-testing-versed-ai"
bucket_stage = "staging-raw-lake-versed-ai"
bucket_prod = "production-raw-lake-versed-ai"
bucket_crawled_dev = "dev-crawl-versed-ai"
bucket_crawled_test = "dev-testing-crawl-versed-ai"
bucket_crawled_stage = "staging-crawl-versed-ai"
bucket_crawled_prod = "production-crawl-versed-ai"


region = "us-east1"

paths = {
    "nlp": "crawled/outputs/",
    "lexisnexis": "lexisnexis/outputs/",
    "product": "product/outputs/",
    "companymentions": "company-mentions/outputs/",
    "commoncrawl": "commoncrawl/outputs/",
    "edgar": "edgar/outputs/",
    "bol_product_embedding": "product_v2/outputs/",
    "bol_product_extraction": "online-bolevidence-products/outputs/",
    "bigtable_lexisnexis": "bigtable_export_lexisnexis/",
    "bigtable_webz": "bigtable_export_webz/",
}

devtest_paths = {
    "nlp": f"{USER}/{paths['nlp']}",
    "lexisnexis": f"{USER}/{paths['lexisnexis']}",
    "product": f"{USER}/{paths['product']}",
    "companymentions": f"{USER}/{paths['companymentions']}",
    "commoncrawl": f"{USER}/{paths['commoncrawl']}",
    "edgar": f"{USER}/{paths['edgar']}",
    "bol_product_embedding": f"{USER}/{paths['bol_product_embedding']}",
    "bol_product_extraction": f"{USER}/{paths['bol_product_extraction']}",
    "bigtable_lexisnexis": f"{USER}/{paths['bigtable_lexisnexis']}",
    "bigtable_webz": f"{USER}/{paths['bigtable_webz']}",
}

# Forced override of typical defaults for one-off tasks
if OVERRIDE_NLP_OUTPUT_PATH:
    for category in paths:
        paths[category] = OVERRIDE_NLP_OUTPUT_PATH
        devtest_paths[category] = OVERRIDE_NLP_OUTPUT_PATH


class CRAWLED(Pipeline):
    dev = {"bucket": bucket_dev, "region": region, "path": devtest_paths["nlp"]}
    test = {"bucket": bucket_test, "region": region, "path": devtest_paths["nlp"]}
    stage = {"bucket": bucket_stage, "region": region, "path": paths["nlp"]}
    prod = {"bucket": bucket_prod, "region": region, "path": paths["nlp"]}


class LEXISNEXIS(Pipeline):
    dev = {"bucket": bucket_dev, "region": region, "path": devtest_paths["lexisnexis"]}
    test = {"bucket": bucket_test, "region": region, "path": devtest_paths["lexisnexis"]}
    stage = {"bucket": bucket_stage, "region": region, "path": paths["lexisnexis"]}
    prod = {"bucket": bucket_prod, "region": region, "path": paths["lexisnexis"]}


class PRODUCT(Pipeline):
    dev = {"bucket": bucket_dev, "region": region, "path": devtest_paths["product"]}
    test = {"bucket": bucket_test, "region": region, "path": devtest_paths["product"]}
    stage = {"bucket": bucket_stage, "region": region, "path": paths["product"]}
    prod = {"bucket": bucket_prod, "region": region, "path": paths["product"]}


class COMPANYMENTIONS(Pipeline):
    dev = {"bucket": bucket_dev, "region": region, "path": devtest_paths["companymentions"]}
    test = {"bucket": bucket_test, "region": region, "path": devtest_paths["companymentions"]}
    stage = {"bucket": bucket_stage, "region": region, "path": paths["companymentions"]}
    prod = {"bucket": bucket_prod, "region": region, "path": paths["companymentions"]}


class COMMONCRAWL(Pipeline):
    dev = {"bucket": bucket_dev, "region": region, "path": devtest_paths["commoncrawl"]}
    test = {"bucket": bucket_test, "region": region, "path": devtest_paths["commoncrawl"]}
    stage = {"bucket": bucket_stage, "region": region, "path": paths["commoncrawl"]}
    prod = {"bucket": bucket_prod, "region": region, "path": paths["commoncrawl"]}


class EDGAR(Pipeline):
    dev = {"bucket": bucket_dev, "region": region, "path": devtest_paths["edgar"]}
    test = {"bucket": bucket_test, "region": region, "path": devtest_paths["edgar"]}
    stage = {"bucket": bucket_stage, "region": region, "path": paths["edgar"]}
    prod = {"bucket": bucket_prod, "region": region, "path": paths["edgar"]}


class BOLPRODUCTEMBEDDING(Pipeline):
    dev = {"bucket": bucket_dev, "region": region, "path": devtest_paths["bol_product_embedding"]}
    test = {"bucket": bucket_test, "region": region, "path": devtest_paths["bol_product_embedding"]}
    stage = {"bucket": bucket_stage, "region": region, "path": paths["bol_product_embedding"]}
    prod = {"bucket": bucket_prod, "region": region, "path": paths["bol_product_embedding"]}


class BOLPRODUCTEXTRACTION(Pipeline):
    dev = {"bucket": bucket_crawled_dev, "region": region, "path": devtest_paths["bol_product_extraction"]}
    test = {"bucket": bucket_test, "region": region, "path": devtest_paths["bol_product_extraction"]}
    stage = {"bucket": bucket_crawled_stage, "region": region, "path": paths["bol_product_extraction"]}
    prod = {"bucket": bucket_crawled_prod, "region": region, "path": paths["bol_product_extraction"]}


class BIGTABLELEXISNEXIS(Pipeline):
    dev = {"bucket": bucket_dev, "region": region, "path": devtest_paths["bigtable_lexisnexis"]}
    test = {"bucket": bucket_test, "region": region, "path": devtest_paths["bigtable_lexisnexis"]}
    stage = {"bucket": bucket_stage, "region": region, "path": paths["bigtable_lexisnexis"]}
    prod = {"bucket": bucket_prod, "region": region, "path": paths["bigtable_lexisnexis"]}


class BIGTABLEWEBZ(Pipeline):
    dev = {"bucket": bucket_dev, "region": region, "path": devtest_paths["bigtable_webz"]}
    test = {"bucket": bucket_test, "region": region, "path": devtest_paths["bigtable_webz"]}
    stage = {"bucket": bucket_stage, "region": region, "path": paths["bigtable_webz"]}
    prod = {"bucket": bucket_prod, "region": region, "path": paths["bigtable_webz"]}


class PipelineOutputs(Enum):
    crawled = CRAWLED
    ln = LEXISNEXIS
    bigtable_lexisnexis = BIGTABLELEXISNEXIS
    bigtable_webz = BIGTABLEWEBZ
    product = PRODUCT
    company_mentions = COMPANYMENTIONS
    common_crawl = COMMONCRAWL
    edgar = EDGAR
    bol_product_embedding = BOLPRODUCTEMBEDDING
    bol_product_extraction = BOLPRODUCTEXTRACTION


# supabase
pe_supabase_dev_table_name = "dev_node_products"
pe_supabase_test_table_name = "test_node_products"
pe_supabase_stage_table_name = "stage_node_products"
pe_supabase_prod_table_name = "node_products"


class SUPABASE(Pipeline):
    dev = {"pe_table_name": pe_supabase_dev_table_name, "url": "https://pfjgphupachjgcscreon.supabase.co"}
    test = {"pe_table_name": pe_supabase_test_table_name, "url": "https://pfjgphupachjgcscreon.supabase.co"}
    stage = {"pe_table_name": pe_supabase_stage_table_name, "url": "https://pfjgphupachjgcscreon.supabase.co"}
    prod = {"pe_table_name": pe_supabase_prod_table_name, "url": "https://pfjgphupachjgcscreon.supabase.co"}


product_nodes_dev_db = "dev_productdb"
product_nodes_test_db = "test_productdb"
product_nodes_stage_db = "productdb"
product_nodes_prod_db = "productdb"


class GCPPOSTGRES(Pipeline):
    dev = {"db": product_nodes_dev_db, "connection_string": "staging-388321:us-east1:product-db"}
    test = {"db": product_nodes_test_db, "connection_string": "staging-388321:us-east1:product-db"}
    stage = {"db": product_nodes_stage_db, "connection_string": "staging-388321:us-east1:product-db"}
    prod = {"db": product_nodes_prod_db, "connection_string": "production-388321:us-east1:product-db"}
