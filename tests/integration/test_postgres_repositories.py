import pytest

pytest.importorskip("sqlalchemy")

from retail_intelligence.infrastructure.db.base import Base


def test_base_metadata_exists() -> None:
    assert Base.metadata is not None
