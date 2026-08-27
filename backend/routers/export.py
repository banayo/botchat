from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from database import get_oracle_langchain_db_uri
from routers.prompts import EXPORT_PROMPT
from ai_config import llm

router = APIRouter(prefix="/api/export-chat", tags=["Export Data"])


class ToolRequest(BaseModel):
    question: str


@router.post("")
async def ask_export_data(request: ToolRequest):
    try:
        oracle_db = SQLDatabase.from_uri(
            get_oracle_langchain_db_uri(),
            schema="KMCOM5",
            view_support=True,
            include_tables=["exp$erp_sale_rep_exp"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}",
        )

    try:
        final_prompt = f"{EXPORT_PROMPT}\n\nคำถามจากผู้ใช้: {request.question}"

        agent_executor = create_sql_agent(
            llm=llm,
            db=oracle_db,
            agent_type="tool-calling",
            verbose=True,
        )

        response = agent_executor.invoke({"input": final_prompt})
        return {"reply": response["output"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
