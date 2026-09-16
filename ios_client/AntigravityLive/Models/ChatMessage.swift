import Foundation
import UIKit

enum MessageSender {
    case user
    case agent
    case system
}

struct ChatMessage: Identifiable, Equatable {
    let id: UUID
    let sender: MessageSender
    var text: String
    let timestamp: Date
    var image: UIImage?
    var audioData: Data?
    var isThinking: Bool
    
    init(
        id: UUID = UUID(),
        sender: MessageSender,
        text: String,
        timestamp: Date = Date(),
        image: UIImage? = nil,
        audioData: Data? = nil,
        isThinking: Bool = false
    ) {
        self.id = id
        self.sender = sender
        self.text = text
        self.timestamp = timestamp
        self.image = image
        self.audioData = audioData
        self.isThinking = isThinking
    }
    
    static func == (lhs: ChatMessage, rhs: ChatMessage) -> Bool {
        return lhs.id == rhs.id && lhs.text == rhs.text && lhs.isThinking == rhs.isThinking
    }
}
