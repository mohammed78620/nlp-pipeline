from typing import List

from pydantic import BaseModel

from nlp_pipeline.schema.vertexai.response.named_entity_recognition import Entity


class Annotation(BaseModel):
    entities: List[Entity]


class TextEvidence(BaseModel):
    annotation: Annotation
    id: str
    text: str


class REPayload(BaseModel):
    """
    Model for Relation Extraction (RE) Vertex AI endpoint payload.
    """

    instances: List[TextEvidence]
