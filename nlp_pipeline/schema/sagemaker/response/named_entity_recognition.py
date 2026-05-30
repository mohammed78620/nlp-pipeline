from typing import Dict, List

from pydantic import BaseModel


class Entity(BaseModel):
    id: int
    text: str
    type: str
    token_start: int
    token_end: int
    end_pos: int
    start_pos: int
    ner_score: float
    ner_version: str = "0.0.0"


class NERResponse(BaseModel):
    """
    Model for Named Entity Recognition (NER) Sagemaker endpoint response.
    """

    batch_size: int
    predictions: Dict[str, List[Entity]]
