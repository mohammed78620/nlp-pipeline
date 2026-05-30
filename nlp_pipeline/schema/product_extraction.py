from typing import List, Optional

from nlp_pipeline.schema.segmentation import SegmentedArticle, SegmentedArticleBatch
from nlp_pipeline.schema.segmentation import Sentence as SegmentationSentence
from nlp_pipeline.schema.vertexai.response.product_extraction import Product


class Sentence(SegmentationSentence):
    products: Optional[List[Product]] = None


class PEedArticle(SegmentedArticle):
    sentences: List[Sentence]


class PEedArticleBatch(SegmentedArticleBatch):
    articles: List[Optional[PEedArticle]]
