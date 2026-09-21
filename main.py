import json
import os
from typing import Literal
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field 

load_dotenv()
client = OpenAI(base_url=os.getenv("OPENAI_BASE_URL"),api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL")

# Dinh nghia schema
class IssueTriage(BaseModel):
    status: Literal["classified","insufficient_data","out_of_scope"]
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
                    "alert_message": {"type": "string", "description": "Nội dung cảnh báo ngắn gọn"}
                },
                "required" : ["component", "severity", "alert_message"]
            }
        }
    }
]

def execute_notify_oncall(component: str, severity: str, alert_message: str, **kwargs) -> dict:
    return{
        "status": "success",
        "delivered_to": "team-core-oncall",
        "details": f"[{severity}] Cảnh báo cho {component}: {alert_message}"
    }


SYSTEM_PROMPT = """
Bạn là một AI Triage Bot chuyên trách phân loại sự cố kỹ thuật và kích hoạt phản ứng khẩn cấp.

TIÊU CHUẨN XÁC ĐỊNH MỨC ĐỘ (SEVERITY):
- P0 (Blocker/Critical): Hệ thống ngừng hoạt động, sập dịch vụ cốt lõi, lỗi cổng thanh toán (HTTP 500, treo giao dịch), rò rỉ dữ liệu hoặc ảnh hưởng toàn bộ người dùng.
- P1 (High): Một tính năng chính bị tê liệt nhưng có giải pháp tạm thời, hoặc ảnh hưởng một nhóm lớn người dùng.
- P2 (Medium): Lỗi ảnh hưởng trải nghiệm người dùng nhưng nghiệp vụ chính vẫn hoạt động.
- P3 (Low): Lỗi giao diện (UI), sai chính tả, gợi ý tính năng mới.

QUY TRÌNH XỬ LÝ (BẮT BUỘC THEO THỨ TỰ):
Bước 1: Đánh giá nhanh mức độ sự cố.
Bước 2: NẾU XÁC ĐỊNH LÀ P0 HOẶC P1:
  - BẮT BUỘC PHẢI GỌI TOOL `notify_oncall_team` TRƯỚC TIÊN.
  - TUYỆT ĐỐI KHÔNG xuất ra văn bản hay phân tích trực tiếp nếu chưa gọi tool này.
Bước 3: Nếu là P2, P3, hoặc issue thiếu dữ liệu/ngoài phạm vi:
  - KHÔNG gọi tool.

QUY TẮC TRẠNG THÁI:
- status = "classified": Issue có dịch vụ hoặc lỗi rõ ràng.
- status = "insufficient_data": Chỉ dùng khi issue quá ngắn hoặc mơ hồ (ví dụ: "lỗi rồi", "hỏng app").
- status = "out_of_scope": Không liên quan đến kỹ thuật phần mềm.
"""

def main():
    user_issue = input("Nhập mô tả sự cố (Issue description): ")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Issue input:\n{user_issue}\n"}
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    if tool_calls:
        messages.append(response_message)
        
        for tool_call in tool_calls:
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)

            print("\n[TRACE 1: tool_call]")
            print(f"Model yêu cầu gọi hàm: {func_name}")
            print(f"Đối số: {func_args}")

            if func_name == "notify_oncall_team":
                tool_output = execute_notify_oncall(**func_args)
                print("\n[TRACE 2: application executes]")
                print(f"Ứng dụng đã xử lý xong tool.")

                print("\n[TRACE 3: tool_result]")
                print(f"Kết quả trả về cho model: {tool_output}")

    final_completion = client.beta.chat.completions.parse(
        model=MODEL,
        messages=messages,
        response_format=IssueTriage
    )

    triage_result: IssueTriage = final_completion.choices[0].message.parsed

    print("\n[TRACE 4: final response]")
    print("Type object:", type(triage_result))
    print(triage_result.model_dump_json(indent=2))

if __name__ == "__main__":
    main()