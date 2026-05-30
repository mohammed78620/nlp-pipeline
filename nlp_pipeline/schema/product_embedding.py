from typing import Dict, List

from pydantic import BaseModel

from nlp_pipeline.schema.product_extraction_chatgpt import PEedArticle, PEedArticleBatch, ProductExtractionMetadata


class Embedding(BaseModel):
    embedding: List[float]


class ProductEmbeddingSettings(BaseModel):
    model_name: str


class ProductEmbeddingMetadata(ProductExtractionMetadata):
    product_embedding: ProductEmbeddingSettings


class ProductEmbeddingArticle(PEedArticle):
    products: List[str]
    products_embeddings: Dict[str, Embedding]
    metadata: ProductEmbeddingMetadata


class ProductEmbeddingArticleBatch(PEedArticleBatch):
    articles: List[ProductEmbeddingArticle]
