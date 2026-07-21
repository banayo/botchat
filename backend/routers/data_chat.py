from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI
from database import get_sales_langchain_db_uri,get_oracle_langchain_db_uri
from langchain.tools import tool

router = APIRouter(prefix="/api/data-chat", tags=["LangChain SQL Agent"])# 

class ChatRequest(BaseModel):
    question: str
    department: str # แผนนก ส่งมา wui

@router.post("/")
async def process_agent_query(request: ChatRequest):
 try:
        active_db = None
        allowed_tools = []
        system_prompt = ""  # 🌟 เตรียมตัวแปรเก็บ Prompt

        # ระบบสับสวิตช์: เลือก DB, เลือก Tool, และเลือก Prompt!
        if request.department == "marketing":
            active_db = oracle_db
            system_prompt = MARKETING_PROMPT
            
        elif request.department == "online":
            active_db = db 
            allowed_tools = [ask_oracle_database]
            system_prompt = ONLINE_PROMPT
            
        elif request.department == "admin":
            active_db = db
            allowed_tools = [ask_oracle_database]
            system_prompt = ADMIN_PROMPT
            
        else:
            raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์เข้าถึง")










# #เรียกใช้ URI จากไฟล์ database.py และโหลดขึ้น Memory ครั้งเดียว
# db = SQLDatabase.from_uri(get_sales_langchain_db_uri())

# llm = ChatOpenAI(
#     openai_api_key=os.getenv("OPENAI_API_KEY"),
#     openai_api_base=os.getenv("OPENAI_API_BASE_URL", "https://openrouter.ai/api/v1"),
#     model_name="openai/gpt-4o-mini",
#     temperature=0
# )
# CUSTOM_PROMPT = """คุณคือผู้ช่วยวิเคราะห์ข้อมูลระดับองค์กร (Enterprise Data Analyst) 
# คุณมีเครื่องมือทั้งการเขียน SQL และการดึงข้อมูลจาก API

# กฎการทำงาน (Strict Rules):
# 1. **เมื่อถูกถามเกี่ยวกับ 'ยอดขาย', 'ยอดรวม', 'บิล' หรือ 'การขาย':** ให้ดึงข้อมูลจาก View ที่ชื่อ vw_net_sales เท่านั้น!! ห้ามอ้างอิง หรือ JOIN กับตารางอื่นเด็ดขาด
# 2. ให้ทำความเข้าใจโครงสร้างของ vw_net_sales ก่อนเขียน SQL เสมอ โดยมีเงื่อนไขดังนี้:
#    - CRE_ID คือ เลขที่บิล
#    - module คือ ประเภทบิล ('POS' = บิลขายปกติ, 'RTPOS' = บิลวอยด์/คืนสินค้า)
#    - REF_INV_ID คือ เลขที่อ้างอิงบิล (ถ้า RTPOS จะอ้างถึง CRE_ID เดิมที่ถูกคืน)
#    - QTY1 คือ จำนวนสินค้าที่ขาย
#    - ITEM_AMT1 คือ ยอดเงิน/ราคา
#    - CANCEL คือ สถานะยกเลิก ('N' = ปกติ, 'Y' = ยกเลิก) **ในการรวมยอดขาย ให้คำนวณเฉพาะบิลที่ CANCEL = 'N' เสมอ**
#    - group_1 คือ กลุ่ม/หมวดหมู่สินค้า
# 3. ห้ามรันคำสั่ง DML (INSERT, UPDATE, DELETE, DROP) เด็ดขาด
# 4. หากดึงข้อมูลมาแสดงเป็นตาราง ให้จำกัดผลลัพธ์ด้วย LIMIT 10 เสมอ
# 5. สรุปผลลัพธ์และตอบกลับผู้ใช้เป็น 'ภาษาไทย' เสมอ"""

# @tool
# def check_product_stock(item_code: str) -> str:
#     """
#     ใช้เครื่องมือนี้เมื่อผู้ใช้ต้องการ 'ตรวจสอบจำนวนสต็อก', 'ของคงเหลือ' หรือ 'เช็คสินค้า'
#     โดยต้องระบุรหัสสินค้า (item_code) เสมอ
#     """
#     # ตัวอย่าง: ถ้ามี API ของระบบ WMS หรือ P-check สามารถใช้ requests.get ยิงไปหาได้เลย
#     # response = requests.get(f"http://api_wms:8000/api/stock/{item_code}")
#     # return response.text
    
#     # อันนี้ผมทำจำลองข้อมูลส่งกลับไปให้ AI คุยกับผู้ใช้ก่อน
#     return f"แจ้งเตือนจากระบบ WMS: สินค้ารหัส {item_code} ขณะนี้มีสต็อกคงเหลือพร้อมหยิบ 120 ชิ้น อยู่ที่ Zone A"
# @router.post("/")
# async def ask_database(request: ChatRequest):
#     try:
#         prompt = CUSTOM_PROMPT + "\n\n" + request.question
#         agent_executor = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True)
#         response = agent_executor.invoke({"input": prompt})
#         return {"answer": response["output"]}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))