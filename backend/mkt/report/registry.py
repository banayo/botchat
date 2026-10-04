from typing import Any

from mkt import QUALIFIED_VIEW

# Columns collected from KMPROD.MKT$ERP_SALE_REP (not guessed names).
# Controlled reports require REGISTRY_READY and filled MKT_DIMENSIONS / MKT_METRICS.
REGISTRY_READY = True

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
    "SHOP_TYPE": {
        "column": "SHOP_TYPE",
        "description": (
            "ประเภทร้านของบิล "
            "(เช่น BEAUTY, ONLINE, WEB, MART, LIVE) "
            "ใช้กรองและจัดกลุ่มเป็นประเภทร้านค้าได้ "
            "ไม่ใช่ช่องทางขาย ดูที่ CUST_CHANNEL"
        ),
        "role": "dimension",
        "use_for_filter": True,
        "use_for_group": True,
    },
    "CUST_CHANNEL": {
        "column": "CUST_CHANNEL",
        "description": (
            "ช่องทางขายของบิล "
            "(เช่น ONL, TDT, MDT, KMS, DEP, EXP) "
            "ใช้กรองและจัดกลุ่มตามช่องทางขายได้ "
            "ไม่ใช่ประเภทร้าน ดูช่องทางที่ SHOP_TYPE"
        ),
        "role": "dimension",
        "use_for_filter": True,
        "use_for_group": True,
    },
    "CUST_AREA_CODE": {
        "column": "CUST_AREA_CODE",
        "description": (
            "ใช้เฉพาะสองแผนก "
            "CUST_CHANNEL = EXP คือชื่อประเทศ "
            "CUST_CHANNEL = TDT คือรหัสพื้นที่ เช่น BK-C1 "
            "แผนกอื่นไม่ใช้คอลัมน์นี้ "
            "ทีมของ TDT ดูที่ BAND_GROUP ไม่ใช่คอลัมน์นี้"
        ),
        "role": "dimension",
        "use_for_filter": True,
        "use_for_group": True,
    },
    "BAND_GROUP": {
        "column": "BAND_GROUP",
        "description": (
            "ทีมของแผนก TDT แบ่งได้ 2 ทีมคือ BBB และ CTD "
            "ใช้เมื่อ CUST_CHANNEL = TDT "
            "ไม่ใช่รหัสพื้นที่ รหัสพื้นที่ของ TDT อยู่ที่ CUST_AREA_CODE"
        ),
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
    "BRAND_CODE": {
        "column": "BRAND_CODE",
        "description": "รหัสแบรนด์ เช่น 'CD (M)' ต้องมีเว้นวรรค ใช้กรองและจัดกลุ่มได้",
        "role": "dimension",
        "use_for_filter": True,
        "use_for_group": True,
    },
}

MKT_DIMENSIONS: dict[str, dict[str, str]] = {
    "month": {
        "expression": "TRUNC(CRE_DATE, 'MM')",
        "alias": "MONTH_KEY",
        "description": "เดือนตามวันที่สร้างเอกสาร",
    },
    "channel": {
        "expression": "SHOP_TYPE",
        "alias": "SHOP_TYPE",
        "description": "ช่องทาง/ประเภทร้าน (SHOP_TYPE)",
        "filter_column": "SHOP_TYPE",
        # every SHOP_TYPE value in the view is uppercase (BEAUTY, ONLINE, ...)
        "filter_case": "upper",
    },
    "dept": {
        "expression": "CUST_CHANNEL",
        "alias": "CUST_CHANNEL",
        "description": "แผนกขาย (CUST_CHANNEL)",
        "filter_column": "CUST_CHANNEL",
        # every CUST_CHANNEL value in the view is uppercase (ONL, TDT, ...)
        "filter_case": "upper",
    },
}

MKT_METRICS: dict[str, dict[str, Any]] = {
    "sales": {
        "description": "ยอดขาย (บาท) จาก ITEM_AMT1",
        "base_expression": "ITEM_AMT1",
        "allowed_aggregations": {
            "sum": "SUM",
            "average": "AVG",
        },
        # View has no CANCEL column; do not invent filters.
        "mandatory_filters": [],
    },
    "quantity": {
        "description": "จำนวนสินค้าจาก QTY1",
        "base_expression": "QTY1",
        "allowed_aggregations": {
            "sum": "SUM",
            "average": "AVG",
        },
        "mandatory_filters": [],
    },
}

DATE_FILTER_COLUMN = MKT_FIELDS["cre_date"]["column"]
FROM_CLAUSE = QUALIFIED_VIEW
