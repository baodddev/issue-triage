import json
import os
from typing import Literal
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field 

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Dinh nghia schema
class IssueTriage(BaseModel):
    status: Literal["classified","insufficent_data","out_of_scope"]
    severity: Literal["P0","P1","P2","P3"] | None = None
    component: str | None=None
    needs_urgent_response: bool = False
    reason: str = Field(description="Lý do ngắn gọn dựa trên dữ liệu issue")

# Khai bao tool
tools = [
    {
        "type": "function",
        "function":{
            "name": "notify_oncall_team",
            "description": "Gửi cảnh báo đến đội trực khi phát hiện issue nghiêm trọng (P0/P1 hay needs_urgent_response=True)",
            "parameters":{
                "type": "object",
                "properties":{
                    "component": {"type": "string", "description": "Tên component bị lỗi"},
                    "severity": {"type": "string", "enum": ["P0", "P1", "P2", "P3"]},
                    "alert_messasge": {"type": "string", "description": "Nội dung cảnh báo ngắn gọn"}
                },
                "required" : ["component", "severity", "alert_message"]
            }
        }
    }
]

def execute_notify_oncall(component: str, severity: str, alert_message: str) -> dict:
    return{
        "status": "success",
        "delivered_to": f"team-core-oncall",
        "details": f"[{severity}] Cảnh báo cho {component}: {alert_message}"
    }
