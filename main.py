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
Bạn là một AI Triage Bot chuyên phân loại lỗi hệ thống phần mềm.

ĐIỀU KIỆN TIÊN QUYẾT:
1. Thiếu dữ liệu (insufficient_data):
   - Nếu mô tả quá mơ hồ, ngắn ngủn, thiếu thông tin kỹ thuật/mã lỗi/hành vi tái hiện (dù có từ 'gấp', 'khẩn cấp'):
     -> status = "insufficient_data", severity = None, component = None, needs_urgent_response = False.
     -> TUYỆT ĐỐI KHÔNG GỌI TOOL `notify_oncall_team`.

2. Phân loại & Kích hoạt On-call (classified):
   - Chỉ khi có thông tin lỗi/thành phần kỹ thuật cụ thể -> status = "classified".
   - BẮT BUỘC GỌI TOOL `notify_oncall_team` KHI VÀ CHỈ KHI sự cố là P0/P1 trên production (sập hệ thống, 500 diện rộng, lỗi thanh toán, rò rỉ dữ liệu).

---
VÍ DỤ MẪU (EXAMPLES):

[Ví dụ 1: Insufficient Data - Có từ kích động nhưng thiếu kỹ thuật]
Input: "Web bị lỗi rồi, fix gấp!"
Phân tích: Người dùng giục gấp nhưng không có log, không rõ URL/chức năng nào bị lỗi.
Hành vi: KHÔNG GỌI TOOL.
Kết quả JSON mong đợi:
{
  "status": "insufficient_data",
  "severity": null,
  "component": null,
  "needs_urgent_response": false,
  "reason": "Mô tả quá chung chung, không có thông tin kỹ thuật hay hành vi lỗi cụ thể để xử lý."
}

[Ví dụ 2: Sự cố nghiêm trọng P0 - Đủ dữ liệu & Cần On-call]
Input: "Nút thanh toán trả HTTP 500 với mọi thẻ Visa từ 14:30."
Phân tích: Lỗi cổng thanh toán diện rộng, có mã HTTP 500 và thời gian rõ ràng. Đây là P0.
Hành vi: BẮT BUỘC GỌI TOOL `notify_oncall_team(component='payment', severity='P0', alert_message='HTTP 500 diện rộng trên cổng thanh toán Visa')`.
Kết quả JSON mong đợi:
{
  "status": "classified",
  "severity": "P0",
  "component": "payment",
  "needs_urgent_response": true,
  "reason": "Sự cố HTTP 500 toàn bộ cổng thanh toán thẻ Visa gây gián đoạn doanh thu."
}

[Ví dụ 3: Lỗi nhỏ P3 - Không gọi On-call]
Input: "Sai chính tả chữ 'Xác nhận' ở trang cá nhân."
Phân tích: Lỗi UI/nội dung, không ảnh hưởng vận hành.
Hành vi: KHÔNG GỌI TOOL.
Kết quả JSON mong đợi:
{
  "status": "classified",
  "severity": "P3",
  "component": "profile_ui",
  "needs_urgent_response": false,
  "reason": "Lỗi hiển thị chính tả giao diện người dùng."
}
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