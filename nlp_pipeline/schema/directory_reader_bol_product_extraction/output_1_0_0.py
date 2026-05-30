"""
Schemas related to the outputs of the BOL Product Extraction pipeline.

That means output for:
  - Directory Reader BOL Product Extraction
  - BOL Product Extraction Precleaning
  - BOL Product Extraction


https://atlassian.net/wiki/spaces/SPEC/pages/2986147939/Online+BOL+Product+Extraction+Pipeline

Sample output of the pipeline:
{
  "supplier_vid": "example-vid-001",
  "source": "bol-example-002",
  "source_type": "bol_evidence",
  "text": "boxes of fish",
  "evidence_date": "2016-08-22T00:00:00.000Z",
  "llm_extracted_products": [
    "105-70HP_4P-6P_380V_50HZ"
  ],
  "processes": {[
    "name": "BOL Product Extraction",
    "pipeline_version": "2.3.0",
    "schema_version": "1.0.0",
    "created_on": "2024-08-08T00:00:00.000Z",
    "batch_id": "000001",
    "prompts": {
      "text_cleaning_prompt": "Cleaning prompt: ",
      "product_extraction_prompt": "Extraction prompt: ",
    },
    "intermediary_texts": {
      "text_cleaning": "boxes of fish",
      "product_extraction": "BOXES OF FISH"
    },
    "llm_model": "text-bison@001"
  ]}
}
"""

from typing import Dict, List, Optional

from pydantic import BaseModel
from typing_extensions import TypedDict

from nlp_pipeline.schema.common import BOLSourceType, Process

VERSION = "1.0.0"


##############################################
# Directory Reader BOL Product Extraction Output
##############################################


class DRBOLProductExtractionProcess(Process):
    """
    Metadata after Directory Reader BOL Product Extraction.
    """

    schema_version: str = VERSION
    prompts: Optional[Dict] = None
    intermediary_texts: Optional[Dict] = None
    llm_model: Optional[str] = None

    class Config:
        extra = "forbid"


class BOLProductArticle(BaseModel):
    """
    Output of Directory Reader BOL Product Extraction
    """

    supplier_vid: str
    source_type: BOLSourceType
    source: str
    text: str
    evidence_date: str
    processes: List[DRBOLProductExtractionProcess]

    class Config:
        extra = "forbid"


##############################################
# BOL Product Extraction Precleaning Output
##############################################


class PrecleanedPrompts(TypedDict):
    text_cleaning_prompt: str


class PrecleanedIntermediaryTexts(TypedDict):
    text_cleaning: str


class BOLProductExtractionPrecleaningProcess(DRBOLProductExtractionProcess):
    """
    Metadata after BOL Product Extraction Precleaning task
    """

    prompts: PrecleanedPrompts
    intermediary_texts: PrecleanedIntermediaryTexts
    llm_model: str

    class Config:
        extra = "forbid"


class BOLProductPrecleanedArticle(BOLProductArticle):
    """
    Output of BOL Product Extraction Precleaning
    """

    llm_cleaned_text: str
    processes: List[BOLProductExtractionPrecleaningProcess]

    class Config:
        extra = "forbid"


##############################################
# BOL Product Extraction Output
##############################################


class ExtractedPrompts(TypedDict):
    text_cleaning_prompt: str
    product_extraction_prompt: str


class ExtractedIntermediaryTexts(TypedDict):
    text_cleaning: str
    product_extraction: str


class BOLProductExtractionProcess(DRBOLProductExtractionProcess):
    """
    Metadata after BOL Product Extraction task
    """

    prompts: ExtractedPrompts
    intermediary_texts: ExtractedIntermediaryTexts
    llm_model: str

    class Config:
        extra = "forbid"


class BOLProductExtractedArticle(BOLProductArticle):
    """
    Output of BOL Product Extraction
    """

    llm_extracted_products: List[str]
    processes: List[BOLProductExtractionProcess]

    class Config:
        extra = "forbid"
