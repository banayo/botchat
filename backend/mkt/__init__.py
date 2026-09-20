import os

VIEW_OWNER = (os.getenv("MKT_VIEW_OWNER") or "KMPROD").strip()
VIEW_NAME = (os.getenv("MKT_VIEW_NAME") or "MKT$ERP_SALE_REP").strip()
QUALIFIED_VIEW = f"{VIEW_OWNER}.{VIEW_NAME}"
AGENT_ROW_CAP = 50
