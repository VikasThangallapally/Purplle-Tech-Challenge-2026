from retail_intelligence.schemas.common import APIModel


class StoreResponse(APIModel):
    id: int
    name: str
    location: str | None = None
