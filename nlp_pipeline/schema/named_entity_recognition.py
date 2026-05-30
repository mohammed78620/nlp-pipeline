from typing import List, Optional

from nlp_pipeline.schema.segmentation import SegmentedArticle, SegmentedArticleBatch
from nlp_pipeline.schema.segmentation import Sentence as SegmentationSentence
from nlp_pipeline.schema.vertexai.response.named_entity_recognition import Entity


class Sentence(SegmentationSentence):
    entities: List[Entity]


class NERedArticle(SegmentedArticle):
    sentences: List[Sentence]


class NERedArticleBatch(SegmentedArticleBatch):
    articles: List[Optional[NERedArticle]]
