"""
Datatypes that are likely to be shared across schemas
"""

from enum import Enum

from pydantic import BaseModel

from nlp_pipeline.settings import VERSION


class BOLSourceType(str, Enum):
    """
    Types of BOL Evidence  i.e. source_type field has this value if is from BOL
    """

    bol_evidence = "bol_evidence"
    ik_us_evidence = "ik_us_evidence"
    ik_global_evidence = "ik_global_evidence"
    commerce_evidence = "commerce_evidence"


class Process(BaseModel):
    """
    A process is a representation to capture manipulations performed at a task or pipeline level.

    Inherit from this class and extend to capture any required metadata.
    """

    name: str
    pipeline_version: str = VERSION
    schema_version: str
    created_on: str
    batch_id: str

    class Config:
        extra = "forbid"
