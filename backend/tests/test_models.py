from datetime import date

import pytest
from pydantic import ValidationError

from export.models import ExportReportRequest


def test_invalid_date_range_is_rejected():
    with pytest.raises(ValidationError):
        ExportReportRequest(
            dimensions=["month"],
            metric="sales",
            aggregation="sum",
            date_from=date(2024, 12, 31),
            date_to=date(2024, 1, 1),
        )


def test_too_many_dimensions_is_rejected():
    with pytest.raises(ValidationError):
        ExportReportRequest(
            dimensions=["month", "country", "month"],
            metric="sales",
            aggregation="sum",
            date_from=date(2024, 1, 1),
            date_to=date(2024, 2, 1),
        )
