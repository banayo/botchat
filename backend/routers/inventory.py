from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from database import get_db_connection

# กำหนด prefix เป็น /api/inventory
router = APIRouter(prefix="/api/inventory", tags=["Inventory"])

class StockQuery(BaseModel):
    item_name: str

@router.post("/check")
async def check_specific_stock(query: StockQuery):
    """เช็คสต็อกเฉพาะสินค้า"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        sql = "SELECT item_code, item_name, qty_on_hand, reorder_point FROM stock_items WHERE item_name ILIKE %s OR item_code ILIKE %s"
        cur.execute(sql, (f'%{query.item_name}%', f'%{query.item_name}%'))
        results = cur.fetchall()
        
        if not results:
            return {"message": f"ไม่พบข้อมูลสินค้าที่ใกล้เคียงกับ: {query.item_name}"}
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("/low-stock")
async def check_low_stock():
    """เช็คสินค้าใกล้หมดสต็อก"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        sql = "SELECT item_code, item_name, qty_on_hand, reorder_point FROM stock_items WHERE qty_on_hand <= reorder_point"
        cur.execute(sql)
        results = cur.fetchall()
        
        if not results:
            return {"message": "ตอนนี้ไม่มีสินค้าใดที่สต็อกต่ำกว่าเกณฑ์สั่งซื้อครับ"}
        return {"message": "พบสินค้าที่สต็อกต่ำกว่าเกณฑ์ กรุณาเตรียมสั่งซื้อ:", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()