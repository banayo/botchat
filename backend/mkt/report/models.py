from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

DimensionKey = Literal["month", "channel"]
MetricKey = Literal["sales", "quantity"]
AggregationKey = Literal["sum", "average"]
YoyMode = Literal["mtd_yoy", "full_month_yoy"]


class MktReportRequest(BaseModel):
    dimensions: list[DimensionKey] = Field(default_factory=list)
    metric: MetricKey
    aggregation: AggregationKey
    date_from: date
    date_to: date
    channel: str | None = Field(default=None, max_length=100)
    limit: int = Field(default=500, ge=1, le=2000)

    @model_validator(mode="after")
    def validate_report(self):
        if len(self.dimensions) > 3:
            raise ValueError("maximum three dimensions")
        if len(set(self.dimensions)) != len(self.dimensions):
            raise ValueError("duplicate dimensions are not allowed")
        # date_to is inclusive; query builder uses < date_to + 1 day
        if self.date_to < self.date_from:
            raise ValueError("date_to must be on or after date_from")
        if (self.date_to - self.date_from).days > 366 * 3:
            raise ValueError("date range cannot exceed three years")
        return self


class MktYoyRequest(BaseModel):
    """Compare current period vs same period last year (executive YoY)."""

    dimensions: list[DimensionKey] = Field(default_factory=list)
    metric: MetricKey = "sales"
    aggregation: AggregationKey = "sum"
    mode: YoyMode = "mtd_yoy"
    as_of: date | None = None
    channel: str | None = Field(default=None, max_length=100)
    limit: int = Field(default=500, ge=1, le=2000)

    @model_validator(mode="after")
    def validate_yoy(self):
        if len(self.dimensions) > 3:
            raise ValueError("maximum three dimensions")
        if len(set(self.dimensions)) != len(self.dimensions):
            raise ValueError("duplicate dimensions are not allowed")
        if "month" in self.dimensions:
            raise ValueError("month dimension is not valid for YoY compare; use channel or none")
        return self
