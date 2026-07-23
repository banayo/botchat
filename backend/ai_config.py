import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()


llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    openai_api_base=os.getenv("OPENAI_API_BASE_URL", "https://openrouter.ai/api/v1"),
    # เผื่ออนาคตเปลี่ยนเป็น Qwen2.5 ก็แค่ไปแก้ในไฟล์ .env ที่เดียวครับ
    model_name=os.getenv("LLM_MODEL_NAME", "openai/gpt-4o-mini"), 
    temperature=0
)