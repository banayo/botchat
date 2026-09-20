from typing import Any

from mkt import QUALIFIED_VIEW

# Fill this after running sql/collect_mkt_view.sql.
# Do not guess column names. Controlled reports stay off until this is True.
REGISTRY_READY = False

MKT_FIELDS: dict[str, dict[str, Any]] = {
    "cre_date": {
        "column": "CRE_DATE",
        "description": "วันที่สร้างเอกสาร ใช้เป็นวันที่หลักสำหรับวิเคราะห์ยอดขาย",
        "role": "date",
        "use_for_filter": True,
        "use_for_group": True,
    },
    "qty1": {
        "column": "QTY1",
        "description": "จำนวนสินค้า ใช้รวมยอดจำนวน อย่าใช้เป็นมูลค่าเงิน",
        "role": "measure",
        "use_for_filter": False,
        "use_for_group": False,
    },
    "item_amt1": {
        "column": "ITEM_AMT1",
        "description": "มูลค่ารายการสินค้า หน่วยบาท",
        "role": "measure",
        "use_for_filter": False,
        "use_for_group": False,
    },
    "CUST_NAME": {
        "column": "CUST_NAME",
        "description": "ชื่อลูกค้าของบิลนั้น ใช้กรองและจัดกลุ่มได้ ไม่ใช่ชื่อพนักงานขาย",
        "role": "dimension",
        "use_for_filter": True,
        "use_for_group": True,
    },
    "SALE_NAME": {
        "column": "SALE_NAME",
        "description": (
            "ชื่อพนักงานขายของบิลนั้น ใช้กรองและจัดกลุ่มได้ "
            "ไม่ใช่ผู้ได้ค่าคอม ดูค่าคอมที่ SELECOM_NAME"
        ),
        "role": "dimension",
        "use_for_filter": True,
        "use_for_group": True,
    },
    "CUST_GROUP": {
        "column": "CUST_GROUP",
        "description": (
            "กลุ่มลูกค้า ใช้กรองและจัดกลุ่มได้ "
            "ไม่ใช่กลุ่มสินค้า ดูกลุ่มสินค้าที่ GROUP_NAME_TH"
        ),
        "role": "dimension",
        "use_for_filter": True,
        "use_for_group": True,
    },
    "CUST_CHANNEL": {
        "column": "CUST_CHANNEL",
        "description": "ช่องทางการขายของลูกค้า/บิล ใช้กรองและจัดกลุ่มได้",
        "role": "dimension",
        "use_for_filter": True,
        "use_for_group": True,
    },
    "SUB_DESC": {
        "column": "SUB_DESC",
        "description": (
            "ประเภทการขายของบิล "
            "ขายสด - ลูกค้าทั่วไป = ขายสดให้ลูกค้าทั่วไป "
            "ขายเชื่อ - ในประเทศ = ขายเชื่อในประเทศ "
            "ขายต่างประเทศ = ขายต่างประเทศ "
            "ใช้กรองและจัดกลุ่มได้"
        ),
        "role": "dimension",
        "use_for_filter": True,
        "use_for_group": True,
    },
    "SELECOM_NAME": {
        "column": "SELECOM_NAME",
        "description": (
            "ชื่อผู้ได้ค่าคอมของบิลนั้น "
            "NO-COM = บิลนี้ไม่มีค่าคอม "
            "ถ้าเป็นชื่อคน = คนนั้นได้ค่าคอมของบิลนี้ "
            "ใช้กรองและจัดกลุ่มได้ อย่าใช้เป็นมูลค่าเงิน"
        ),
        "role": "dimension",
        "use_for_filter": True,
        "use_for_group": True,
    },
    "WH_ID": {
        "column": "WH_ID",
        "description": "รหัสคลังที่บิลนั้นตัดสต็อก ใช้บอกว่าบิลตัดจากคลังไหน กรองและจัดกลุ่มได้",
        "role": "dimension",
        "use_for_filter": True,
        "use_for_group": True,
    },
    "FOC": {
        "column": "FOC",
        "description": (
            "สถานะโปรโมชันของบิล "
            "N = บิลนั้นไม่มีโปร "
            "Y = บิลนั้นมีโปร "
            "ใช้กรองและจัดกลุ่มได้"
        ),
        "role": "dimension",
        "use_for_filter": True,
        "use_for_group": True,
    },
    "FIRST_SALE_DATE": {
        "column": "FIRST_SALE_DATE",
        "description": (
            "วันที่สินค้าขายวันแรก "
            "ไม่ใช่วันที่บิล ห้ามใช้แทน CRE_DATE เมื่อวิเคราะห์ยอดตามช่วงเวลาขาย"
        ),
        "role": "date",
        "use_for_filter": True,
        "use_for_group": True,
    },
    "FIRST_DISCON": {
        "column": "FIRST_DISCON",
        "description": (
            "วันที่สินค้าเลิกขาย "
            "ไม่ใช่วันที่บิล ห้ามใช้แทน CRE_DATE เมื่อวิเคราะห์ยอดตามช่วงเวลาขาย"
        ),
        "role": "date",
        "use_for_filter": True,
        "use_for_group": True,
    },
    "GROUP_NAME_TH": {
        "column": "GROUP_NAME_TH",
        "description": (
            "กลุ่มสินค้า ชั้นใหญ่ที่สุดในลำดับสินค้า "
            "ใหญ่กว่า CATEGORY_DESC_TH และ SUB_CAT_DESC_TH"
        ),
        "role": "dimension",
        "use_for_filter": True,
        "use_for_group": True,
    },
    "CATEGORY_DESC_TH": {
        "column": "CATEGORY_DESC_TH",
        "description": (
            "หมวดหมู่สินค้า อยู่ภายใต้ GROUP_NAME_TH "
            "ใหญ่กว่า SUB_CAT_DESC_TH"
        ),
        "role": "dimension",
        "use_for_filter": True,
        "use_for_group": True,
    },
    "SUB_CAT_DESC_TH": {
        "column": "SUB_CAT_DESC_TH",
        "description": (
            "หมวดหมู่ย่อยสินค้า ชั้นเล็กที่สุด "
            "อยู่ภายใต้ CATEGORY_DESC_TH และ GROUP_NAME_TH"
        ),
        "role": "dimension",
        "use_for_filter": True,
        "use_for_group": True,
    },
    "COLOR_TH": {
        "column": "COLOR_TH",
        "description": "สีสินค้า (ชื่อภาษาไทย) ใช้กรองและจัดกลุ่มได้",
        "role": "dimension",
        "use_for_filter": True,
        "use_for_group": True,
    },
    "SERIES": {
        "column": "SERIES",
        "description": "ซีรีส์สินค้า ใช้กรองและจัดกลุ่มได้",
        "role": "dimension",
        "use_for_filter": True,
        "use_for_group": True,
    },
}

MKT_DIMENSIONS: dict[str, dict[str, str]] = {}

MKT_METRICS: dict[str, dict[str, Any]] = {}

DATE_FILTER_COLUMN = ""
FROM_CLAUSE = QUALIFIED_VIEW
