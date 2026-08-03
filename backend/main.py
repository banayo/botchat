from fastapi import FastAPI
from routers import  marketing,online
app = FastAPI(title="Assistant API")

app.include_router(marketing.router)
app.include_router(online.router)
@app.get("/")
def read_root():
    return {"message": "API Server is running!"}