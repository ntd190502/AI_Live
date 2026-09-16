import SwiftUI

struct SettingsView: View {
    @AppStorage(AppConfig.defaultServerHostKey) private var serverHost = "192.168.1.100"
    @AppStorage(AppConfig.defaultServerPortKey) private var serverPort = 8000
    @AppStorage(AppConfig.defaultSessionIdKey) private var sessionId = "ios_trollstore_user"
    
    @State private var connectionStatus: String = "Chưa kiểm tra"
    @State private var isTesting: Bool = false
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Cấu Hình Kết Nối PC Gateway")) {
                    HStack {
                        Text("IP Tĩnh / Host:")
                            .frame(width: 110, alignment: .leading)
                        TextField("Nhập IP tĩnh của bạn", text: $serverHost)
                            .keyboardType(.numbersAndPunctuation)
                            .autocapitalization(.none)
                            .disableAutocorrection(true)
                    }
                    
                    HStack {
                        Text("Cổng (Port):")
                            .frame(width: 110, alignment: .leading)
                        TextField("8000", value: $serverPort, formatter: NumberFormatter())
                            .keyboardType(.numberPad)
                    }
                    
                    HStack {
                        Text("Mã phiên:")
                            .frame(width: 110, alignment: .leading)
                        TextField("ios_trollstore_user", text: $sessionId)
                            .autocapitalization(.none)
                            .disableAutocorrection(true)
                    }
                }
                
                Section(header: Text("Kiểm Tra Đường Truyền")) {
                    HStack {
                        Button(action: testConnection) {
                            if isTesting {
                                HStack {
                                    ProgressView()
                                        .padding(.trailing, 4)
                                    Text("Đang ping...")
                                }
                            } else {
                                Text("Kiểm tra kết nối tới PC")
                                    .fontWeight(.medium)
                            }
                        }
                        .disabled(isTesting)
                        
                        Spacer()
                        
                        Text(connectionStatus)
                            .font(.system(size: 13))
                            .foregroundColor(connectionStatus.contains("Thành công") ? .green : (connectionStatus.contains("Lỗi") ? .red : .gray))
                    }
                }
                
                Section(header: Text("Thông Tin Ứng Dụng")) {
                    HStack {
                        Text("Tên ứng dụng")
                        Spacer()
                        Text(AppConfig.appName)
                            .foregroundColor(.gray)
                    }
                    HStack {
                        Text("Phiên bản")
                        Spacer()
                        Text(AppConfig.appVersion)
                            .foregroundColor(.gray)
                    }
                    HStack {
                        Text("Môi trường cài")
                        Spacer()
                        Text("TrollStore (Vĩnh viễn)")
                            .foregroundColor(.cyan)
                    }
                    HStack {
                        Text("Mô hình AI")
                        Spacer()
                        Text("Gemini 3.8 Flash (PC)")
                            .foregroundColor(.gray)
                    }
                }
            }
            .navigationTitle("Cài Đặt")
        }
    }
    
    private func testConnection() {
        isTesting = true
        connectionStatus = "Đang kiểm tra..."
        
        let urlStr = "http://\(serverHost):\(serverPort)/health"
        guard let url = URL(string: urlStr) else {
            connectionStatus = "Lỗi: URL không hợp lệ"
            isTesting = false
            return
        }
        
        var request = URLRequest(url: url)
        request.timeoutInterval = 5.0
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                isTesting = false
                if let error = error {
                    connectionStatus = "Lỗi: \(error.localizedDescription)"
                    return
                }
                
                if let httpResp = response as? HTTPURLResponse, httpResp.statusCode == 200 {
                    connectionStatus = "Thành công (200 OK)!"
                    // Reconnect WebSocket with new config
                    WebSocketService.shared.connect()
                } else {
                    connectionStatus = "Lỗi máy chủ trả về mã khác 200"
                }
            }
        }.resume()
    }
}
