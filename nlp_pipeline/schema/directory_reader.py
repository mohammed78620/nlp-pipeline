from typing import Dict, List, Optional

from pydantic import BaseModel

from nlp_pipeline.schema.input.edgar import Filing, SecApiTaskMessage


class FingerprintConfig(BaseModel):
    method: str
    version: str

    class Config:
        extra = "forbid"


class LSHFingerprintConfig(FingerprintConfig):
    seed: int
    num_seeds: int
    char_ngram: int
    hashbytes: int
    num_bands: int

    class Config:
        extra = "forbid"


class ExtraHeaderInfo(BaseModel):
    checksum: Optional[str] = None
    ipaddress: Optional[str] = None
    host: Optional[str] = None
    vid: Optional[str] = None

    class Config:
        extra = "allow"


class ExtraEdgarInfo(BaseModel):
    version: str
    worker_query: SecApiTaskMessage
    query_result: Filing


class MetaJson(BaseModel):
    fingerprint: Optional[str] = None
    fingerprint_config: Optional[LSHFingerprintConfig | FingerprintConfig] = None
    timestamp: Optional[int] = None
    wbm_id: Optional[str] = None
    url: Optional[str] = None
    access_epoch: Optional[int] = None
    scraper_type: Optional[str] = None
    extra_header_info: Optional[ExtraHeaderInfo] = None
    host_name: Optional[str] = None
    redirected_from: Optional[str] = None
    date_guess: Optional[str] = None
    date_acc: Optional[str] = None
    meta_date: Optional[str] = None
    meta_year: Optional[int] = None
    guess_method: Optional[str] = None
    year: Optional[int] = None
    date: Optional[str] = None
    date_score: Optional[float] = None
    metajson_extraction_error: Optional[str] = None
    extra_lexis_nexis_info: Optional[Dict] = None
    extra_edgar_info: Optional[ExtraEdgarInfo] = None

    class Config:
        extra = "allow"


class RawArticle(BaseModel):
    id: str
    html: Optional[str] = None
    text: str
    pre_segmented_text: List[str]
    original_compressed_filename: str
    original_html_file: Optional[str] = None
    source_type: str
    source: Optional[str] = None
    evidence_date: Optional[str] = None
    metadata: MetaJson

    class Config:
        extra = "forbid"


class RawArticleBatch(BaseModel):
    batch_id: str
    version: str
    created_on: str
    source_file: str
    source_type: str
    source: str
    articles: List[RawArticle]

    class Config:
        extra = "forbid"
