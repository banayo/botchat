# Export Chat / Export Report

ระบบถามข้อมูลแผนกส่งออกใน `botchat`  
ผู้ใช้คุยภาษาธรรมชาติหรือขอรายงานรวม แล้ว FastAPI ดึงข้อมูลจาก Oracle view `KMPROD.EXP$ERP_SALE_REP_EXP`  
LLM เป็น vLLM คนละเครื่อง มีด่านกัน SQL อันตราย และมีเส้นทางรายงานที่ SQL ถูกประกอบจาก registry ไม่ให้โมเดลเขียนอิสระ

## สองเส้นทาง

```
Open WebUI
 ├─ ask_export_data
 │    POST /api/export-chat
 │    คำถามอิสระ → LangChain SQL Agent → SQL guard → Oracle
 │
 └─ show_export_pivot   (ปิดอยู่จนกว่า ENABLE_PIVOT=true)
      POST /api/export-report
      JSON โครงสร้างตายตัว → registry → SQL builder → Oracle
```

ของที่ใช้ร่วมกัน:

- view เดียว และบัญชี Oracle แบบอ่านอย่างเดียว (ค่าใน `.env`)
- registry กฎธุรกิจ (สูตรยอดขาย, ตัดบิลยกเลิก)
- Authentik JWT
- audit log (ไม่เก็บ token / รหัสผ่าน / แถวลูกค้าเต็ม)
- SQL แบบ Oracle 11g (`ROWNUM` ไม่ใช้ `FETCH FIRST`)

LangChain agent **ไม่ได้ถูกลบ** รายงานควบคุมเป็นทางเสริมสำหรับคำถามซ้ำที่รู้โครงสร้างแล้ว

## สิ่งที่ต้องไม่สับสน

| ชื่อ | ความหมาย |
|---|---|
| `KMPRDDB` | service name ของ instance Oracle |
| `KMPROD` | owner/schema ของ view |
| `EXP$ERP_SALE_REP_EXP` | ชื่อ view ในพจนานุกรม Oracle (ตัวพิมพ์ใหญ่) |
| `exp$erp_sale_rep_exp` | ชื่อที่ LangChain inspector มักคืนมา ใช้กับ `sql_db_schema` |

สามชั้นใช้คนละกติกาชื่อ:

- Oracle `ALL_VIEWS`: `KMPROD.EXP$ERP_SALE_REP_EXP`
- LangChain tools: ชื่อสั้น ตัวพิมพ์ต้องตรงลิสต์ ห้ามใส่ schema นำหน้าตอนเรียก tool
- `SELECT` ไม่ quote: Oracle พับเป็นตัวใหญ่ได้

ตัวอย่างในเอกสารเก่า (`INV_DATE`, `PAY_DATE`, `NET_AMOUNT`, `DOC_TYPE`) **ไม่ได้ใช้ในโค้ด** เพราะห้ามเดาคอลัมน์

## คอลัมน์ที่ใช้จริง (registry)

| ความหมาย | คอลัมน์ Oracle |
|---|---|
| วันที่วิเคราะห์ยอด | `CRE_DATE` |
| ประเภทเอกสาร | `MODULE` (`IV` ขาย, `RT` คืน, `CN` ลดหนี้, `DN` เพิ่มหนี้) |
| มูลค่า (บาท) | `ITEM_AMT1` |
| จำนวน | `QTY1` |
| ยกเลิก | `CANCEL` (`N` ปกติ, `Y` ยกเลิก) |
| เขต / พื้นที่ขาย | `ZONE_NAME` (มิติ API ชื่อ `country`) |

กฎยอดใน controlled path:

- บังคับ `CANCEL = 'N'`
- `RT` / `CN` กลับเครื่องหมายเป็นลบ
- `IV` / `DN` เป็นบวก

`COMMENT ON COLUMN` เป็นเอกสารให้ LangChain อ่านเท่านั้น **เปลี่ยน comment ไม่ได้เปลี่ยนสูตร SQL** สูตรอยู่ที่ `backend/export/report/registry.py`

## โครงสร้างไฟล์

```
backend/
  main.py
  database.py              # URI + Instant Client thick mode
  ai_config.py             # ChatOpenAI → vLLM
  db/oracle.py             # engine เดียวต่อ process
  routers/auth.py          # JWT Authentik
  export/
    routes.py
    authz.py
    audit.py
    chat/
    report/

sql/collect_export_view.sql
sql/export_oracle_setup.sql
openwebui-tools/export_tools.py
```

## API

### `POST /api/export-chat`

Body:

```json
{ "question": "สรุปยอดขายส่งออกเดือนล่าสุด" }
```

ต้องมี `Authorization: Bearer <access_token>`

ตอบ:

```json
{ "kind": "answer", "reply": "..." }
```

พฤติกรรม:

