from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from retail_intelligence.infrastructure.db.base import Base


class ZoneModel(Base):
    __tablename__ = "zones"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    zone_type: Mapped[str] = mapped_column(String(64), nullable=False)
