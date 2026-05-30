from typing import List

from pydantic import BaseModel


class Instance(BaseModel):
    id: str
    text: str


class PEPayload(BaseModel):
    """
    Model for Product Extraction (PE) Sagemaker endpoint payload.
    """

    texts: List[Instance]
