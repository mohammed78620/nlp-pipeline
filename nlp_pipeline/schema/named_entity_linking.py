from typing import List, Optional

from nlp_pipeline.schema.relation_extraction import REedArticeBatch, REedArticle, REedSentence
from nlp_pipeline.schema.vertexai.response.named_entity_linking import LinkedEntity


class NELedSentence(REedSentence):
    entities: List[LinkedEntity]


class NELedArticle(REedArticle):
    sentences: List[NELedSentence]


class NELedArticleBatch(REedArticeBatch):
    articles: List[Optional[NELedArticle]]
