"""SQLAlchemy persistence for the pricing service.

Tables owned by this service:   price_observations, model_versions
Table read from the web app:     demand  (buyer requests; only the columns the
                                 Demand Board needs are mapped here)
"""
import os
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pricing.db").replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base = declarative_base()


class PriceObservation(Base):
    """A realised resale: what the item originally cost and what it sold for."""
    __tablename__ = "price_observations"
    id = Column(Integer, primary_key=True)
    product_type = Column(String(64), nullable=False, index=True)
    original_price = Column(Float, nullable=False)
    sale_price = Column(Float, nullable=False)
    age_months = Column(Float, nullable=True)
    condition = Column(Integer, nullable=True)          # 1 (like new) .. 5 (heavily used)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ModelVersion(Base):
    __tablename__ = "model_versions"
    id = Column(Integer, primary_key=True)
    model_name = Column(String(32), nullable=False)
    path = Column(Text, nullable=False)
    n_train = Column(Integer, nullable=False)
    holdout_mae = Column(Float, nullable=False)
    holdout_accuracy = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Demand(Base):
    """Read-only view of the web app's `demand` table."""
    __tablename__ = "demand"
    id = Column(Integer, primary_key=True)
    sub_cat = Column(Text, nullable=False)
    college = Column(Text, nullable=False)


OWNED_TABLES = [PriceObservation.__table__, ModelVersion.__table__]


def init_db(include_demand: bool = False) -> None:
    tables = OWNED_TABLES + ([Demand.__table__] if include_demand else [])
    Base.metadata.create_all(engine, tables=tables)
