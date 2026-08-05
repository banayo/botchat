from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from langchain_community.agent_toolkits import create_sql_agent
from database import get_sales_langchain_db_uri
from routers.prompts import ONLINE_PROMPT
from langchain_community.utilities import SQLDatabase
from ai_config import llm
from sso import verify_sso_token

router = APIRouter(prefix="/api/online-chat", tags=["Online Data"])

class ChatRequest(BaseModel):
    question: str

@router.post("/")
async def ask_online_data(request: ChatRequest,user_data: dict = Depends(verify_sso_token)):

    # เช็คว่า Database เชื่อมต่อสำเร็จไหม
    if postgres_db is None:
        raise HTTPException(status_code=500, detail="Database connection failed.")    
    try:
        final_prompt = f"{ONLINE_PROMPT}\n\nคำถามจากผู้ใช้: {request.question}"
        
        # Agent นี้จะเก่งเรื่องการหา vw_net_sales
        agent_executor = create_sql_agent(
            llm=llm, 
            db=postgres_db, 
            agent_type="openai-tools",
            verbose=True# เปิด True ไว้ตอน Develop จะได้เห็นว่ามันเขียน SQl
        )
        
        response = agent_executor.invoke({"input": final_prompt})
        return {"answer": response["output"]}
    except Exception as e:
        # ดักจับ Error เผื่อ AI สับสน หรือ Database ช้า
        raise HTTPException(status_code=500, detail=str(e))