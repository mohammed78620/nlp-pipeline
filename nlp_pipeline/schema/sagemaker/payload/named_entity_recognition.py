from typing import List

from pydantic import BaseModel


class Instance(BaseModel):
    id: str
    text: str


class NERPayload(BaseModel):
    """
    Model for Named Entity Recognition (NER) Sagemaker endpoint payload.
    """

    texts: List[Instance]
