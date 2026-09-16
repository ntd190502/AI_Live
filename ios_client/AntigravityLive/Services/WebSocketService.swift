import Foundation
import UIKit

protocol WebSocketServiceDelegate: AnyObject {
    func webSocketDidConnect()
    func webSocketDidDisconnect(error: Error?)
    func webSocketDidReceiveStatus(_ status: String)
    func webSocketDidReceiveTextDelta(_ delta: String)
    func webSocketDidReceiveVoiceChunk(audioData: Data, fullText: String)
    func webSocketDidReceiveScreenshot(image: UIImage, caption: String)
    func webSocketDidReceiveToolOutput(tool: String, output: String)
    func webSocketDidCompleteTurn(fullText: String)
    func webSocketDidReceiveError(_ message: String)
}

class WebSocketService: NSObject, URLSessionWebSocketDelegate {
    static let shared = WebSocketService()
    
    weak var delegate: WebSocketServiceDelegate?
    
    private var webSocketTask: URLSessionWebSocketTask?
    private var urlSession: URLSession?
    private var pingTimer: Timer?
    private(set) var isConnected: Bool = false
    
    private override init() {
        super.init()
        let config = URLSessionConfiguration.default
        self.urlSession = URLSession(configuration: config, delegate: self, delegateQueue: OperationQueue())
    }
    
    func connect() {
        disconnect()
        
        guard let url = AppConfig.wsLiveURL else {
            delegate?.webSocketDidReceiveError("Địa chỉ WebSocket không hợp lệ!")
            return
        }
        
        webSocketTask = urlSession?.webSocketTask(with: url)
        webSocketTask?.resume()
        
        listenForMessages()
        startHeartbeat()
    }
    
    func disconnect() {
        stopHeartbeat()
        webSocketTask?.cancel(with: .goingAway, reason: nil)
        webSocketTask = nil
        isConnected = false
    }
    
    func sendTextMessage(_ text: String, sessionId: String = AppConfig.sessionId) {
        let payload: [String: Any] = [
            "type": "chat_text",
            "session_id": sessionId,
            "text": text,
            "live_call": false
        ]
        sendJSON(payload)
    }
    
    func sendVoiceAudio(audioData: Data, sessionId: String = AppConfig.sessionId, isLiveCall: Bool = true) {
        let b64 = audioData.base64EncodedString()
        let payload: [String: Any] = [
            "type": "voice_audio",
            "session_id": sessionId,
            "audio_b64": b64,
            "mime": "audio/wav",
            "live_call": isLiveCall
        ]
        sendJSON(payload)
    }
    
    func sendImageMessage(image: UIImage, text: String = "", sessionId: String = AppConfig.sessionId) {
        guard let jpegData = image.jpegData(compressionQuality: 0.7) else { return }
        let b64 = jpegData.base64EncodedString()
        let payload: [String: Any] = [
            "type": "chat_text",
            "session_id": sessionId,
            "text": text,
            "image_b64": b64,
            "image_mime": "image/jpeg",
            "live_call": false
        ]
        sendJSON(payload)
    }
    
    func resetSession(sessionId: String = AppConfig.sessionId) {
        let payload: [String: Any] = [
            "type": "reset",
            "session_id": sessionId
        ]
        sendJSON(payload)
    }
    
    private func sendJSON(_ dict: [String: Any]) {
        guard let data = try? JSONSerialization.data(withJSONObject: dict),
              let jsonString = String(data: data, encoding: .utf8) else { return }
        
        let message = URLSessionWebSocketTask.Message.string(jsonString)
        webSocketTask?.send(message) { error in
            if let error = error {
                print("[WebSocket] Send error: \(error.localizedDescription)")
            }
        }
    }
    
    private func listenForMessages() {
        webSocketTask?.receive { [weak self] result in
            guard let self = self else { return }
            
            switch result {
            case .failure(let error):
                DispatchQueue.main.async {
                    self.isConnected = false
                    self.delegate?.webSocketDidDisconnect(error: error)
                }
            case .success(let message):
                switch message {
                case .string(let text):
                    self.handleIncomingJSON(text)
                case .data(let data):
                    if let text = String(data: data, encoding: .utf8) {
                        self.handleIncomingJSON(text)
                    }
                @unknown default:
                    break
                }
                
                // Re-arm listener for continuous stream
                self.listenForMessages()
            }
        }
    }
    
    private func handleIncomingJSON(_ jsonString: String) {
        guard let data = jsonString.data(using: .utf8),
              let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            return
        }
        
        let type = obj["type"] as? String ?? ""
        
        DispatchQueue.main.async {
            switch type {
            case "status":
                let text = obj["text"] as? String ?? ""
                self.delegate?.webSocketDidReceiveStatus(text)
                
            case "text_delta":
                let delta = obj["delta"] as? String ?? ""
                self.delegate?.webSocketDidReceiveTextDelta(delta)
                
            case "tool_executed":
                let tool = obj["tool"] as? String ?? ""
                let output = obj["output"] as? String ?? ""
                self.delegate?.webSocketDidReceiveToolOutput(tool: tool, output: output)
                
            case "voice_chunk":
                if let b64 = obj["audio_b64"] as? String,
                   let audioData = Data(base64Encoded: b64) {
                    let fullText = obj["full_text"] as? String ?? ""
                    self.delegate?.webSocketDidReceiveVoiceChunk(audioData: audioData, fullText: fullText)
                }
                
            case "screenshot":
                if let b64 = obj["image_b64"] as? String,
                   let imgData = Data(base64Encoded: b64),
                   let image = UIImage(data: imgData) {
                    let caption = obj["caption"] as? String ?? ""
                    self.delegate?.webSocketDidReceiveScreenshot(image: image, caption: caption)
                }
                
            case "turn_complete":
                let fullText = obj["full_text"] as? String ?? ""
                self.delegate?.webSocketDidCompleteTurn(fullText: fullText)
                
            case "error":
                let msg = obj["message"] as? String ?? "Lỗi không xác định"
                self.delegate?.webSocketDidReceiveError(msg)
                
            default:
                break
            }
        }
    }
    
    private func startHeartbeat() {
        pingTimer?.invalidate()
        pingTimer = Timer.scheduledTimer(withTimeInterval: 15.0, repeats: true) { [weak self] _ in
            self?.sendJSON(["type": "ping"])
        }
    }
    
    private func stopHeartbeat() {
        pingTimer?.invalidate()
        pingTimer = nil
    }
    
    // MARK: - URLSessionWebSocketDelegate
    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didOpenWithProtocol protocol: String?) {
        DispatchQueue.main.async {
            self.isConnected = true
            self.delegate?.webSocketDidConnect()
        }
    }
    
    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didCloseWith closeCode: URLSessionWebSocketTask.CloseCode, reason: Data?) {
        DispatchQueue.main.async {
            self.isConnected = false
            self.delegate?.webSocketDidDisconnect(error: nil)
        }
    }
}
