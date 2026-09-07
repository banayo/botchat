from typing import Any

from mkt import QUALIFIED_VIEW

# Fill this after running sql/collect_mkt_view.sql.
# Do not guess column names. Controlled reports stay off until this is True.
REGISTRY_READY = False

MKT_FIELDS: dict[str, dict[str, Any]] = {}

MKT_DIMENSIONS: dict[str, dict[str, str]] = {}

MKT_METRICS: dict[str, dict[str, Any]] = {}

DATE_FILTER_COLUMN = ""
FROM_CLAUSE = QUALIFIED_VIEW
