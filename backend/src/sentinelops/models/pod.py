from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sentinelops.core.database import Base


class Pod(Base):
    __tablename__ = "pods"
    __table_args__ = {'extend_existing': True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    cluster_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("clusters.id"))
    namespace: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(253), nullable=False, index=True)
    node_name: Mapped[str | None] = mapped_column(String(253))
    phase: Mapped[str] = mapped_column(String(32), default="Unknown")
    owner_kind: Mapped[str | None] = mapped_column(String(64))
    owner_name: Mapped[str | None] = mapped_column(String(253))
    labels_json: Mapped[str | None] = mapped_column(Text)
    restart_count: Mapped[int] = mapped_column(Integer, default=0)
    cpu_limit_millicores: Mapped[int | None] = mapped_column(Integer)
    memory_limit_bytes: Mapped[int | None] = mapped_column(Integer)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    cluster: Mapped["Cluster"] = relationship("Cluster", back_populates="pods")  # noqa: F821
    metrics: Mapped[list["PodMetric"]] = relationship("PodMetric", back_populates="pod")


class PodMetric(Base):
    __tablename__ = "pod_metrics"
    __table_args__ = {'extend_existing': True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    pod_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("pods.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    cpu_usage_millicores: Mapped[float | None] = mapped_column(Float)
    memory_usage_bytes: Mapped[float | None] = mapped_column(Float)
    cpu_percent: Mapped[float | None] = mapped_column(Float)
    memory_percent: Mapped[float | None] = mapped_column(Float)
    network_rx_bytes: Mapped[float | None] = mapped_column(Float)
    network_tx_bytes: Mapped[float | None] = mapped_column(Float)
    disk_usage_bytes: Mapped[float | None] = mapped_column(Float)

    pod: Mapped["Pod"] = relationship("Pod", back_populates="metrics")
