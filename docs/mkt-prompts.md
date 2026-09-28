# Open WebUI Prompts — Marketing

คัดลอกแต่ละบล็อกไปที่ **Workspace → Prompts → Create**  
ต้องมี tools `show_mkt_pivot` และ `show_mkt_yoy` จาก `openwebui-tools/mkt_tools.py` เปิดอยู่

| dimensions | คอลัมน์ | ความหมาย |
|------------|---------|----------|
| `dept` | `CUST_CHANNEL` | แผนกขาย (ONL, TDT, MDT, KMS, …) |
| `channel` | `SHOP_TYPE` | ช่องทาง/ประเภทร้าน (BEAUTY, ONLINE, WEB, …) |

---

## 1. ยอดขายรายวัน แยกแผนกขาย

| Field | Value |
|-------|--------|
| Command | `mkt-daily-dept` |
| Title | ยอดขายรายวัน แยกแผนกขาย |

**Content:**

```
คุณต้องเรียก tool show_mkt_pivot เท่านั้น
ห้ามตอบตัวเลขจากความรู้เอง
ห้ามใช้ ask_mkt_data และห้ามใช้ show_mkt_yoy

เรียก 2 ครั้ง แล้วสรุปเป็นตารางภาษาไทย คอลัมน์: แผนกขาย | ยอดขาย (บาท) | จำนวน

1) dimensions=["dept"], metric="sales", aggregation="sum",
   date_from=<เมื่อวาน YYYY-MM-DD>, date_to=<เมื่อวาน YYYY-MM-DD>, limit=500

2) dimensions=["dept"], metric="quantity", aggregation="sum",
   date_from / date_to ชุดเดียวกัน

รวมผลตาม CUST_CHANNEL (แผนกขาย) จาก rows ของทั้งสองครั้ง
ถ้า rows ว่าง ให้บอกว่าไม่มีข้อมูล ห้ามเดาตัวเลขหรือชื่อแผนก
ระบุวันที่ที่ใช้ในคำตอบให้ชัด
```

ใช้งาน: `/mkt-daily-dept`

---

## 2. ยอด MTD เทียบปีที่แล้ว แยกแผนกขาย (ผู้บริหาร)

| Field | Value |
|-------|--------|
| Command | `mkt-mtd-yoy` |
| Title | ยอด MTD เทียบปีที่แล้ว แยกแผนกขาย |

**Content:**

```
คุณต้องเรียก tool show_mkt_yoy เท่านั้น
ห้ามตอบตัวเลขจากความรู้เอง
ห้ามใช้ ask_mkt_data และห้ามใช้ show_mkt_pivot

เรียกครั้งเดียวด้วยพารามิเตอร์นี้:
- mode="mtd_yoy"
- dimensions=["dept"]
- metric="sales"
- aggregation="sum"

สรุปภาษาไทยสั้นๆ แบบผู้บริหาร:
1) จาก summary: ยอดรวมปีนี้ (current_total) vs ปีที่แล้ว (prior_total) + ส่วนต่างและ %
2) ตารางแผนกจาก rows: CUST_CHANNEL | CURRENT_VALUE | PRIOR_VALUE | DELTA | PCT_CHANGE
3) ระบุช่วงวันที่ current_period และ prior_period ให้ชัด
4) แบ่งตาม CUST_CHANNEL เทียบกับปีที่แล้ว ทีละแผนก:
   ยอดปีนี้ (CURRENT_VALUE), ยอดปีที่แล้ว (PRIOR_VALUE),
   โตหรือหดกี่บาท (DELTA) และกี่เปอร์เซ็นต์ (PCT_CHANGE)
   เรียงจากโตมากไปน้อย
   PCT_CHANGE เป็นบวก = โต, เป็นลบ = หด
   ห้ามคำนวณตัวเลขเอง ใช้ค่าจาก rows เท่านั้น

ถ้าไม่มีข้อมูลห้ามเดาตัวเลขหรือชื่อแผนก
```

ใช้งาน: `/mkt-mtd-yoy`

---

## 3. ยอดทั้งเดือน เทียบปีที่แล้ว แยกแผนกขาย

| Field | Value |
|-------|--------|
| Command | `mkt-month-yoy` |
| Title | ยอดทั้งเดือน เทียบปีที่แล้ว แยกแผนกขาย |

**Content:**

```
คุณต้องเรียก tool show_mkt_yoy เท่านั้น
ห้ามตอบตัวเลขจากความรู้เอง
ห้ามใช้ ask_mkt_data

เรียกครั้งเดียว:
- mode="full_month_yoy"
- dimensions=["dept"]
- metric="sales"
- aggregation="sum"

สรุปแบบผู้บริหาร:
1) ยอดรวมทั้งเดือนปีนี้ vs ปีที่แล้ว + %
2) Top แผนกที่โต และที่หด (จาก PCT_CHANGE)
3) ตารางสั้นไม่เกิน 15 แถว เรียงตาม CURRENT_VALUE
4) แบ่งตาม CUST_CHANNEL เทียบกับปีที่แล้ว ทีละแผนก:
   ยอดปีนี้ (CURRENT_VALUE), ยอดปีที่แล้ว (PRIOR_VALUE),
   โตหรือหดกี่บาท (DELTA) และกี่เปอร์เซ็นต์ (PCT_CHANGE)
   เรียงจากโตมากไปน้อย
   PCT_CHANGE เป็นบวก = โต, เป็นลบ = หด
   ห้ามคำนวณตัวเลขเอง ใช้ค่าจาก rows เท่านั้น
ระบุช่วงวันที่ทั้งสองช่วงให้ชัด ห้ามเดาถ้าไม่มีข้อมูล
```

ใช้งาน: `/mkt-month-yoy`

---

## 4. ยอดขายรายวัน แยกช่องทางร้าน (SHOP_TYPE)

| Field | Value |
|-------|--------|
| Command | `mkt-daily-channel` |
| Title | ยอดขายรายวัน แยกช่องทางร้าน |

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

รวมผลตาม SHOP_TYPE จาก rows ของทั้งสองครั้ง
ถ้า rows ว่าง ให้บอกว่าไม่มีข้อมูล ห้ามเดา
ระบุวันที่ที่ใช้ในคำตอบให้ชัด
```

ใช้งาน: `/mkt-daily-channel`

---

## หมายเหตุ

- `dept` = แผนกขาย (`CUST_CHANNEL`) · `channel` = ช่องทางร้าน (`SHOP_TYPE`) — คนละความหมาย
- `date_from` / `date_to` ของ pivot เป็นวันแบบ **inclusive**
- YoY ไม่ต้องส่งวันที่เอง ระบบใช้วันนี้เป็น `as_of`
- ยอดรวมทั้งบริษัท: `dimensions=[]`
- API: `POST /api/mkt-report` และ `POST /api/mkt-report/yoy`
