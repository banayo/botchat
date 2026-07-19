import os
from database import get_db_connection

def setup_mock_database():
    '''
    สร้างตารางและจำลองข้อมูลสต็อกสินค้าเบื้องต้น
    '''
    conn = get_db_connection()
    if not conn:
        print("Failed to connect. Cannot setup mock data.")
        return

    try:
        cur = conn.cursor()
        
        # สร้างตาราง stock_items
        cur.execute('''
            CREATE TABLE IF NOT EXISTS stock_items (
                item_code VARCHAR(50) PRIMARY KEY,
                item_name VARCHAR(100) NOT NULL,
                category VARCHAR(50),
                qty_on_hand INTEGER DEFAULT 0,
                reorder_point INTEGER DEFAULT 10,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # เช็คว่ามีข้อมูลหรือยัง ถ้ายังให้ใส่เข้าไป
        cur.execute("SELECT COUNT(*) FROM stock_items")
        if cur.fetchone()[0] == 0:
            mock_items = [
                ('A101', 'Ubiquiti UniFi AP AC Pro', 'Networking', 15, 5),
                ('A102', 'MikroTik RouterBOARD', 'Networking', 3, 10),
                ('B201', 'Fortinet FortiGate 60F', 'Security', 2, 2),
                ('C301', 'Anytek Wireless Mouse', 'Accessories', 50, 20),
                ('C302', 'Low-profile Keyboard XDA', 'Accessories', 8, 15)
            ]
            
            cur.executemany('''
                INSERT INTO stock_items (item_code, item_name, category, qty_on_hand, reorder_point)
                VALUES (%s, %s, %s, %s, %s)
            ''', mock_items)
            
            print("Successfully inserted mock data.")
        else:
            print("Mock data already exists.")
            
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"Error setting up database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    setup_mock_database()