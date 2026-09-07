from pydantic import BaseModel, Field


class MktQuestion(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
