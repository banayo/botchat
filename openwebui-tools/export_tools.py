"""
Open WebUI Tools for export data.

ask_export_data: exploratory LangChain path.
show_export_pivot: controlled report + Rich UI iframe (HTMLResponse).
Turn on ENABLE_PIVOT after /api/export-report is verified.
"""

from __future__ import annotations

import html
import json
import os
from typing import Any, Optional

import requests
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

HEIGHT_SCRIPT = """
<script>
  function reportHeight() {
    const h = document.documentElement.scrollHeight;
    parent.postMessage({ type: 'iframe:height', height: h }, '*');
  }
  window.addEventListener('load', reportHeight);
  new ResizeObserver(reportHeight).observe(document.body);
</script>
"""


def _escape(value: Any) -> str:
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def _format_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:,.2f}"
    if isinstance(value, int) and not isinstance(value, bool):
        return f"{value:,}"
    return str(value)


def _summary_cards(summary: dict[str, Any]) -> str:
    items = [
        ("Total", summary.get("total")),
        ("Rows", summary.get("row_count")),
        ("Periods", summary.get("periods")),
        ("Countries", summary.get("countries")),
        ("Top country", summary.get("highest_country")),
        ("Metric", summary.get("metric")),
        ("Aggregation", summary.get("aggregation")),
    ]
    cards = []
    for label, value in items:
        if value is None:
            continue
        cards.append(
            f'<div class="stat"><div class="stat-label">{_escape(label)}</div>'
            f'<div class="stat-value">{_escape(_format_cell(value))}</div></div>'
        )
    return "".join(cards)


def _rows_table(columns: list[str], rows: list[dict[str, Any]]) -> str:
    if not columns:
        return "<p>No columns returned.</p>"
    headers = "".join(
        f'<th data-col="{_escape(col)}" onclick="sortTable(this)">{_escape(col)}</th>'
        for col in columns
    )
    body_rows = []
    for row in rows:
        cells = []
        for col in columns:
            raw = row.get(col)
            cells.append(
                f'<td data-sort="{_escape(raw)}">{_escape(_format_cell(raw))}</td>'
            )
        body_rows.append("<tr>" + "".join(cells) + "</tr>")
    tbody = "".join(body_rows) or '<tr><td colspan="99">No rows.</td></tr>'
    return (
        f'<table id="pivot"><thead><tr>{headers}</tr></thead>'
        f"<tbody>{tbody}</tbody></table>"
    )


def build_pivot_html(body: dict[str, Any]) -> str:
    columns = body.get("columns") or []
    rows = body.get("rows") or []
    summary = body.get("summary") or {}
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Export pivot</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: system-ui, sans-serif;
      padding: 12px;
      color: #1a1a1a;
      background: #f6f7f9;
    }}
    .stats {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }}
    .stat {{
      background: #fff;
      border: 1px solid #e3e6eb;
      border-radius: 10px;
      padding: 8px 12px;
      min-width: 110px;
    }}
    .stat-label {{ font-size: 11px; color: #667; text-transform: uppercase; }}
    .stat-value {{ font-size: 16px; font-weight: 650; margin-top: 2px; }}
    .note {{ font-size: 12px; color: #556; margin-bottom: 8px; }}
    .wrap {{ overflow: auto; background: #fff; border-radius: 10px; border: 1px solid #e3e6eb; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
    th, td {{ padding: 8px 10px; border-bottom: 1px solid #eee; text-align: left; white-space: nowrap; }}
    th {{ cursor: pointer; background: #f0f2f5; position: sticky; top: 0; }}
    th:hover {{ background: #e4e8ee; }}
  </style>
</head>
<body>
  <div class="stats">{_summary_cards(summary)}</div>
  <p class="note">Values were calculated on the server. Click a column header to sort this approved dataset only.</p>
  <div class="wrap">{_rows_table(columns, rows)}</div>
  <script>
    let sortDir = 1;
    let lastCol = -1;
    function sortTable(th) {{
      const table = document.getElementById('pivot');
      const idx = Array.from(th.parentNode.children).indexOf(th);
      if (idx === lastCol) {{ sortDir *= -1; }} else {{ sortDir = 1; lastCol = idx; }}
      const tbody = table.tBodies[0];
      const rows = Array.from(tbody.rows);
      rows.sort((a, b) => {{
        const av = a.cells[idx].getAttribute('data-sort') || '';
        const bv = b.cells[idx].getAttribute('data-sort') || '';
        const an = Number(av.replace(/,/g, ''));
        const bn = Number(bv.replace(/,/g, ''));
        if (!Number.isNaN(an) && !Number.isNaN(bn) && av !== '' && bv !== '') {{
          return (an - bn) * sortDir;
        }}
        return av.localeCompare(bv) * sortDir;
      }});
      rows.forEach((row) => tbody.appendChild(row));
      reportHeight();
    }}
  </script>
  {HEIGHT_SCRIPT}
</body>
</html>
"""


class Tools:
    class Valves(BaseModel):
        API_BASE_URL: str = Field(
            default=os.getenv("EXPORT_API_BASE_URL", "http://assistant_api:8000")
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

    def ask_export_data(
        self,
        question: str,
        __oauth_token__: Optional[dict] = None,
    ) -> str:
        """
        Use for detailed or exploratory export-data questions that cannot be
        represented by show_export_pivot. Input is a natural-language question.
        """
        if not isinstance(__oauth_token__, dict) or not __oauth_token__.get("access_token"):
            return json.dumps(
                {
                    "error": "No Authentik access_token from Open WebUI. Sign in with OAuth and pass __oauth_token__."
                },
                ensure_ascii=False,
            )

        response = requests.post(
            f"{self.valves.API_BASE_URL.rstrip('/')}/api/export-chat",
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
                    "error": f"{response.status_code} from /api/export-chat",
                    "fastapi_detail": payload.get("detail", payload),
                },
                ensure_ascii=False,
            )
        return json.dumps(payload, ensure_ascii=False)

    def show_export_pivot(
        self,
        dimensions: list[str],
        metric: str,
        aggregation: str,
        date_from: str,
        date_to: str,
        country: Optional[str] = None,
        limit: int = 500,
        __oauth_token__: Optional[dict] = None,
    ):
        """
        Use for aggregated reports, comparisons, totals, trends and pivot tables.
        Renders a table in chat (Rich UI). The model only receives a compact summary.

        Use for aggregated reports...
    
        Valid dimensions: "month", "country" (max 3, no duplicates)
        Valid metrics: "sales", "quantity"
        Valid aggregations: "sum", "average"
        
        Example:
            show_export_pivot(
                dimensions=["month", "country"],
                metric="sales",
                aggregation="sum",
                date_from="2025-01-01",
                date_to="2025-06-30"
            )
        """
        if not self.valves.ENABLE_PIVOT:
            return json.dumps(
                {
                    "error": "show_export_pivot is disabled until ENABLE_PIVOT is true. Use ask_export_data."
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
        if country:
            payload["country"] = country

        response = requests.post(
            f"{self.valves.API_BASE_URL.rstrip('/')}/api/export-report",
            headers=self._headers(__oauth_token__),
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        body = response.json()
        page = build_pivot_html(body)
        embed = HTMLResponse(
            content=page,
            headers={"Content-Disposition": "inline"},
        )
        return embed, body.get("summary") or {
            "row_count": body.get("row_count"),
            "columns": body.get("columns"),
        }
