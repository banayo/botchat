from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from database import get_db_connection
from mock_data import setup_mock_database
from routers import sales, inventory, data_chat
app = FastAPI(title="Assistant API")

app.include_router(inventory.router)
app.include_router(sales.router)
app.include_router(data_chat.router)

@app.get("/")
def read_root():
    return {"message": "API Server is running!"}