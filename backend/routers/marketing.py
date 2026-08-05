# routers/marketing.py
from fastapi import APIRouter
from pydantic import BaseModel
# from database import get_oracle_langchain_db_uri # 👈 คอมเมนต์ไว้ก่อน
# from langchain_community.utilities import SQLDatabase

router = APIRouter(prefix="/api/marketing-chat", tags=["Marketing Data"])

class ToolRequest(BaseModel):
    question: str 

@router.post("")
async def ask_marketing_data(request: ToolRequest):
    # ปิดการเชื่อมต่อ DB ไปก่อน แล้วทำเป็น Mock ตอบกลับแทน
    # oracle_db = SQLDatabase.from_uri(get_oracle_langchain_db_uri()) 
    
    return {"reply": f"Database is temporarily closed (you asked: {request.question})"}