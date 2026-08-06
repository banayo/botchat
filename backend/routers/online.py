from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from database import get_sales_langchain_db_uri
from routers.prompts import ONLINE_PROMPT
from ai_config import llm
from sso import verify_sso_token

router = APIRouter(prefix="/api/online-chat", tags=["Online Data"])


class ChatRequest(BaseModel):
    question: str


@router.post("")
async def ask_online_data(
    request: ChatRequest,
    user_data: dict = Depends(verify_sso_token),
):
    print("\n" + "="*40)
    print(f"📥 มีข้อมูลส่งเข้ามาถึง FastAPI แล้ว!!")
    print(f"💬 คำถามที่รับมา: {request.question}")
    print(f"👤 คนถามคือ (จาก Token): {user_data.get('email', user_data.get('preferred_username', 'Unknown'))}")
    print("="*40 + "\n")
    try:
        postgres_db = SQLDatabase.from_uri(get_sales_langchain_db_uri())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}",
        )

    try:
        final_prompt = f"{ONLINE_PROMPT}\n\nคำถามจากผู้ใช้: {request.question}"

        agent_executor = create_sql_agent(
            llm=llm,
            db=postgres_db,
            agent_type="openai-tools",
            verbose=True,
        )

        response = agent_executor.invoke({"input": final_prompt})
        return {"reply": response["output"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
