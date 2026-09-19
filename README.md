# Issue Triage App

Ứng dụng tự động tiếp nhận và phân loại sự cố phần mềm sử dụng mô hình ngôn ngữ lớn (LLM), kết hợp gọi công cụ tự động và kiểm thực dữ liệu đầu ra có cấu trúc.

## Tính Năng

- **Phân loại sự cố:** Đánh giá mức độ nghiêm trọng, xác định thành phần ảnh hưởng và đưa ra lý do phân loại dựa trên nội dung mô tả lỗi.
- **Cảnh báo tự động:** Tự động kích hoạt cơ chế báo động đến đội trực kỹ thuật khi phát hiện các sự cố nghiêm trọng hoặc khẩn cấp.
- **Đảm bảo chuẩn dữ liệu:** Ép kiểu và kiểm tra tính hợp lệ của dữ liệu đầu ra ngay tại ứng dụng theo schema định sẵn.
- **Theo dõi luồng xử lý:** Ghi nhận và hiển thị từng bước thực thi từ lúc mô hình phát yêu cầu gọi công cụ, ứng dụng xử lý nội bộ, trả kết quả cho mô hình cho đến phản hồi cuối cùng.
