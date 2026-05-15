from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from sentinelops.core.database import Base


class Service(Base):
    __tablename__ = "services"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    cluster_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    namespace: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(253), nullable=False, index=True)
    service_type: Mapped[str] = mapped_column(String(32), default="ClusterIP")
    selector_json: Mapped[str | None] = mapped_column(Text)
    ports_json: Mapped[str | None] = mapped_column(Text)
    labels_json: Mapped[str | None] = mapped_column(Text)
    health_status: Mapped[str] = mapped_column(String(32), default="unknown")
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
