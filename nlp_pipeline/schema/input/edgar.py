from typing import List, Optional

from pydantic import BaseModel


class SecApiTaskMessage(BaseModel):
    vid: str
    ticker: str
    form_type: str
    start_year: str
    end_year: str
    delivery_name: str

    class Config:
        extra = "forbid"


class Entity(BaseModel):
    companyName: str  # noqa: N815
    cik: str
    irsNo: Optional[str] = None  # noqa: N815
    stateOfIncorporation: Optional[str] = None  # noqa: N815
    fiscalYearEnd: Optional[str] = None  # noqa: N815
    sic: Optional[str] = None
    type: Optional[str] = None
    act: Optional[str] = None
    fileNo: Optional[str] = None  # noqa: N815
    filmNo: Optional[str] = None  # noqa: N815

    class Config:
        extra = "forbid"


class FileMetadata(BaseModel):
    sequence: Optional[str] = None
    description: Optional[str] = None
    documentUrl: str  # noqa: N815
    type: Optional[str] = None
    size: Optional[str] = None

    class Config:
        extra = "forbid"


class Filing(BaseModel):
    """
    Definitions based on SEC API Documentation
    https://sec-api.io/docs/query-api#response-format
    """

    accessionNo: str  # noqa: N815
    cik: str
    ticker: str
    companyName: str  # noqa: N815
    companyNameLong: str  # noqa: N815
    formType: str  # noqa: N815
    description: str
    linkToFilingDetails: str  # noqa: N815
    linkToTxt: str  # noqa: N815
    linkToHtml: str  # noqa: N815
    linkToXbrl: Optional[str] = None  # noqa: N815
    filedAt: str  # noqa: N815
    periodOfReport: Optional[str] = None  # noqa: N815
    effectivenessDate: Optional[str] = None  # noqa: N815
    registrationForm: Optional[str] = None  # noqa: N815
    referenceAccessionNo: Optional[str] = None  # noqa: N815
    items: Optional[List[str]] = None
    groupMembers: Optional[List[str]] = None  # noqa: N815
    id: str
    entities: List[Optional[Entity]]
    documentFormatFiles: List[FileMetadata]  # noqa: N815
    dataFiles: List[FileMetadata]  # noqa: N815

    class Config:
        extra = "forbid"


class SecFiling(BaseModel):
    """
    Representation of a filing from SEC API.

    Produced by: https://github.com/versed-ai/edgar-preprocessing-worker
    """

    version: str  # Version of worker that produced the data
    worker_query: SecApiTaskMessage  # The query the worker ran to encounter the filing
    query_result: Filing  # The details for this particular filing
    filing_text: str  # The filing document (HTML)

    class Config:
        extra = "forbid"
