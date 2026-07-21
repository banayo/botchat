from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI
from database import get_sales_langchain_db_uri
from prompts import ONLINE_PROMPT
from langchain_community.utilities import SQLDatabase

router = APIRouter(prefix="/api/online-chat", tags=["Online Data"])

class ChatRequest(BaseModel):
    question: str
    department: str

# โหลดเฉพาะ Postgres ขึ้นมา
postgres_db = SQLDatabase.from_uri(get_sales_langchain_db_uri())

llm = ChatOpenAI(
    # ... (ตั้งค่า LLM เหมือนเดิม) ...
)

@router.post("/")
async def ask_online_data(request: ChatRequest):
    allowed_departments = ["online", "ITT"]
    if request.department not in allowed_departments:
        raise HTTPException(
            status_code=403, 
            detail=f"Access Denied: คุณอยู่แผนก '{request.department}' ไม่มีสิทธิ์เข้าถึงข้อมูลยอดขายออนไลน์"
        )
    try:
        final_prompt = ONLINE_PROMPT + "\n\nคำถาม: " + request.question
        
        # Agent นี้จะเก่งเรื่องการหา vw_net_sales
        agent_executor = create_sql_agent(
            llm=llm, 
            db=postgres_db, 
            agent_type="openai-tools",
            verbose=True
        )
        
        response = agent_executor.invoke({"input": final_prompt})
        return {"answer": response["output"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))