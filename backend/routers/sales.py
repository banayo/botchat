from fastapi import APIRouter, HTTPException
from database import get_sales_db_connection
from psycopg2.extras import RealDictCursor

# ตั้งค่า Prefix ให้ API ในไฟล์นี้ขึ้นต้นด้วย /api/sales เสมอ
router = APIRouter(prefix="/api/sales", tags=["Sales"])

@router.get("/daily")
async def check_daily_sales():
    conn = get_sales_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="ต่อ DB ยอดขายไม่ได้")
        
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT SUM(total_amount) as revenue FROM orders WHERE DATE(order_date) = CURRENT_DATE")
        result = cur.fetchone()
        return {"revenue": result['revenue']}
    finally:
        conn.close()