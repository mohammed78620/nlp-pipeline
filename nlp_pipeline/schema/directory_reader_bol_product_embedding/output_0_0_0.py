"""
Schema for the output of Directory Reader BOL Production Embedding.
"""

from typing import List

from pydantic import BaseModel
from typing_extensions import TypedDict

from nlp_pipeline.schema.directory_reader import RawArticleBatch

VERSION = "0.0.0"


class Prompts(TypedDict):
    cleaning_prompt: str
    product_extraction_prompt: str


class IntermediaryTexts(TypedDict):
    cleaning_input_text: str
    product_extraction_text: str


class Metadata(BaseModel):
    prompts: Prompts
    input_texts: IntermediaryTexts
    llm_extracted_products: List[str]
    llm_model: str


class DRBOLProductEmbeddingArticle(BaseModel):
    """
    Output article of Directory Reader BOL Product Embedding
    """

    id: str
    supplier_vid: str
    source: str
    source_type: str
    text: str
    evidence_date: str
    processing_date: str
    metadata: Metadata


class DRBOLProductEmbeddingBatch(RawArticleBatch):
    """
    Output Directory Reader BOL Product Embedding
    """

    articles: List[DRBOLProductEmbeddingArticle]
