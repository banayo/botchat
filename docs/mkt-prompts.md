# Open WebUI Prompts — Marketing

คัดลอกแต่ละบล็อกไปที่ **Workspace → Prompts → Create**  
ต้องมี tools `show_mkt_pivot` และ `show_mkt_yoy` จาก `openwebui-tools/mkt_tools.py` เปิดอยู่

---

## 1. ยอดขายรายวัน แยกช่องทาง

| Field | Value |
|-------|--------|
| Command | `mkt-daily-channel` |
| Title | ยอดขายรายวัน แยกช่องทาง |

**Content:**

```
คุณต้องเรียก tool show_mkt_pivot เท่านั้น
ห้ามตอบตัวเลขจากความรู้เอง
ห้ามใช้ ask_mkt_data และห้ามใช้ show_mkt_yoy

เรียก 2 ครั้ง แล้วสรุปเป็นตารางภาษาไทย คอลัมน์: ช่องทาง | ยอดขาย (บาท) | จำนวน

1) dimensions=["channel"], metric="sales", aggregation="sum",
   date_from=<เมื่อวาน YYYY-MM-DD>, date_to=<เมื่อวาน YYYY-MM-DD>, limit=500

2) dimensions=["channel"], metric="quantity", aggregation="sum",
   date_from / date_to ชุดเดียวกัน

รวมผลตาม CUST_CHANNEL จาก rows ของทั้งสองครั้ง
ถ้า rows ว่าง ให้บอกว่าไม่มีข้อมูล ห้ามเดาตัวเลขหรือชื่อช่องทาง
ระบุวันที่ที่ใช้ในคำตอบให้ชัด
```

ใช้งาน: ในแชทพิมพ์ `/mkt-daily-channel`

---

## 2. ยอด MTD เทียบปีที่แล้ว (ผู้บริหาร)

| Field | Value |
|-------|--------|
| Command | `mkt-mtd-yoy` |
| Title | ยอด MTD เทียบเดือนเดียวกันปีที่แล้ว |

**Content:**

```
คุณต้องเรียก tool show_mkt_yoy เท่านั้น
ห้ามตอบตัวเลขจากความรู้เอง
ห้ามใช้ ask_mkt_data และห้ามใช้ show_mkt_pivot

เรียกครั้งเดียวด้วยพารามิเตอร์นี้:
- mode="mtd_yoy"
- dimensions=["channel"]
- metric="sales"
- aggregation="sum"

สรุปภาษาไทยสั้นๆ แบบผู้บริหาร:
1) จาก summary: ยอดรวมปีนี้ (current_total) vs ปีที่แล้ว (prior_total) + ส่วนต่างและ %
2) ตารางช่องทางจาก rows: CUST_CHANNEL | CURRENT_VALUE | PRIOR_VALUE | DELTA | PCT_CHANGE
3) ระบุช่วงวันที่ current_period และ prior_period ให้ชัด

ถ้าไม่มีข้อมูลห้ามเดาตัวเลขหรือชื่อช่องทาง
```

ใช้งาน: `/mkt-mtd-yoy`

---

## 3. ยอดทั้งเดือน เทียบปีที่แล้ว

| Field | Value |
|-------|--------|
| Command | `mkt-month-yoy` |
| Title | ยอดทั้งเดือน เทียบเดือนเดียวกันปีที่แล้ว |

**Content:**

```
คุณต้องเรียก tool show_mkt_yoy เท่านั้น
ห้ามตอบตัวเลขจากความรู้เอง
ห้ามใช้ ask_mkt_data

เรียกครั้งเดียว:
- mode="full_month_yoy"
- dimensions=["channel"]
- metric="sales"
- aggregation="sum"

สรุปแบบผู้บริหาร:
1) ยอดรวมทั้งเดือนปีนี้ vs ปีที่แล้ว + %
2) Top ช่องทางที่โต และที่หด (จาก PCT_CHANGE)
3) ตารางสั้นไม่เกิน 15 แถว เรียงตาม CURRENT_VALUE
ระบุช่วงวันที่ทั้งสองช่วงให้ชัด ห้ามเดาถ้าไม่มีข้อมูล
```

ใช้งาน: `/mkt-month-yoy`

---

## หมายเหตุ

- `date_from` / `date_to` ของ pivot เป็นวันแบบ **inclusive**
- YoY ไม่ต้องส่งวันที่เอง ระบบใช้วันนี้เป็น `as_of` (หรือส่ง `as_of` ถ้าต้องการย้อนหลัง)
- ต้องการยอดรวมทั้งบริษัทไม่แยกช่องทาง: ใช้ `dimensions=[]` กับ `show_mkt_yoy`
- API ตรง: `POST /api/mkt-report` และ `POST /api/mkt-report/yoy`
