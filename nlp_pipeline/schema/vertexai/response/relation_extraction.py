from typing import Dict, List

from pydantic import BaseModel, Field


class Relation(BaseModel):
    from_field: int = Field(..., alias="from")
    to: int
    label: str
    class_field: int = Field(..., alias="class")
    re_score: float
    re_version: str = "0.0.0"


class REResponse(BaseModel):
    """
    Model for Relation Extraction (RE) Vertex AI endpoint response.
    """

    predictions: List[Dict[str, List[Relation]]]
