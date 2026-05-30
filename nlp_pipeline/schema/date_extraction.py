from typing import List, Optional

from nlp_pipeline.schema.named_entity_linking import NELedArticle, NELedArticleBatch


class DEedArticleBatch(NELedArticleBatch):
    articles: List[Optional[NELedArticle]]
