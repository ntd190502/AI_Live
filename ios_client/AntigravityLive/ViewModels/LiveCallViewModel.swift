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
    @Published var isHandsFreeMode: Bool = false
    
    let audioEngine = AudioEngineManager()
    private let wsService = WebSocketService.shared
    private var cancellables = Set<AnyCancellable>()
    
    init() {
        wsService.addListener(self)
        if wsService.isConnected {
            callState = .idle
            statusSubtitle = "Sẵn sàng"
        }
        
        // Sync audio levels from engine to UI
        audioEngine.$audioLevel
            .receive(on: DispatchQueue.main)
            .assign(to: \.audioLevel, on: self)
            .store(in: &cancellables)
            
        // Voice Activity Detection (VAD) Callback for 1vs1 Hands-Free Mode
        audioEngine.onVADDetectedEndOfSpeech = { [weak self] in
            guard let self = self else { return }
            if self.callState == .listening {
                print("[LiveCallVM] VAD nhận diện dứt câu -> Tự động gửi thoại lên PC.")
                self.finishTalkingAndSend()
            }
        }
            
        // Handle app returning to foreground
        NotificationCenter.default.publisher(for: UIApplication.willEnterForegroundNotification)
            .receive(on: DispatchQueue.main)
            .sink { [weak self] _ in
                guard let self = self else { return }
                if !self.wsService.isConnected {
                    self.statusSubtitle = "Đang kết nối lại PC..."
                    self.wsService.reconnectIfDisconnected()
                } else {
                    self.wsService.requestSync()
                }
            }
            .store(in: &cancellables)
    }
    
    func onAppear() {
        wsService.addListener(self)
        if wsService.isConnected {
            if callState == .disconnected {
                callState = .idle
                statusSubtitle = "Sẵn sàng. Giữ nút để nói."
            }
            wsService.requestSync()
        } else {
            connect()
        }
    }
    
    func toggleHandsFreeMode() {
        isHandsFreeMode.toggle()
        audioEngine.isVADEnabled = isHandsFreeMode
        
        if isHandsFreeMode {
            statusSubtitle = "Đã BẬT Đàm Thoại 1vs1 Rảnh Tay! Mở miệng là nói được ngay."
            if callState == .idle && wsService.isConnected {
                startTalking()
            }
        } else {
            statusSubtitle = "Đã TẮT Đàm Thoại Rảnh Tay. Dùng phím bấm như bình thường."
            if callState == .listening {
                audioEngine.stopRecording()
                callState = .idle
            }
        }
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
        if !wsService.isConnected {
            wsService.reconnectIfDisconnected()
            statusSubtitle = "Đang kết nối lại PC... Hãy thử lại sau giây lát."
            return
        }
        
        // If AI is currently speaking or thinking, interrupt immediately (Barge-in)
        if audioEngine.isPlaying || callState == .speaking || callState == .thinking {
            audioEngine.stopPlayback()
            wsService.cancelCurrentTurn()
        }
        
        lastTranscript = ""
        audioEngine.startRecording()
        callState = .listening
        statusSubtitle = isHandsFreeMode ? "Đang lắng nghe... (Dừng nói 0.8s để tự gửi)" : "Hãy nói gì đó với Antigravity..."
    }
    
    func finishTalkingAndSend() {
        guard audioEngine.isRecording else { return }
        
        guard let audioData = audioEngine.stopRecording() else {
            callState = .idle
            statusSubtitle = "Chạm quá nhanh. Hãy nói rõ ràng hơn!"
            return
        }
        
        if !wsService.isConnected {
            callState = .disconnected
            statusSubtitle = "Mất kết nối PC. Không thể gửi âm thanh!"
            wsService.reconnectIfDisconnected()
            return
        }
        
        callState = .thinking
        statusSubtitle = "Đang gửi âm thanh lên PC..."
        wsService.sendVoiceAudio(audioData: audioData, isLiveCall: true)
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
        if callState != .speaking && callState != .thinking {
            callState = .idle
            statusSubtitle = isHandsFreeMode ? "Đã kết nối! Đang ở chế độ rảnh tay 1vs1." : "Đã kết nối! Bấm giữ nút để nói chuyện."
            if isHandsFreeMode {
                startTalking()
            }
        }
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
                guard let self = self else { return }
                self.callState = .idle
                
                // If in Hands-Free 1vs1 mode, immediately open the mic for the next user turn!
                if self.isHandsFreeMode && self.wsService.isConnected {
                    self.statusSubtitle = "Đang đón câu nói tiếp theo của mày..."
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) {
                        if self.isHandsFreeMode && self.callState == .idle {
                            self.startTalking()
                        }
                    }
                } else {
                    self.statusSubtitle = "Đã xong lượt thoại. Tiếp tục nói nào!"
                }
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
        if !fullText.isEmpty {
            lastTranscript = fullText
        }
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
