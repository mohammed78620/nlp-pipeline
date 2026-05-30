from typing import List, Optional

from pydantic import BaseModel

from nlp_pipeline.schema.directory_reader import RawArticle, RawArticleBatch


class Sentence(BaseModel):
    id: str
    fingerprint: str
    text: str


class SegmentedArticle(RawArticle):
    sentences: List[Sentence]
    pre_segmented_text: Optional[List[str]] = None


class SegmentedArticleBatch(RawArticleBatch):
    articles: List[SegmentedArticle]
