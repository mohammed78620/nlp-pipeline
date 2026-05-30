from typing import List

from pydantic import BaseModel


class Text(BaseModel):
    id: str
    text: str


class DEPayload(BaseModel):
    """
    Model for Date Extraction (DE) Sagemaker endpoint payload.
    """

    texts: List[Text]
    min_year: int
    max_year: int
