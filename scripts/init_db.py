# python
import os
import asyncio
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    JSON,
    Boolean,
    func,
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://sentineliq:sentineliq@localhost:5432/sentineliq")

Base = declarative_base()


class CVE(Base):
    __tablename__ = "cves"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cve_id = Column(String(64), unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    severity = Column(String(32), nullable=True)
    cvss_score = Column(Float, nullable=True)
    published_date = Column(DateTime(timezone=True), nullable=True)
    affected_products = Column(JSON, nullable=True)
    raw = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(128), nullable=False)
    event_time = Column(DateTime(timezone=True), nullable=True)
    severity = Column(String(32), nullable=True)
    message = Column(String, nullable=True)
    metadata = Column(JSON, nullable=True)
    correlated_cves = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


async def init_db() -> None:
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_db())