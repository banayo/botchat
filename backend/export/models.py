from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

DimensionKey = Literal["month", "country"]
MetricKey = Literal["sales", "quantity"]
AggregationKey = Literal["sum", "average"]


class ExportQuestion(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class ExportReportRequest(BaseModel):
    dimensions: list[DimensionKey]
    metric: MetricKey
    aggregation: AggregationKey
    date_from: date
    date_to: date
    country: str | None = Field(default=None, max_length=100)
    limit: int = Field(default=500, ge=1, le=2000)

    @model_validator(mode="after")
    def validate_report(self):
        if not self.dimensions:
            raise ValueError("at least one dimension is required")
        if len(self.dimensions) > 3:
            raise ValueError("maximum three dimensions")
        if len(set(self.dimensions)) != len(self.dimensions):
            raise ValueError("duplicate dimensions are not allowed")
        if self.date_to <= self.date_from:
            raise ValueError("date_to must be after date_from")
        if (self.date_to - self.date_from).days > 366 * 3:
            raise ValueError("date range cannot exceed three years")
        return self
