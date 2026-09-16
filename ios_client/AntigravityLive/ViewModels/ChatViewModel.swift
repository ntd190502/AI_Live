import Foundation
import SwiftUI
import Combine

class ChatViewModel: ObservableObject, WebSocketServiceDelegate {
    @Published var messages: [ChatMessage] = []
    @Published var inputText: String = ""
    @Published var isSending: Bool = false
    @Published var currentStatus: String = ""
    @Published var selectedImage: UIImage?
    
    private let wsService = WebSocketService.shared
    private var currentAgentMessageId: UUID?
    
    init() {
        // Welcome message
        messages.append(ChatMessage(
            sender: .agent,
            text: "Chào mày! Tao là Antigravity đây. Có chuyện gì cần tao giải quyết hay sai vặt trên PC không?"
        ))
    }
    
    func bindWebSocket() {
        wsService.addListener(self)
        if !wsService.isConnected {
            wsService.connect()
        }
    }
    
    func sendMessage() {
        let trimmed = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed.isEmpty && selectedImage == nil { return }
        
        let userMsg = ChatMessage(
            sender: .user,
            text: trimmed,
            image: selectedImage
        )
        messages.append(userMsg)
        
        // Prepare thinking bubble for agent
        let agentMsg = ChatMessage(
            sender: .agent,
            text: "",
            isThinking: true
        )
        messages.append(agentMsg)
        currentAgentMessageId = agentMsg.id
        
        isSending = true
        currentStatus = "Đang gửi lên PC..."
        
        if let img = selectedImage {
            wsService.sendImageMessage(image: img, text: trimmed)
            selectedImage = nil
        } else {
            wsService.sendTextMessage(trimmed)
        }
        
        inputText = ""
    }
    
    func clearMessages() {
        messages.removeAll()
        wsService.resetSession()
        messages.append(ChatMessage(
            sender: .system,
            text: "Đã làm mới toàn bộ lịch sử trò chuyện."
        ))
    }
    
    // MARK: - WebSocketServiceDelegate
    func webSocketDidConnect() {
        currentStatus = "Đã kết nối PC"
    }
    
    func webSocketDidDisconnect(error: Error?) {
        currentStatus = "Mất kết nối PC"
        isSending = false
    }
    
    func webSocketDidReceiveStatus(_ status: String) {
        currentStatus = status
    }
    
    func webSocketDidReceiveTextDelta(_ delta: String) {
        guard let id = currentAgentMessageId,
              let idx = messages.firstIndex(where: { $0.id == id }) else { return }
        
        messages[idx].isThinking = false
        messages[idx].text += delta
    }
    
    func webSocketDidReceiveVoiceChunk(audioData: Data, fullText: String) {
        guard let id = currentAgentMessageId,
              let idx = messages.firstIndex(where: { $0.id == id }) else { return }
        
        messages[idx].audioData = audioData
        if messages[idx].text.isEmpty {
            messages[idx].text = fullText
        }
    }
    
    func webSocketDidReceiveScreenshot(image: UIImage, caption: String) {
        messages.append(ChatMessage(
            sender: .agent,
            text: caption.isEmpty ? "📸 Ảnh chụp màn hình từ PC Windows:" : caption,
            image: image
        ))
    }
    
    func webSocketDidReceiveToolOutput(tool: String, output: String) {
        currentStatus = "⚡ Xong công cụ: \(tool)"
    }
    
    func webSocketDidCompleteTurn(fullText: String) {
        if let id = currentAgentMessageId,
           let idx = messages.firstIndex(where: { $0.id == id }) {
            messages[idx].isThinking = false
            if messages[idx].text.isEmpty {
                messages[idx].text = fullText
            }
        }
        currentAgentMessageId = nil
        isSending = false
        currentStatus = "Sẵn sàng"
    }
    
    func webSocketDidReceiveError(_ message: String) {
        messages.append(ChatMessage(
            sender: .system,
            text: "⚠️ Lỗi: \(message)"
        ))
        currentAgentMessageId = nil
        isSending = false
        currentStatus = "Lỗi"
    }
}
