import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    '''
    สร้างการเชื่อมต่อกับ PostgreSQL Database
    '''
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "db"),
            database=os.getenv("POSTGRES_DB", "enterprise_ai"),
            user=os.getenv("POSTGRES_USER", "admin"),
            password=os.getenv("POSTGRES_PASSWORD", "admin"),
            port=os.getenv("POSTGRES_PORT", "5432")
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None
# 0.6
def get_sales_db_connection():
    '''
    สร้างการเชื่อมต่อกับ PostgreSQL Database ยอดขาย06
    '''
    try:
        conn = psycopg2.connect(
            host=os.getenv("SALES_DB_HOST"),
            database=os.getenv("SALES_DB_NAME"),
            user=os.getenv("SALES_DB_USER"),
            password=os.getenv("SALES_DB_PASSWORD"),
            port=os.getenv("SALES_DB_PORT")
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None
  #ใช้กับ LangChain SQL Agent      
def get_sales_langchain_db_uri():
    db_user = os.getenv("SALES_DB_USER")
    db_password = os.getenv("SALES_DB_PASSWORD")
    db_host = os.getenv("SALES_DB_HOST")
    db_port = os.getenv("SALES_DB_PORT")
    db_name = os.getenv("SALES_DB_NAME")
    
    return f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"                