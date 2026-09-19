import json
import os
from typing import Literal
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field 

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class IssueTriage(BaseModel):
    status: Literal["classified","insufficent_data","out_of_scope"]
    severity: Literal["P0","P1","P2","P3"] | None = None
    component: str | None=None
    needs_urgent_response: bool = False
    reason: str = Field(description="Lý do ngắn gọn dựa trên dữ liệu issue")

    
