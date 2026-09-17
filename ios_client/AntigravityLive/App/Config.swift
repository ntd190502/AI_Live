import Foundation
import SwiftUI

extension Color {
    // Backport Color.cyan for iOS 14.0+ compatibility
    static let cyan = Color(red: 0.0, green: 0.78, blue: 0.95)
}

struct AppConfig {
    static let appName = "Antigravity Live"
    static let appVersion = "1.0.0"
    
    // Default Server IP & Port (Can be modified inside Settings in the app)
    static let defaultServerHostKey = "server_host"
    static let defaultServerPortKey = "server_port"
    static let defaultSessionIdKey = "session_id"
    
    static var serverHost: String {
        get {
            UserDefaults.standard.string(forKey: defaultServerHostKey) ?? "192.168.1.100"
        }
        set {
            UserDefaults.standard.set(newValue, forKey: defaultServerHostKey)
        }
    }
    
    static var serverPort: Int {
        get {
            let port = UserDefaults.standard.integer(forKey: defaultServerPortKey)
            return port > 0 ? port : 8000
        }
        set {
            UserDefaults.standard.set(newValue, forKey: defaultServerPortKey)
        }
    }
    
    static var sessionId: String {
        get {
            UserDefaults.standard.string(forKey: defaultSessionIdKey) ?? "ios_trollstore_user"
        }
        set {
            UserDefaults.standard.set(newValue, forKey: defaultSessionIdKey)
        }
    }
    
    static var httpBaseURL: String {
        return "http://\(serverHost):\(serverPort)"
    }
    
    static var wsLiveURL: URL? {
        var components = URLComponents(string: "ws://\(serverHost):\(serverPort)/ws/live")
        components?.queryItems = [
            URLQueryItem(name: "session_id", value: sessionId)
        ]
        return components?.url ?? URL(string: "ws://\(serverHost):\(serverPort)/ws/live?session_id=\(sessionId)")
    }
}
