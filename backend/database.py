import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_oracle_langchain_db_uri():
    oracle_user = os.getenv("ORACLE_USER")
    oracle_password = urllib.parse.quote_plus(os.getenv("ORACLE_PASSWORD", ""))
    oracle_host = os.getenv("ORACLE_HOST")
    oracle_port = os.getenv("ORACLE_PORT", "1521")
    oracle_service = os.getenv("ORACLE_SERVICE")
    oracle_uri = f"oracle+oracledb://{oracle_user}:{oracle_password}@{oracle_host}:{oracle_port}/?service_name={oracle_service}"
    return oracle_uri



  #ใช้กับ LangChain SQL Agent 006     
def get_sales_langchain_db_uri():
    db_user = os.getenv("SALES_DB_USER")
    db_password = os.getenv("SALES_DB_PASSWORD")
    db_host = os.getenv("SALES_DB_HOST")
    db_port = os.getenv("SALES_DB_PORT")
    db_name = os.getenv("SALES_DB_NAME")
    
    return f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"   