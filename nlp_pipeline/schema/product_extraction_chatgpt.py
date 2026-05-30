from typing import List, Optional

from pydantic import BaseModel

from nlp_pipeline.schema.directory_reader import MetaJson, RawArticle, RawArticleBatch


class ProductExtractionSettings(BaseModel):
    prompt_template: str
    llm_model: str
    max_prod_str_tokens: int
    min_num_products: int
    bad_response_length: int
    max_product_length: int
    text: str


class ProductExtractionMetadata(MetaJson):
    product_extraction: ProductExtractionSettings


class PEedArticle(RawArticle):
    text: str
    products: List[str]
    metadata: ProductExtractionMetadata


class PEedArticleBatch(RawArticleBatch):
    articles: List[Optional[PEedArticle]]
