import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# ชี้ไปที่ vLLM (OpenAI-compatible) ผ่าน .env ไม่ใช้ OpenRouter
llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENAI_API_KEY", "not-needed"),
    openai_api_base=os.getenv("OPENAI_API_BASE_URL"),
    model=os.getenv("LLM_MODEL_NAME"),
    temperature=0,
)