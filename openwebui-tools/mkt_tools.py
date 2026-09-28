"""
Open WebUI Tools for marketing data.

ask_mkt_data: exploratory LangChain path → POST /api/mkt-chat
show_mkt_pivot: controlled report → POST /api/mkt-report
show_mkt_yoy: MTD / full-month vs same period last year → POST /api/mkt-report/yoy
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
            default=os.getenv("MKT_API_BASE_URL", "http://assistant_api:8000")
        )
        ENABLE_PIVOT: bool = Field(default=True)

    def __init__(self):
        self.valves = self.Valves()

    def _headers(self, oauth_token: dict | None = None) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        token = ""
        if isinstance(oauth_token, dict):
            token = str(oauth_token.get("access_token") or "")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _post_json(
        self,
        path: str,
        payload: dict,
        oauth_token: dict | None,
    ) -> str:
        if not isinstance(oauth_token, dict) or not oauth_token.get("access_token"):
            return json.dumps(
                {
                    "error": "No Authentik access_token from Open WebUI. Sign in with OAuth and pass __oauth_token__."
                },
                ensure_ascii=False,
            )

        response = requests.post(
            f"{self.valves.API_BASE_URL.rstrip('/')}{path}",
            headers=self._headers(oauth_token),
            json=payload,
            timeout=120,
        )
        try:
            body = response.json()
        except ValueError:
            body = {"detail": response.text[:2000]}
        if not response.ok:
            return json.dumps(
                {
                    "error": f"{response.status_code} from {path}",
                    "fastapi_detail": body.get("detail", body),
                },
                ensure_ascii=False,
            )
        return json.dumps(body, ensure_ascii=False)

    def ask_mkt_data(
        self,
        question: str,
        __oauth_token__: Optional[dict] = None,
    ) -> str:
        """
        Use for marketing-data questions in natural language.
        Do not use this for export sales; use ask_export_data instead.
        """
        return self._post_json(
            "/api/mkt-chat",
            {"question": question},
            __oauth_token__,
        )

    def show_mkt_pivot(
        self,
        dimensions: list[str],
        metric: str,
        aggregation: str,
        date_from: str,
        date_to: str,
        channel: Optional[str] = None,
        dept: Optional[str] = None,
        limit: int = 500,
        __oauth_token__: Optional[dict] = None,
    ) -> str:
        """
        Aggregated marketing reports (controlled SQL).

        Valid dimensions: "month", "channel" (SHOP_TYPE), "dept" (CUST_CHANNEL / แผนกขาย);
        empty list = grand total only
        Valid metrics: "sales", "quantity"
        Valid aggregations: "sum", "average"
        date_from / date_to are inclusive (YYYY-MM-DD).
        """
        if not self.valves.ENABLE_PIVOT:
            return json.dumps(
                {
                    "error": "show_mkt_pivot is disabled until registry columns are filled. Use ask_mkt_data."
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
        if channel:
            payload["channel"] = channel
        if dept:
            payload["dept"] = dept

        return self._post_json("/api/mkt-report", payload, __oauth_token__)

    def show_mkt_yoy(
        self,
        mode: str = "mtd_yoy",
        dimensions: Optional[list[str]] = None,
        metric: str = "sales",
        aggregation: str = "sum",
        as_of: Optional[str] = None,
        channel: Optional[str] = None,
        dept: Optional[str] = None,
        limit: int = 500,
        __oauth_token__: Optional[dict] = None,
    ) -> str:
        """
        Compare marketing sales/quantity to the same period last year.

        mode:
          - "mtd_yoy": month-to-date this year vs same days last year
          - "full_month_yoy": full calendar month vs same month last year

        Valid dimensions: "channel" (SHOP_TYPE), "dept" (CUST_CHANNEL / แผนกขาย),
        or empty for company total only. Do not pass "month".
        Prefer this over ask_mkt_data for executive YoY.
        """
        if not self.valves.ENABLE_PIVOT:
            return json.dumps(
                {
                    "error": "show_mkt_yoy is disabled until registry columns are filled. Use ask_mkt_data."
                }
            )

        payload: dict = {
            "dimensions": dimensions or [],
            "metric": metric,
            "aggregation": aggregation,
            "mode": mode,
            "limit": limit,
        }
        if as_of:
            payload["as_of"] = as_of
        if channel:
            payload["channel"] = channel
        if dept:
            payload["dept"] = dept

        return self._post_json("/api/mkt-report/yoy", payload, __oauth_token__)
