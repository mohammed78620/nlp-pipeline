from typing import Dict, List, Optional

from pydantic import BaseModel

from nlp_pipeline.schema.vertexai.response.named_entity_recognition import Entity


class LinkedEntity(Entity):
    vid: Optional[str] = None
    display_name: Optional[str] = None
    nel_score: float
    nel_version: str = "0.0.0"


class NELResponse(BaseModel):
    """
    Model for Named Entity Linking (NEL) Vertex AI endpoint response.
    """

    predictions: List[Dict[str, List[LinkedEntity]]]
