from typing import Dict, List, Optional

from pydantic import BaseModel

from nlp_pipeline.schema.sagemaker.response.named_entity_recognition import Entity


class LinkedEntity(Entity):
    vid: Optional[str]
    display_name: Optional[str]
    nel_score: float
    nel_version: str = "0.0.0"


class NELResponse(BaseModel):
    """
    Model for Named Entity Linking (NEL) Sagemaker endpoint response.
    """

    batch_size: int
    predictions: Dict[str, List[LinkedEntity]]