- สร้าง engine + agent ครั้งเดียวต่อ process (`lru_cache`) มี lock กัน request ซ้อน
- รัน agent ใน `asyncio.to_thread`
- ทุก SQL ผ่าน `validate_and_limit_sql` ก่อนถึง Oracle
- ไม่สุ่มแถวตัวอย่างเข้า prompt (`sample_rows_in_table_info=0`)
- เพดาน: `top_k=50`, `max_iterations=6`, `max_execution_time=90`
- ผลถูกคลุม `ROWNUM <= 50`

### `POST /api/export-report`

ตัวอย่าง body:

```json
{
  "dimensions": ["month", "country"],
  "metric": "sales",
  "aggregation": "sum",
  "date_from": "2024-01-01",
  "date_to": "2024-12-31",
  "country": null,
  "limit": 500
}
```

ข้อจำกัด: สูงสุด 3 มิติ, `date_to` ต้องหลัง `date_from`, ช่วงไม่เกินประมาณ 3 ปี, `limit` 1–2000

`date_to` ใน SQL เป็น exclusive (`CRE_DATE < วันถัดไป`) จึงนับรวมวันสุดท้ายที่ผู้ใช้เลือก

ตอบมี `kind: "pivot"`, `columns`, `rows`, `row_count`, `summary` สั้น สำหรับ UI ไม่ส่งชุดใหญ่กลับไปให้โมเดลสรุป

ถ้า JSON ไม่ผ่าน validation ได้ HTTP 422

## SQL guard

ไฟล์ `backend/export/chat/sql_guard.py` ใช้ sqlglot (Oracle) เป็นหลัก

ปฏิเสธ:

- ไม่ใช่ `SELECT` / `WITH ... SELECT`
- หลาย statement
- database link (`@`)
- DML/DDL
- ตารางอื่นนอก `KMPROD.EXP$ERP_SALE_REP_EXP`
- `FETCH FIRST` / `OFFSET` / `LIMIT`
- ฟังก์ชันประมาณ `DBMS_*`, `UTL_*`, `SYS.`

ถ้าผ่าน จะห่อ:

```sql
SELECT * FROM (
  <query>
) WHERE ROWNUM <= 50
```

ตัวเลข cap มาจากโค้ด ไม่มาจากข้อความที่โมเดลพิมพ์

## ความปลอดภัย

- แอปต้องไม่ล็อกอินเป็น `KMPROD` ใช้บัญชี `SELECT` บน view นี้เท่านั้น (เช่น `EXPORT_AI`)
- ไม่เชื่อ `user_id` ใน body ตัวตนมาจาก JWT
- `EXPORT_ALLOWED_GROUPS` ว่าง = JWT ที่ valid ก็เข้าได้ ถ้าใส่ค่าต้องตรงกลุ่ม Authentik
- audit ไม่เก็บ token, รหัส Oracle, แถวข้อมูลเต็ม

## Open WebUI

`openwebui-tools/export_tools.py`

| Tool | ใช้เมื่อ | เรียก |
|---|---|---|
| `ask_export_data` | คำถามรายละเอียด / นอกกรอบรายงาน | `/api/export-chat` |
| `show_export_pivot` | รวมยอด เทียบ เทรนด์ (ยังปิด) | `/api/export-report` |

เปิด pivot เมื่อเทสสูตรยอดขายแล้ว ตั้ง `ENABLE_PIVOT=true`

## ปัญหาที่เคยเจอ (ย่อ)

1. vLLM คนละเครื่อง ชื่อโมเดลต้องตรง `GET /v1/models` และต้องส่ง API key ทดสอบจากใน container
2. `include_tables` / `sql_db_schema` เทียบชื่อแบบตรงตัว ทั้งตัวพิมพ์และมี/ไม่มี schema
3. สร้าง `SQLDatabase` ทุก request ทำให้ช้าจาก reflect catalog ไม่ใช่แค่ SQL ช้า
4. ย้าย prompt ไป `.md` ไม่ลดค่าโมเดล ถ้าข้อความยาวเท่าเดิม

## สิ่งที่ต้องทำบนเครื่องจริง

1. รัน `sql/collect_export_view.sql` ยืนยันคอลัมน์ แล้วค่อยขยาย registry
2. รัน `sql/export_oracle_setup.sql` (DBA): `COMMENT ON COLUMN` + สร้าง user อ่านอย่างเดียว
3. ตั้ง `.env`: `ORACLE_USER` เป็นบัญชีนั้น, vLLM, Authentik
4. rebuild `assistant_api` เพราะมี `sqlglot` / `sqlalchemy` ใน `requirements.txt`
5. ทดสอบ IT ด้วย `ask_export_data` ก่อน แล้วค่อยเปิด pivot

## เทสหน่วย

จากโฟลเดอร์ `backend`:

```bat
python -m pytest tests -q
```

ครอบคลุม: ปฏิเสธ DML / ตารางอื่น / database link / หลาย statement / `FETCH FIRST`, builder ใช้ `CRE_DATE` + `ROWNUM` + bind, Pydantic ปฏิเสธช่วงวันที่ผิด
