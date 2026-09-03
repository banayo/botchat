"""
Open WebUI Tools for export data.

Enable ask_export_data first. Turn on ENABLE_PIVOT only after controlled
registry tests are complete.
"""

from __future__ import annotations

import json
import os
from typing import Optional

import requests
from pydantic import BaseModel, Field


class Tools:
    class Valves(BaseModel):
        API_BASE_URL: str = Field(
            default=os.getenv("EXPORT_API_BASE_URL", "http://assistant_api:8000")
        )
        ENABLE_PIVOT: bool = Field(default=False)

    def __init__(self):
        self.valves = self.Valves()

    def _headers(self, user: dict | None) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        token = ""
        if user:
            token = str(user.get("token") or user.get("access_token") or "")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def ask_export_data(
        self,
        question: str,
        __user__: Optional[dict] = None,
    ) -> str:
        """
        Use for detailed or exploratory export-data questions that cannot be
        represented by show_export_pivot. Input is a natural-language question.
        """
        response = requests.post(
            f"{self.valves.API_BASE_URL.rstrip('/')}/api/export-chat",
            headers=self._headers(__user__),
            json={"question": question},
            timeout=120,
        )
        response.raise_for_status()
        return json.dumps(response.json(), ensure_ascii=False)

    def show_export_pivot(
        self,
        dimensions: list[str],
        metric: str,
        aggregation: str,
        date_from: str,
        date_to: str,
        country: Optional[str] = None,
        limit: int = 500,
        __user__: Optional[dict] = None,
    ) -> str:
        """
        Use for aggregated reports, comparisons, totals, trends and pivot tables.
        Disabled until ENABLE_PIVOT is true.
        """
        if not self.valves.ENABLE_PIVOT:
            return json.dumps(
                {
                    "error": "show_export_pivot is disabled until the controlled registry is verified. Use ask_export_data."
                }
            )

        payload = {
            "dimensions": dimensions,
            "metric": metric,
            "aggregation": aggregation,
            "date_from": date_from,
            "date_to": date_to,
            "limit": limit,
        }
        if country:
            payload["country"] = country

        response = requests.post(
            f"{self.valves.API_BASE_URL.rstrip('/')}/api/export-report",
            headers=self._headers(__user__),
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        body = response.json()
        compact = {
            "kind": body.get("kind"),
            "summary": body.get("summary"),
            "row_count": body.get("row_count"),
            "columns": body.get("columns"),
        }
        return json.dumps(compact, ensure_ascii=False)
