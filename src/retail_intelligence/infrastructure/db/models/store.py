from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from retail_intelligence.infrastructure.db.base import Base


class StoreModel(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
