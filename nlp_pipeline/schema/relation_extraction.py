from typing import List, Optional

from nlp_pipeline.schema.named_entity_recognition import NERedArticleBatch, SegmentedArticle, Sentence
from nlp_pipeline.schema.vertexai.response.relation_extraction import Relation


class REedSentence(Sentence):
    relations: List[Relation]


class REedArticle(SegmentedArticle):
    sentences: List[REedSentence]


class REedArticeBatch(NERedArticleBatch):
    articles: List[Optional[REedArticle]]
