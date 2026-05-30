from typing import Dict, List, Optional

from pydantic import BaseModel


class Instance(BaseModel):
    date: Optional[str] = None
    year: Optional[int] = None
    score: Optional[float] = None
    de_version: str = "0.0.0"


class DEResponse(BaseModel):
    """
    Model for Date Extraction (DE) VertexAI endpoint response.
    """

    predictions: List[Dict[str, Instance]]
