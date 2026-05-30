from typing import List

from pydantic import BaseModel

from nlp_pipeline.schema.vertexai.response.named_entity_recognition import Entity


class Annotation(BaseModel):
    entities: List[Entity]


class TextEvidence(BaseModel):
    annotation: Annotation
    text: str
    id: str


class NELPayload(BaseModel):
    """
    Model for Named Entity Linking (NEL) Vertex AI endpoint payload.
    """

    instances: List[TextEvidence]
