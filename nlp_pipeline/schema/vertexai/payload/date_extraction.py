from typing import List

from pydantic import BaseModel


class DEInstance(BaseModel):
    id: str
    text: str


class DEPayload(BaseModel):
    """
    Model for Date Extraction (DE) Vertex AI endpoint payload.
    """

    instances: List[DEInstance]
