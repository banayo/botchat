from typing import Any

from export import QUALIFIED_VIEW

# Columns collected from KMPROD.EXP$ERP_SALE_REP_EXP (not guessed names).
# Executable SQL lives here. Oracle COMMENT ON COLUMN is documentation only.

EXPORT_FIELDS: dict[str, dict[str, Any]] = {
    "create_date": {
        "column": "CRE_DATE",
        "description": "วันที่สร้างเอกสาร ใช้เป็นวันที่หลักสำหรับวิเคราะห์ยอดขาย",
        "role": "date",
        "use_for_filter": True,
        "use_for_group": True,
    },
    "module": {
        "column": "MODULE",
        "description": "ประเภทเอกสาร (IV = ใบขาย, RT = ใบคืน, CN = ใบลดหนี้, DN = ใบเพิ่มหนี้)",
        "role": "dimension",
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
    "cancel": {
        "column": "CANCEL",
        "description": "สถานะยกเลิก (Y = ยกเลิก, N = เอกสารปกติ)",
        "role": "dimension",
        "use_for_filter": True,
        "use_for_group": False,
    },
    "zone_name": {
        "column": "ZONE_NAME",
        "description": "พื้นที่ขาย / เขต ใช้เป็นมิติประเทศหรือโซน",
        "role": "dimension",
        "use_for_filter": True,
        "use_for_group": True,
    },
}

EXPORT_DIMENSIONS: dict[str, dict[str, str]] = {
    "month": {
        "expression": "TRUNC(CRE_DATE, 'MM')",
        "alias": "MONTH_KEY",
        "description": "เดือนตามวันที่สร้างเอกสาร",
    },
    "country": {
        "expression": "ZONE_NAME",
        "alias": "COUNTRY",
        "description": "พื้นที่ขาย / เขต",
        "filter_column": "ZONE_NAME",
    },
}

EXPORT_METRICS: dict[str, dict[str, Any]] = {
    "sales": {
        "description": "ยอดขายสุทธิ (บาท) กลับเครื่องหมายใบคืนและใบลดหนี้",
        "base_expression": """
            CASE
                WHEN MODULE IN ('RT', 'CN') THEN -ITEM_AMT1
                WHEN MODULE IN ('IV', 'DN') THEN ITEM_AMT1
                ELSE 0
            END
        """,
        "allowed_aggregations": {
            "sum": "SUM",
            "average": "AVG",
        },
        "mandatory_filters": [
            "CANCEL = 'N'",
        ],
    },
    "quantity": {
        "description": "จำนวนสินค้าสุทธิ กลับเครื่องหมายใบคืนและใบลดหนี้",
        "base_expression": """
            CASE
                WHEN MODULE IN ('RT', 'CN') THEN -QTY1
                WHEN MODULE IN ('IV', 'DN') THEN QTY1
                ELSE 0
            END
        """,
        "allowed_aggregations": {
            "sum": "SUM",
            "average": "AVG",
        },
        "mandatory_filters": [
            "CANCEL = 'N'",
        ],
    },
}

DATE_FILTER_COLUMN = EXPORT_FIELDS["create_date"]["column"]
FROM_CLAUSE = QUALIFIED_VIEW
