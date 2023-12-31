from pydantic import BaseModel, Field

from ...enums import Order


class DashboardPagination(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=10, ge=1, le=100)
    page_count: int | None


class DashboardSort(BaseModel):
    order: Order = Order.ASC
    field: str = "id"

    class Config:
        use_enum_values = True


class DashboardFilter(BaseModel):
    field: str
    value: str


class DashboardMeta(BaseModel):
    pagination: DashboardPagination = DashboardPagination()
    sort: DashboardSort = DashboardSort()
    filter: list[DashboardFilter] = []
