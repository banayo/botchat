-- Run as KMPROD or a DBA. The FastAPI app must not connect as KMPROD.
-- Comments are documentation for LangChain. SQL behavior lives in export/registry.py.

-- CREATE USER EXPORT_AI IDENTIFIED BY "change-me";
-- GRANT CREATE SESSION TO EXPORT_AI;
-- GRANT SELECT ON KMPROD.EXP$ERP_SALE_REP_EXP TO EXPORT_AI;

COMMENT ON COLUMN KMPROD.EXP$ERP_SALE_REP_EXP.CRE_DATE IS
  'วันที่สร้างเอกสาร ใช้เป็นวันที่หลักสำหรับวิเคราะห์ยอดขายส่งออก กรองช่วงเวลาด้วยคอลัมน์นี้';

COMMENT ON COLUMN KMPROD.EXP$ERP_SALE_REP_EXP.MODULE IS
  'ประเภทเอกสาร: IV=ใบขาย, RT=ใบคืน, CN=ใบลดหนี้, DN=ใบเพิ่มหนี้ ใช้จัดกลุ่มและกำหนดเครื่องหมายยอด';

COMMENT ON COLUMN KMPROD.EXP$ERP_SALE_REP_EXP.QTY1 IS
  'จำนวนสินค้า ใช้รวมยอดจำนวน อย่าใช้เป็นมูลค่าเงิน';

COMMENT ON COLUMN KMPROD.EXP$ERP_SALE_REP_EXP.ITEM_AMT1 IS
  'มูลค่ารายการสินค้า หน่วยบาท ใช้เป็นฐานยอดขายก่อนกลับเครื่องหมายใบคืนหรือใบลดหนี้';

COMMENT ON COLUMN KMPROD.EXP$ERP_SALE_REP_EXP.CANCEL IS
  'สถานะยกเลิก: Y=ยกเลิก ไม่นับในยอดขาย, N=เอกสารปกติ ต้องกรอง CANCEL = ''N'' ทุกครั้งที่วิเคราะห์ยอด';

COMMENT ON COLUMN KMPROD.EXP$ERP_SALE_REP_EXP.ZONE_NAME IS
  'พื้นที่ขายหรือเขต ใช้เป็นมิติกลุ่มตามประเทศหรือโซน ใช้กรองและ GROUP BY ได้';
