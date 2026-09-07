import asyncio
import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from mkt.audit import hash_text, identity_sub, log_mkt_event
from mkt.authz import require_mkt_access
from mkt.chat.agent import invoke_mkt_agent
from mkt.chat.models import MktQuestion
from mkt.report.models import MktReportRequest
from mkt.report.service import execute_mkt_report

logger = logging.getLogger("uvicorn.error")

router = APIRouter(tags=["Marketing Data"])


@router.post("/api/mkt-chat")
async def ask_mkt_data(
    request: MktQuestion,
    identity: dict[str, Any] = Depends(require_mkt_access),
):
    started = time.perf_counter()
    success = False
    try:
        response = await asyncio.to_thread(invoke_mkt_agent, request.question)
        success = True
        return {"kind": "answer", "reply": response.get("output", "")}
    except Exception as exc:
        logger.exception("mkt-chat failed: %s", exc)
        raise HTTPException(status_code=500, detail="ไม่สามารถประมวลผลคำถามได้ กรุณาลองใหม่") from exc
    finally:
        log_mkt_event(
            user_sub=identity_sub(identity),
            tool="ask_mkt_data",
            question_hash=hash_text(request.question),
            execution_path="langchain",
            llm_duration_ms=int((time.perf_counter() - started) * 1000),
            success=success,
        )


@router.post("/api/mkt-report")
async def create_mkt_report(
    request: MktReportRequest,
    identity: dict[str, Any] = Depends(require_mkt_access),
):
    started = time.perf_counter()
    success = False
    sql = ""
    row_count = 0
    try:
        result = await asyncio.to_thread(execute_mkt_report, request)
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
        logger.warning("mkt-report rejected: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("mkt-report failed: %s", exc)
        raise HTTPException(status_code=500, detail="ไม่สามารถสร้างรายงานได้ กรุณาลองใหม่") from exc
    finally:
        log_mkt_event(
            user_sub=identity_sub(identity),
            tool="show_mkt_pivot",
            metric=request.metric,
            dimensions=list(request.dimensions),
            execution_path="controlled",
            generated_sql_hash=hash_text(sql) if sql else None,
            sql_duration_ms=int((time.perf_counter() - started) * 1000),
            returned_rows=row_count,
            success=success,
        )
