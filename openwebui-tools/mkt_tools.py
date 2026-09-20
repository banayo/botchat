"""
Open WebUI Tools for marketing data.

ask_mkt_data: exploratory LangChain path → POST /api/mkt-chat
show_mkt_pivot: controlled report (off until registry is filled)
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
        ENABLE_PIVOT: bool = Field(default=False)

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

    def ask_mkt_data(
        self,
        question: str,
        __oauth_token__: Optional[dict] = None,
    ) -> str:
        """
        Use for marketing-data questions in natural language.
        Do not use this for export sales; use ask_export_data instead.
        """
        if not isinstance(__oauth_token__, dict) or not __oauth_token__.get("access_token"):
            return json.dumps(
                {
                    "error": "No Authentik access_token from Open WebUI. Sign in with OAuth and pass __oauth_token__."
                },
                ensure_ascii=False,
            )

        response = requests.post(
            f"{self.valves.API_BASE_URL.rstrip('/')}/api/mkt-chat",
            headers=self._headers(__oauth_token__),
            json={"question": question},
            timeout=120,
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {"detail": response.text[:2000]}
        if not response.ok:
            return json.dumps(
                {
                    "error": f"{response.status_code} from /api/mkt-chat",
                    "fastapi_detail": payload.get("detail", payload),
                },
                ensure_ascii=False,
            )
        return json.dumps(payload, ensure_ascii=False)

    def show_mkt_pivot(
        self,
        dimensions: list[str],
        metric: str,
        aggregation: str,
        date_from: str,
        date_to: str,
        zone: Optional[str] = None,
        limit: int = 500,
        __oauth_token__: Optional[dict] = None,
    ) -> str:
        """
        Aggregated marketing reports. Disabled until MKT registry columns are filled.

        Valid dimensions: "month", "zone"
        Valid metrics: "sales", "quantity"
        Valid aggregations: "sum", "average"
        """
        if not self.valves.ENABLE_PIVOT:
            return json.dumps(
                {
                    "error": "show_mkt_pivot is disabled until registry columns are filled. Use ask_mkt_data."
                }
            )

        if not isinstance(__oauth_token__, dict) or not __oauth_token__.get("access_token"):
            return json.dumps(
                {
                    "error": "No Authentik access_token from Open WebUI. Sign in with OAuth and pass __oauth_token__."
                },
                ensure_ascii=False,
            )

        payload = {
            "dimensions": dimensions,
            "metric": metric,
            "aggregation": aggregation,
            "date_from": date_from,
            "date_to": date_to,
            "limit": limit,
        }
        if zone:
            payload["zone"] = zone

        response = requests.post(
            f"{self.valves.API_BASE_URL.rstrip('/')}/api/mkt-report",
            headers=self._headers(__oauth_token__),
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
                    "error": f"{response.status_code} from /api/mkt-report",
                    "fastapi_detail": body.get("detail", body),
                },
                ensure_ascii=False,
            )
        return json.dumps(body.get("summary") or body, ensure_ascii=False)
