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
    
    private var listeners = NSHashTable<AnyObject>.weakObjects()
    private var webSocketTask: URLSessionWebSocketTask?
    private var urlSession: URLSession?
    private var pingTimer: Timer?
    private(set) var isConnected: Bool = false
    
    private override init() {
        super.init()
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 120.0
        config.timeoutIntervalForResource = 600.0
        config.waitsForConnectivity = true
        self.urlSession = URLSession(configuration: config, delegate: self, delegateQueue: OperationQueue())
    }
    
    func addListener(_ listener: WebSocketServiceDelegate) {
        listeners.add(listener as AnyObject)
    }
    
    func removeListener(_ listener: WebSocketServiceDelegate) {
        listeners.remove(listener as AnyObject)
    }
    
    private func notifyListeners(_ action: @escaping (WebSocketServiceDelegate) -> Void) {
        DispatchQueue.main.async {
            for item in self.listeners.allObjects {
                if let listener = item as? WebSocketServiceDelegate {
                    action(listener)
                }
            }
        }
    }
    
    func connect() {
        if isConnected && webSocketTask != nil {
            return // Already connected, avoid reconnecting
        }
        
        disconnect()
        
        guard let url = AppConfig.wsLiveURL else {
            notifyListeners { $0.webSocketDidReceiveError("Địa chỉ WebSocket không hợp lệ!") }
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
    
    func cancelCurrentTurn() {
        let payload: [String: Any] = [
            "type": "cancel"
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
                    self.notifyListeners { $0.webSocketDidDisconnect(error: error) }
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
        
        switch type {
        case "status":
            let text = obj["text"] as? String ?? ""
            notifyListeners { $0.webSocketDidReceiveStatus(text) }
            
        case "text_delta":
            let delta = obj["delta"] as? String ?? ""
            notifyListeners { $0.webSocketDidReceiveTextDelta(delta) }
            
        case "tool_executed":
            let tool = obj["tool"] as? String ?? ""
            let output = obj["output"] as? String ?? ""
            notifyListeners { $0.webSocketDidReceiveToolOutput(tool: tool, output: output) }
            
        case "voice_chunk":
            if let b64 = obj["audio_b64"] as? String,
               let audioData = Data(base64Encoded: b64) {
                let fullText = obj["full_text"] as? String ?? ""
                notifyListeners { $0.webSocketDidReceiveVoiceChunk(audioData: audioData, fullText: fullText) }
            }
            
        case "screenshot":
            if let b64 = obj["image_b64"] as? String,
               let imgData = Data(base64Encoded: b64),
               let image = UIImage(data: imgData) {
                let caption = obj["caption"] as? String ?? ""
                notifyListeners { $0.webSocketDidReceiveScreenshot(image: image, caption: caption) }
            }
            
        case "turn_complete":
            let fullText = obj["full_text"] as? String ?? ""
            notifyListeners { $0.webSocketDidCompleteTurn(fullText: fullText) }
            
        case "ping", "pong":
            // Heartbeat packet from server, socket is alive
            break
            
        case "error":
            let msg = obj["message"] as? String ?? "Lỗi không xác định"
            notifyListeners { $0.webSocketDidReceiveError(msg) }
            
        default:
            break
        }
    }
    
    private func startHeartbeat() {
        pingTimer?.invalidate()
        let timer = Timer(timeInterval: 5.0, repeats: true) { [weak self] _ in
            self?.webSocketTask?.sendPing { error in
                if let error = error {
                    print("[WebSocket] Ping error: \(error.localizedDescription)")
                }
            }
        }
        RunLoop.main.add(timer, forMode: .common)
        self.pingTimer = timer
    }
    
    private func stopHeartbeat() {
        pingTimer?.invalidate()
        pingTimer = nil
    }
    
    // MARK: - URLSessionWebSocketDelegate
    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didOpenWithProtocol protocol: String?) {
        DispatchQueue.main.async {
            self.isConnected = true
            self.notifyListeners { $0.webSocketDidConnect() }
        }
    }
    
    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didCloseWith closeCode: URLSessionWebSocketTask.CloseCode, reason: Data?) {
        DispatchQueue.main.async {
            self.isConnected = false
            self.notifyListeners { $0.webSocketDidDisconnect(error: nil) }
        }
    }
}
