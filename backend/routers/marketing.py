from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI
from database import get_oracle_langchain_db_uri
from prompts import MARKETING_PROMPT
from langchain_community.utilities import SQLDatabase

router = APIRouter(prefix="/api/marketing-chat", tags=["Marketing Data"])

class ChatRequest(BaseModel):
    question: str
    department: str
# โหลดเฉพาะ Oracle ขึ้นมา
oracle_db = SQLDatabase.from_uri(get_oracle_langchain_db_uri())

llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    openai_api_base=os.getenv("OPENAI_API_BASE_URL", "https://openrouter.ai/api/v1"),
    model_name="openai/gpt-4o-mini",
    temperature=0
)

@router.post("/")
async def ask_marketing_data(request: ChatRequest):
    try:
        final_prompt = MARKETING_PROMPT + "\n\nคำถาม: " + request.question
        
        # Agent นี้จะเก่งเฉพาะเรื่อง Oracle
        agent_executor = create_sql_agent(
            llm=llm, 
            db=oracle_db, 
            agent_type="openai-tools",
            verbose=True
        )
        
        response = agent_executor.invoke({"input": final_prompt})
        return {"answer": response["output"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))