import asyncio
import logging
import time
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from export.audit import hash_text, identity_sub, log_export_event
from export.authz import require_export_access
from export.chat.agent import invoke_export_agent
from export.chat.models import ExportQuestion
from export.report.models import ExportReportRequest
from export.report.service import execute_export_report

logger = logging.getLogger("uvicorn.error")

router = APIRouter(tags=["Export Data"])


@router.post("/api/export-chat")
async def ask_export_data(#  คำถามอิสระ สำหรับการสอบถามข้อมูลจากฐานข้อมูล → LangChain Agent → SQL guard → Oracle
    request: ExportQuestion,
    identity: dict[str, Any] = Depends(require_export_access),
):
    started = time.perf_counter()
    success = False
    reply = ""
    try:
        response = await asyncio.to_thread(invoke_export_agent, request.question)
        reply = response.get("output", "")
        success = True
        return {"kind": "answer", "reply": reply}
    except Exception as exc:
        logger.exception("export-chat failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        log_export_event(
            user_sub=identity_sub(identity),
            tool="ask_export_data",
            question_hash=hash_text(request.question),
            execution_path="langchain",
            llm_duration_ms=int((time.perf_counter() - started) * 1000),
            success=success,
        )


@router.post("/api/export-report")
async def create_export_report(#Pydantic → registry → SQL builder → Oracle # สร้างรายงานข้อมูลจากฐานข้อมูล
    request: ExportReportRequest,
    identity: dict[str, Any] = Depends(require_export_access),
):
    started = time.perf_counter()
    success = False
    sql = ""
    row_count = 0
    try:
        result = await asyncio.to_thread(execute_export_report, request)
        sql = result.pop("sql")
        row_count = result["row_count"]
        success = True
        return {
            "kind": "pivot",
            "dimensions": request.dimensions,
            "metric": request.metric,
            "aggregation": request.aggregation,
            "columns": result["columns"],
            "rows": result["rows"],
            "row_count": row_count,
            "summary": result["summary"],
        }
    except ValueError as exc:
        logger.warning("export-report rejected: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("export-report failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        log_export_event(
            user_sub=identity_sub(identity),
            tool="show_export_pivot",
            metric=request.metric,
            dimensions=list(request.dimensions),
            execution_path="controlled",
            generated_sql_hash=hash_text(sql) if sql else None,
            sql_duration_ms=int((time.perf_counter() - started) * 1000),
            returned_rows=row_count,
            success=success,
        )
