import SwiftUI

struct ChatView: View {
    @StateObject private var viewModel = ChatViewModel()
    @State private var showingImagePicker = false
    @State private var inputImage: UIImage?
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Status Header
                if !viewModel.currentStatus.isEmpty {
                    HStack {
                        Circle()
                            .fill(viewModel.currentStatus.contains("kết nối") ? Color.green : Color.orange)
                            .frame(width: 8, height: 8)
                        Text(viewModel.currentStatus)
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(.gray)
                    }
                    .padding(.vertical, 4)
                }
                
                // Messages Scroll View
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(spacing: 14) {
                            ForEach(viewModel.messages) { msg in
                                MessageBubbleView(message: msg)
                                    .id(msg.id)
                            }
                        }
                        .padding(.horizontal, 16)
                        .padding(.vertical, 12)
                    }
                    .onChange(of: viewModel.messages.count) { _ in
                        if let lastId = viewModel.messages.last?.id {
                            withAnimation {
                                proxy.scrollTo(lastId, anchor: .bottom)
                            }
                        }
                    }
                }
                
                Divider()
                
                // Input Bar
                VStack(spacing: 8) {
                    if let selected = viewModel.selectedImage {
                        HStack {
                            Image(uiImage: selected)
                                .resizable()
                                .scaledToFit()
                                .frame(height: 60)
                                .cornerRadius(8)
                            
                            Spacer()
                            
                            Button(action: {
                                viewModel.selectedImage = nil
                            }) {
                                Image(systemName: "xmark.circle.fill")
                                    .foregroundColor(.gray)
                            }
                        }
                        .padding(.horizontal, 16)
                        .padding(.top, 6)
                    }
                    
                    HStack(spacing: 12) {
                        // Image attachment button
                        Button(action: {
                            showingImagePicker = true
                        }) {
                            Image(systemName: "photo.on.rectangle.angled")
                                .font(.system(size: 22))
                                .foregroundColor(.cyan)
                        }
                        
                        // Text Field
                        TextField("Nhập tin nhắn hoặc ra lệnh PC...", text: $viewModel.inputText)
                            .padding(.horizontal, 14)
                            .padding(.vertical, 10)
                            .background(Color(UIColor.secondarySystemBackground))
                            .cornerRadius(20)
                        
                        // Send Button
                        Button(action: {
                            viewModel.sendMessage()
                        }) {
                            Image(systemName: "arrow.up.circle.fill")
                                .font(.system(size: 32))
                                .foregroundColor(viewModel.inputText.isEmpty && viewModel.selectedImage == nil ? .gray : .cyan)
                        }
                        .disabled(viewModel.inputText.isEmpty && viewModel.selectedImage == nil)
                    }
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                }
                .background(Color(UIColor.systemBackground))
            }
            .navigationTitle("Trò Chuyện AI")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        viewModel.clearMessages()
                    }) {
                        Image(systemName: "trash")
                            .foregroundColor(.gray)
                    }
                }
            }
        }
        .onAppear {
            viewModel.bindWebSocket()
        }
        .sheet(isPresented: $showingImagePicker) {
            ImagePicker(image: $viewModel.selectedImage)
        }
    }
}

struct MessageBubbleView: View {
    let message: ChatMessage
    @State private var isPlayingVoice = false
    @StateObject private var audioPlayer = AudioEngineManager()
    
    var isUser: Bool {
        message.sender == .user
    }
    
    var body: some View {
        HStack(alignment: .bottom, spacing: 8) {
            if isUser { Spacer() }
            
            VStack(alignment: isUser ? .trailing : .leading, spacing: 6) {
                if let img = message.image {
                    Image(uiImage: img)
                        .resizable()
                        .scaledToFit()
                        .frame(maxWidth: 240, maxHeight: 240)
                        .cornerRadius(12)
                }
                
                if message.isThinking && message.text.isEmpty {
                    HStack(spacing: 4) {
                        ProgressView()
                            .scaleEffect(0.8)
                        Text("Antigravity đang xử lý...")
                            .font(.system(size: 14, weight: .regular))
                            .foregroundColor(.gray)
                    }
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(Color(UIColor.secondarySystemBackground))
                    .cornerRadius(16)
                } else if !message.text.isEmpty {
                    Text(message.text)
                        .font(.system(size: 15))
                        .foregroundColor(isUser ? .white : Color(UIColor.label))
                        .padding(.horizontal, 14)
                        .padding(.vertical, 10)
                        .background(isUser ? Color.cyan : Color(UIColor.secondarySystemBackground))
                        .cornerRadius(16)
                }
                
                // Voice note playback button if available
                if let audio = message.audioData {
                    Button(action: {
                        if audioPlayer.isPlaying {
                            audioPlayer.stopPlayback()
                        } else {
                            audioPlayer.playVoiceData(audio)
                        }
                    }) {
                        HStack(spacing: 6) {
                            Image(systemName: audioPlayer.isPlaying ? "stop.fill" : "play.fill")
                            Text("Giọng nói Hoài My")
                                .font(.system(size: 12, weight: .medium))
                        }
                        .padding(.horizontal, 10)
                        .padding(.vertical, 5)
                        .background(Color.purple.opacity(0.2))
                        .foregroundColor(.purple)
                        .cornerRadius(12)
                    }
                }
            }
            
            if !isUser { Spacer() }
        }
    }
}

// Simple UIImagePicker wrapper for SwiftUI
struct ImagePicker: UIViewControllerRepresentable {
    @Binding var image: UIImage?
    @Environment(\.presentationMode) var presentationMode
    
    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        picker.delegate = context.coordinator
        picker.sourceType = .photoLibrary
        return picker
    }
    
    func updateUIViewController(_ uiViewController: UIImagePickerController, context: Context) {}
    
    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }
    
    class Coordinator: NSObject, UIImagePickerControllerDelegate, UINavigationControllerDelegate {
        let parent: ImagePicker
        init(_ parent: ImagePicker) { self.parent = parent }
        
        func imagePickerController(_ picker: UIImagePickerController, didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey : Any]) {
            if let uiImage = info[.originalImage] as? UIImage {
                parent.image = uiImage
            }
            parent.presentationMode.wrappedValue.dismiss()
        }
    }
}
