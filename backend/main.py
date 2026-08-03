from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import marketing, online, auth

app = FastAPI(title="Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(data_chat.router)
app.include_router(marketing.router)
app.include_router(online.router)
app.include_router(auth.router)

@app.get("/")
def read_root():
    return {"message": "API Server is running!"}