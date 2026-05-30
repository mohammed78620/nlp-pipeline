from typing import List

from pydantic import BaseModel


class Text(BaseModel):
    id: str
    text: str


class NERPayload(BaseModel):
    """
    Model for Named Entity Recognition (NER) Vertex AI endpoint payload.
    """

    instances: List[Text]
