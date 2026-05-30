"""
Schema for article level data incoming to BOL Product Embedding pipeline.

Sample:
{
  "supplier_vid": "example-vid-001",
  "source": "bol-example-002",
  "source_type": "bol_evidence",
  "text": "(1 PACKAGE ONLY) 1EA OF 105-70HP_4P-6P_380V_50HZ _",
  "evidence_date": "2016-08-22T00:00:00.000Z",
  "prompts": {
    "cleaning_prompt": "Text for a super smart cleaning prompt.",
    "product_extraction_prompt": "Text for a super smart extraction prompt."
  },
  "input_texts": {
    "cleaning_input_text": "(1 PACKAGE ONLY) 1EA OF 105-70HP_4P-6P_380V_50HZ _",
    "product_extraction_text": "(1 PACKAGE ONLY) 1EA OF 105-70HP_4P-6P_380V_50HZ"
  },
  "llm_extracted_products": [
    "105-70HP_4P-6P_380V_50HZ"
  ],
  "llm_model": "text-bison@001"
}
"""

from typing import List

from pydantic import BaseModel
from typing_extensions import TypedDict

from nlp_pipeline.schema.common import BOLSourceType

VERSION = "0.0.0"


class Prompts(TypedDict):
    cleaning_prompt: str
    product_extraction_prompt: str


class InputTexts(TypedDict):
    cleaning_input_text: str
    product_extraction_text: str


class BOLProductEmbeddingInput(BaseModel):
    supplier_vid: str
    source: str
    source_type: BOLSourceType
    text: str
    evidence_date: str
    prompts: Prompts
    input_texts: InputTexts
    llm_extracted_products: List[str]
    llm_model: str
