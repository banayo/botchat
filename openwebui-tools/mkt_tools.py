"""
Open WebUI Tools for marketing data.

ask_mkt_data: sales questions → POST /api/mkt-chat
ask_mkt_return: product-return questions → POST /api/mkt-return-chat
show_mkt_pivot: controlled report → POST /api/mkt-report
show_mkt_yoy: MTD / full-month vs same period last year → POST /api/mkt-report/yoy
"""

from __future__ import annotations

import asyncio
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

    async def _post_json(
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

        # Open WebUI runs a sync tool directly on its event loop, which freezes
        # every user's websocket until the API answers (the agent often takes
        # 40-60s, past socket.io's 45s ping window). Run the blocking call in a
        # thread so the loop stays free.
        response = await asyncio.to_thread(
            requests.post,
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

    async def ask_mkt_data(
        self,
        question: str,
        __oauth_token__: Optional[dict] = None,
    ) -> str:
        """
        Use for free-form marketing sales questions only.
        Do not use this for product returns; use ask_mkt_return.
        Do not use this for export sales; use ask_export_data instead.
        """
        return await self._post_json(
            "/api/mkt-chat",
            {"question": question},
            __oauth_token__,
        )

    async def ask_mkt_return(
        self,
        question: str,
        __oauth_token__: Optional[dict] = None,
    ) -> str:
        """
        Use for free-form product-return questions only.
        Do not use this for sales totals; use ask_mkt_data or show_mkt_yoy.
        If the user asks for both sales and returns, call each tool separately.
        """
        return await self._post_json(
            "/api/mkt-return-chat",
            {"question": question},
            __oauth_token__,
        )

    async def show_mkt_pivot(
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

        dimensions = how to break the result down (group by):
          "month", "channel" (ช่องทางร้าน), "dept" (แผนกขาย),
          "module" (ประเภทเอกสาร IV/RT/CN/DN จากรหัส MODULE); empty list = grand total only
        channel / dept = optional filters to ONE value; leave empty to include all.
          They are values, never column names - do not pass "SHOP_TYPE" or "CUST_CHANNEL".
          e.g. sales per channel  -> dimensions=["channel"], channel empty
               ONLINE sales only  -> dimensions=[], channel="ONLINE"
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

        return await self._post_json("/api/mkt-report", payload, __oauth_token__)

    async def show_mkt_yoy(
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

        dimensions = how to break the result down: "channel" (ช่องทางร้าน), "dept" (แผนกขาย),
        "module" (ประเภทเอกสาร), or empty for company total only. Do not pass "month".
        channel / dept = optional filters to ONE value, e.g. channel="ONLINE";
        leave empty to include all. Never pass "SHOP_TYPE" or "CUST_CHANNEL" as a value.
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

        return await self._post_json("/api/mkt-report/yoy", payload, __oauth_token__)
