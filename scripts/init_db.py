# python
import os
import asyncio
from typing import Any

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    JSON,
    func,
    select,
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://sentineliq:sentineliq@localhost:5432/sentineliq")

Base = declarative_base()


class CVERecord(Base):
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


class AlertRecord(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(128), nullable=False)
    event_time = Column(DateTime(timezone=True), nullable=True)
    severity = Column(String(32), nullable=True)
    message = Column(String, nullable=True)
    payload = Column(JSON, nullable=True)
    correlated_cves = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


async def init_db() -> None:
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


async def save_cves(records: list[dict[str, Any]]) -> int:
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        for record in records:
            result = await session.execute(select(CVERecord).where(CVERecord.cve_id == record["id"]))
            db_record = result.scalar_one_or_none()
            if db_record is None:
                db_record = CVERecord(
                    cve_id=record["id"],
                    description=record.get("description"),
                    severity=record.get("severity"),
                    cvss_score=record.get("cvss_score"),
                    published_date=record.get("published"),
                    affected_products=record.get("affected_products"),
                    raw=record,
                )
                session.add(db_record)
            else:
                db_record.description = record.get("description")
                db_record.severity = record.get("severity")
                db_record.cvss_score = record.get("cvss_score")
                db_record.published_date = record.get("published")
                db_record.affected_products = record.get("affected_products")
                db_record.raw = record
        await session.commit()
    await engine.dispose()
    return len(records)


async def save_alerts(alerts: list[dict[str, Any]]) -> int:
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        for alert in alerts:
            session.add(
                AlertRecord(
                    source=alert.get("source", "unknown"),
                    event_time=alert.get("event_time"),
                    severity=alert.get("severity"),
                    message=alert.get("message"),
                    payload=alert.get("metadata"),
                    correlated_cves=alert.get("correlated_cves"),
                )
            )
        await session.commit()
    await engine.dispose()
    return len(alerts)


async def get_recent_alerts(limit: int = 50) -> list[dict[str, Any]]:
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    out: list[dict[str, Any]] = []
    async with async_session() as session:
        result = await session.execute(select(AlertRecord).order_by(AlertRecord.created_at.desc()).limit(limit))
        rows = result.scalars().all()
        for r in rows:
            out.append({
                "id": r.id,
                "source": r.source,
                "event_time": r.event_time.isoformat() if r.event_time else None,
                "severity": r.severity,
                "message": r.message,
                "metadata": r.payload,
                "correlated_cves": r.correlated_cves or [],
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })
    await engine.dispose()
    return out


async def get_recent_cves(limit: int = 50) -> list[dict[str, Any]]:
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    out: list[dict[str, Any]] = []
    async with async_session() as session:
        result = await session.execute(select(CVERecord).order_by(CVERecord.published_date.desc()).limit(limit))
        rows = result.scalars().all()
        for r in rows:
            out.append({
                "id": r.cve_id,
                "description": r.description,
                "severity": r.severity,
                "cvss_score": r.cvss_score,
                "published_date": r.published_date.isoformat() if r.published_date else None,
                "affected_products": r.affected_products or [],
            })
    await engine.dispose()
    return out


if __name__ == "__main__":
    asyncio.run(init_db())