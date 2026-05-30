from typing import List

from pydantic import BaseModel

from nlp_pipeline.schema.vertexai.response.named_entity_recognition import Entity
from nlp_pipeline.schema.vertexai.response.relation_extraction import Relation


class FinalisedSentence(BaseModel):
    entities = List[Entity]
    relations = List[Relation]


class FinalisedArticle(BaseModel):
    sentences: List[FinalisedSentence]
