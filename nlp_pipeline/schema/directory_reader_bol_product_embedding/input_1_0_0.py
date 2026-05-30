"""
Schema for article level data incoming to BOL Product Embedding pipeline.
"""

# Input schema is the output of BOL Product Extraction Pipeline
from nlp_pipeline.schema.directory_reader_bol_product_extraction import BOLProductExtractedArticle  # noqa

VERSION = "1.0.0"
