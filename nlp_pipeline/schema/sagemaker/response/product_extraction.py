from typing import Dict, List

from pydantic import BaseModel


class Product(BaseModel):
    id: int
    text: str
    type: str
    token_start: int
    token_end: int
    end_pos: int
    start_pos: int
    pe_score: float
    pe_version: str = "0.0.0"


class PEResponse(BaseModel):
    """
    Model for Product Extraction (PE) Sagemaker endpoint response.
    """

    batch_size: int
    predictions: Dict[str, List[Product]]
