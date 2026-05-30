from typing import Dict, List

from typing_extensions import TypedDict

from nlp_pipeline.schema.directory_reader_bol_product_embedding import (
    DRBOLProductEmbeddingArticle,
    DRBOLProductEmbeddingBatch,
    Metadata,
)
from nlp_pipeline.schema.product_embedding import Embedding


class ProductEmbedding(TypedDict):
    model_name: str


class BOLProductEmbeddingMetadata(Metadata):
    product_embedding: ProductEmbedding


class BOLProductEmbeddingArticle(DRBOLProductEmbeddingArticle):
    """
    Output article of BOL Product Embedding
    """

    products_embeddings: Dict[str, Embedding]
    metadata: BOLProductEmbeddingMetadata


class BOLProductEmbeddingBatch(DRBOLProductEmbeddingBatch):
    """
    Output of BOL Product Embedding
    """

    articles: List[BOLProductEmbeddingArticle]
