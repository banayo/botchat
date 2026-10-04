from typing import Any

# Columns on the returns-request view only. Do not reuse MKT_FIELDS here.
# CONIFRIM_CN_ON is spelled as stored. An empty value means the request is not approved yet.
MKT_RETURN_FIELDS: dict[str, dict[str, Any]] = {
    "RTR_NO": {
        "column": "RTR_NO",
        "description": "เลขที่ใบขอคืน",
    },
    "CONIFRIM_CN_ON": {
        "column": "CONIFRIM_CN_ON",
        "description": (
            "เลขที่ใบคืน "
            "ถ้าไม่มีค่า ใบขอคืนยังไม่ผ่าน"
        ),
    },
    "SALES_GROUP": {
        "column": "SALES_GROUP",
        "description": "ช่องทางที่ทำใบขอคืนมา",
    },
    "WARE_CODE": {
        "column": "WARE_CODE",
        "description": "รหัสคลังที่รับคืนสินค้า",
    },
    "TRAN_QTY": {
        "column": "TRAN_QTY",
        "description": "จำนวนที่ขอคืน อย่าใช้เป็นมูลค่าเงิน",
    },
    "TOTAL_PRICE": {
        "column": "TOTAL_PRICE",
        "description": "จำนวนเงินของใบขอคืน หน่วยบาท ไม่ใช่ยอดขาย",
    },
    "ITEM_NAME_TH": {
        "column": "ITEM_NAME_TH",
        "description": "ชื่อสินค้าภาษาไทยที่ขอคืน",
    },
    "RTR_DATE": {
        "column": "RTR_DATE",
        "description": "วันที่ทำเลขที่ใบขอคืน ใช้เป็นวันที่หลักเมื่อถามช่วงเวลา",
    },
}
