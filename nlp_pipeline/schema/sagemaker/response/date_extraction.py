from typing import Dict, Optional

from pydantic import BaseModel


class Instance(BaseModel):
    date: Optional[str]
    year: Optional[int]
    score: Optional[float]
    de_version: str = "0.0.0"


class DEResponse(BaseModel):
    """
    Model for Date Extraction (DE) Sagemaker endpoint response.
    """

    batch_size: int
    predictions: Dict[str, Instance]
