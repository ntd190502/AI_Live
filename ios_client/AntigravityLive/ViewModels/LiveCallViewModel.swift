import Foundation
import SwiftUI
import Combine

enum LiveCallState: String {
    case disconnected = "Chưa kết nối"
    case idle = "Sẵn sàng"
    case listening = "Đang lắng nghe..."
    case thinking = "Antigravity đang suy nghĩ..."
    case speaking = "Hoài My đang trả lời..."
}

class LiveCallViewModel: ObservableObject, WebSocketServiceDelegate {
    @Published var callState: LiveCallState = .disconnected
    @Published var statusSubtitle: String = ""
    @Published var lastTranscript: String = ""
    @Published var isMuted: Bool = false
    @Published var isSpeakerOn: Bool = true
    @Published var audioLevel: Float = 0.0
    
    let audioEngine = AudioEngineManager()
    private let wsService = WebSocketService.shared
    private var cancellables = Set<AnyCancellable>()
    
    init() {
        wsService.delegate = self
        
        // Sync audio levels from engine to UI
        audioEngine.$audioLevel
            .receive(on: DispatchQueue.main)
            .assign(to: \.audioLevel, on: self)
            .store(in: &cancellables)
    }
    
    func connect() {
        callState = .disconnected
        statusSubtitle = "Đang kết nối tới PC Gateway..."
        wsService.connect()
    }
    
    func disconnect() {
        audioEngine.stopRecording()
        audioEngine.stopPlayback()
        wsService.disconnect()
        callState = .disconnected
        statusSubtitle = "Đã ngắt kết nối"
    }
    
    func startTalking() {
        guard wsService.isConnected else {
            statusSubtitle = "Chưa kết nối tới PC! Kiểm tra lại IP trong Cài đặt."
            return
        }
        
        audioEngine.stopPlayback()
        audioEngine.startRecording()
        callState = .listening
        statusSubtitle = "Hãy nói gì đó với Antigravity..."
    }
    
    func finishTalkingAndSend() {
        guard audioEngine.isRecording else { return }
        
        if let audioData = audioEngine.stopRecording() {
            callState = .thinking
            statusSubtitle = "Đang gửi âm thanh lên PC..."
            wsService.sendVoiceAudio(audioData: audioData, isLiveCall: true)
        } else {
            callState = .idle
            statusSubtitle = "Không thu được âm thanh."
        }
    }
    
    func toggleMute() {
        isMuted.toggle()
        if isMuted {
            audioEngine.stopRecording()
            audioEngine.stopPlayback()
            callState = .idle
            statusSubtitle = "Đã tắt mic."
        }
    }
    
    func resetCallSession() {
        audioEngine.stopPlayback()
        wsService.resetSession()
        lastTranscript = ""
        statusSubtitle = "Đã làm mới phiên gọi."
        callState = .idle
    }
    
    // MARK: - WebSocketServiceDelegate
    func webSocketDidConnect() {
        callState = .idle
        statusSubtitle = "Đã kết nối! Bấm giữ nút để nói chuyện."
    }
    
    func webSocketDidDisconnect(error: Error?) {
        callState = .disconnected
        statusSubtitle = error != nil ? "Mất kết nối: \(error!.localizedDescription)" : "Đã ngắt kết nối."
    }
    
    func webSocketDidReceiveStatus(_ status: String) {
        statusSubtitle = status
    }
    
    func webSocketDidReceiveTextDelta(_ delta: String) {
        lastTranscript += delta
    }
    
    func webSocketDidReceiveVoiceChunk(audioData: Data, fullText: String) {
        callState = .speaking
        lastTranscript = fullText
        statusSubtitle = "Đang phát giọng nói Hoài My..."
        
        audioEngine.playVoiceData(audioData) { [weak self] in
            DispatchQueue.main.async {
                self?.callState = .idle
                self?.statusSubtitle = "Đã xong lượt thoại. Tiếp tục nói nào!"
            }
        }
    }
    
    func webSocketDidReceiveScreenshot(image: UIImage, caption: String) {
        statusSubtitle = "📸 PC đã chụp màn hình Windows và lưu vào chat!"
    }
    
    func webSocketDidReceiveToolOutput(tool: String, output: String) {
        statusSubtitle = "⚡ Thực thi xong: \(tool)"
    }
    
    func webSocketDidCompleteTurn(fullText: String) {
        if !audioEngine.isPlaying {
            callState = .idle
            statusSubtitle = "Sẵn sàng cho câu hỏi tiếp theo."
        }
    }
    
    func webSocketDidReceiveError(_ message: String) {
        statusSubtitle = "⚠️ Lỗi: \(message)"
        callState = .idle
    }
}
