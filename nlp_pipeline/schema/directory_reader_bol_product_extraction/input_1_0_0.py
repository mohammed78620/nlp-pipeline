"""
Schema for article level data incoming to Directory Reader BOL Product Extraction.

Sample:
{
    "supplier_vid": "sample-vid-001",
    "source_type": "bol_evidence",
    "source": "bol-sample-bol-id",
    "text": "nuts, bolts",
    "evidence_date": "2024-01-01T00:00:00.000Z"
}
"""

from pydantic import BaseModel

from nlp_pipeline.schema.common import BOLSourceType

VERSION = "1.0.0"


class BOLProductDescription(BaseModel):
    """
    A BOL Product Description
    """

    supplier_vid: str
    source_type: BOLSourceType
    source: str
    text: str
    evidence_date: str

    class Config:
        extra = "forbid"
