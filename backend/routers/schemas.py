from pydantic import BaseModel
from typing import List, Dict, Any

class UserContext(BaseModel):
    name: str
    email: str
    role: str                  
    group: str
    division: str
    department: str

class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]
    user_context: UserContext