from pgvector.sqlalchemy import Vector
from sqlalchemy import TIMESTAMP, Column, Text, func
from sqlalchemy.orm import mapped_column

from nlp_pipeline.models.base import Base


class NodeProduct(Base):
    __tablename__ = "node_products"

    __mapper_args__ = {"confirm_deleted_rows": False}

    vid = Column(Text, primary_key=True, nullable=False)
    product = Column(Text, primary_key=True, nullable=False)
    emb_model = Column(Text, nullable=False)
    product_source_type = Column(Text, nullable=False)
    product_source = Column(Text, primary_key=True)
    created_on = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    modified_on = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    emb = mapped_column(Vector(768))
    prompt = Column(Text)
    source_text = Column(Text)


class NodeProductV2Old(Base):
    # Decommissioned in favour of NodeProductV2Fixed
    __tablename__ = "node_products_v2_old"

    __mapper_args__ = {"confirm_deleted_rows": False}

    vid = Column(Text, primary_key=True, nullable=False)
    product = Column(Text, primary_key=True, nullable=False, comment="Product name/description.")
    emb_model = Column(Text, nullable=False)
    product_source_type = Column(Text, nullable=False)
    product_source = Column(Text, primary_key=True)
    created_on = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    modified_on = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    emb = Column(Vector(768), nullable=False, comment="Product embedding.")
    source_text = Column(Text, comment="Original text product came from.")
    query_metadata = Column("metadata", Text, comment="Metadata relating to the generation of the product.")


class NodeProductV2(Base):
    # Fixed as per SCI-5382
    __tablename__ = "node_products_v2"

    __mapper_args__ = {"confirm_deleted_rows": False}

    vid = Column(Text, primary_key=True, nullable=False)
    product = Column(Text, primary_key=True, nullable=False, comment="Product name/description.")
    emb = Column(Vector(768), nullable=False, comment="Product embedding.")
