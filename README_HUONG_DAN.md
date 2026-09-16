# HƯỚNG DẪN CÀI ĐẶT VÀ SỬ DỤNG ANTIGRAVITY LIVE TRÊN IOS (TROLLSTORE)

Thư mục dự án độc lập: `D:\install\CODE\AntigravityTelegramBot\AI_LIVE`

Toàn bộ hệ thống được thiết kế độc lập 100%, không làm ảnh hưởng đến bot Telegram gốc đang chạy trên máy tính.

---

## 1. Cấu Trúc Thư Mục `AI_LIVE`

- `gateway_server.py`: Máy chủ FastAPI & WebSocket trung tâm, kết nối thẳng vào trí tuệ AI và các công cụ điều khiển PC Windows của `agent_core.py`.
- `run_gateway.bat`: File kích hoạt server chỉ bằng 1 cú nhấp chuột (cổng mặc định `8000`).
- `ios_client/`: Toàn bộ mã nguồn Swift & SwiftUI của ứng dụng iOS Native:
  - Tab **Live Call**: Giao diện đàm thoại thời gian thực, có sóng âm visualizer bập bùng, giọng nói Hoài My (`vi-VN-HoaiMyNeural`).
  - Tab **Tin Nhắn**: Chat bong bóng, gửi text, gửi hình ảnh, xem ảnh chụp màn hình máy tính gửi về.
  - Tab **Cài Đặt**: Cấu hình IP tĩnh và Port linh hoạt ngay trên app.
- `.github/workflows/build_ipa.yml`: Kịch bản tự động build file `AntigravityLive.ipa` trên máy chủ Mac của GitHub.

---

## 2. Cách Tạo File `.ipa` Bằng GitHub Actions (Không Cần Máy Mac)

Chỉ cần 3 bước đẩy code lên GitHub:

1. **Tạo một Repository mới trên GitHub**:
   - Truy cập https://github.com/new, đặt tên repo (ví dụ: `AntigravityLiveIOS`).
   - Chọn chế độ **Public** hoặc **Private** tùy ý.

2. **Đẩy thư mục `AI_LIVE` lên repo**:
   - Mở PowerShell tại thư mục `D:\install\CODE\AntigravityTelegramBot\AI_LIVE` và chạy các lệnh:
   ```bash
   git init
   git add .
   git commit -m "Initial commit Antigravity Live iOS"
   git branch -M main
   git remote add origin <URL_REPO_GITHUB_CUA_BAN>
   git push -u origin main
   ```

3. **Lấy file `.ipa`**:
   - Vào tab **Actions** trên GitHub repository vừa đẩy.
   - Bạn sẽ thấy workflow `Build iOS IPA for TrollStore` đang tự động chạy (mất khoảng 2-3 phút).
   - Khi chạy xong hiện dấu tích xanh ✅, bấm vào đó và cuộn xuống mục **Artifacts**, tải file `AntigravityLive-TrollStore-IPA.zip` về (bên trong có chứa file `AntigravityLive.ipa`).

---

## 3. Cài Đặt Lên iPhone Qua TrollStore

1. Dùng trình duyệt **Safari** trên iPhone truy cập GitHub tải file zip hoặc file `.ipa` về máy.
2. Bấm vào file `.ipa` đã tải -> Chọn nút **Chia sẻ (Share)** -> Chọn **Open in TrollStore** (hoặc mở TrollStore bấm dấu `+` chọn file).
3. Bấm **Install**. Ứng dụng **Antigravity Live** sẽ xuất hiện ngay trên màn hình chính iPhone của bạn, **dùng vĩnh viễn không bao giờ hết hạn chứng chỉ**!

---

## 4. Chạy Hệ Thống Khi Bạn Muốn Dùng

1. **Trên PC Windows**:
   - Khi nào muốn dùng app trên điện thoại, bạn chỉ cần nhấp đúp vào file `run_gateway.bat` trong thư mục `AI_LIVE`.
   - Cửa sổ server hiện thông báo:
     ```
     🚀 Antigravity Live Gateway đang khởi động...
     🌐 Lắng nghe trên: http://0.0.0.0:8000
     📡 WebSocket Live Endpoint: ws://0.0.0.0:8000/ws/live
     ```

2. **Trên iPhone**:
   - Mở app **Antigravity Live**.
   - Vào tab **Cài Đặt** -> Điền IP tĩnh của bạn và Port `8000`.
   - Bấm **Kiểm tra kết nối tới PC** -> Thấy báo `Thành công (200 OK)` là thông luồng.
   - Chuyển sang tab **Live Call**: Bấm giữ nút tròn màu xanh ngọc ở giữa và nói tiếng Việt tự nhiên (ví dụ: *"Kiểm tra xem máy tính đang tải game gì"*, *"Chụp màn hình máy tính gửi cho tao"*...).
   - Nhả tay ra, trợ lý Hoài My sẽ tự động suy nghĩ, thực thi lệnh trên PC và phát giọng nói trả lời trực tiếp qua loa ngoài iPhone!
