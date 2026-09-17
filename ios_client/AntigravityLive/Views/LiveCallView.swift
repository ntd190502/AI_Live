import SwiftUI

struct LiveCallView: View {
    @StateObject private var viewModel = LiveCallViewModel()
    @State private var isPressingTalk: Bool = false
    
    var body: some View {
        ZStack {
            // Background gradient
            LinearGradient(
                gradient: Gradient(colors: [
                    Color(red: 0.05, green: 0.07, blue: 0.12),
                    Color(red: 0.10, green: 0.12, blue: 0.20)
                ]),
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()
            
            VStack(spacing: 24) {
                // Top Bar
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("ANTIGRAVITY LIVE")
                            .font(.system(size: 14, weight: .bold, design: .monospaced))
                            .foregroundColor(.cyan)
                        
                        Text(viewModel.callState.rawValue)
                            .font(.system(size: 20, weight: .semibold))
                            .foregroundColor(.white)
                    }
                    
                    Spacer()
                    
                    Button(action: {
                        viewModel.resetCallSession()
                    }) {
                        Image(systemName: "arrow.counterclockwise.circle.fill")
                            .font(.system(size: 24))
                            .foregroundColor(.gray)
                    }
                }
                .padding(.horizontal, 24)
                .padding(.top, 16)
                
                Spacer()
                
                // Audio Wave Visualizer & Glowing Orb
                ZStack {
                    // Outer Pulsating Wave 2
                    Circle()
                        .stroke(Color.cyan.opacity(0.15), lineWidth: 2)
                        .scaleEffect(1.0 + CGFloat(viewModel.audioLevel) * 0.9)
                        .frame(width: 260, height: 260)
                        .animation(.easeOut(duration: 0.1), value: viewModel.audioLevel)
                    
                    // Outer Pulsating Wave 1
                    Circle()
                        .stroke(Color.cyan.opacity(0.3), lineWidth: 3)
                        .scaleEffect(1.0 + CGFloat(viewModel.audioLevel) * 0.6)
                        .frame(width: 210, height: 210)
                        .animation(.easeOut(duration: 0.1), value: viewModel.audioLevel)
                    
                    // Main Glowing Orb
                    Circle()
                        .fill(
                            RadialGradient(
                                gradient: Gradient(colors: [
                                    viewModel.callState == .listening ? Color.green : (viewModel.callState == .speaking ? Color.purple : Color.cyan),
                                    Color.blue.opacity(0.7),
                                    Color.clear
                                ]),
                                center: .center,
                                startRadius: 10,
                                endRadius: 85
                            )
                        )
                        .frame(width: 170, height: 170)
                        .shadow(color: Color.cyan.opacity(0.5), radius: 25, x: 0, y: 0)
                        .scaleEffect(viewModel.callState == .thinking ? 1.08 : 1.0)
                        .animation(
                            viewModel.callState == .thinking ?
                            Animation.easeInOut(duration: 0.8).repeatForever(autoreverses: true) :
                            .default,
                            value: viewModel.callState
                        )
                    
                    // Center Icon
                    Image(systemName: viewModel.callState == .speaking ? "waveform" : (viewModel.callState == .listening ? "mic.fill" : "sparkles"))
                        .font(.system(size: 44, weight: .medium))
                        .foregroundColor(.white)
                }
                
                // Status & Subtitle
                VStack(spacing: 8) {
                    Text(viewModel.statusSubtitle)
                        .font(.system(size: 15, weight: .medium))
                        .foregroundColor(.white.opacity(0.85))
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 32)
                        .animation(.easeInOut, value: viewModel.statusSubtitle)
                    
                    if !viewModel.lastTranscript.isEmpty {
                        Text("\"\(viewModel.lastTranscript)\"")
                            .font(.system(size: 13, weight: .regular))
                            .foregroundColor(.cyan.opacity(0.9))
                            .lineLimit(3)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal, 36)
                    }
                }
                .frame(minHeight: 60)
                
                // Mode Selector: Hands-Free 1vs1 vs Push-To-Talk
                Button(action: {
                    let generator = UIImpactFeedbackGenerator(style: .medium)
                    generator.impactOccurred()
                    viewModel.toggleHandsFreeMode()
                }) {
                    HStack(spacing: 8) {
                        Image(systemName: viewModel.isHandsFreeMode ? "waveform.badge.mic" : "hand.tap.fill")
                            .font(.system(size: 14, weight: .bold))
                        Text(viewModel.isHandsFreeMode ? "Đàm Thoại 1vs1: BẬT (Rảnh tay)" : "Chế độ: Bấm giữ để nói")
                            .font(.system(size: 13, weight: .semibold))
                    }
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(viewModel.isHandsFreeMode ? Color.green.opacity(0.2) : Color.white.opacity(0.12))
                    .foregroundColor(viewModel.isHandsFreeMode ? .green : .white.opacity(0.85))
                    .cornerRadius(20)
                    .overlay(
                        RoundedRectangle(cornerRadius: 20)
                            .stroke(viewModel.isHandsFreeMode ? Color.green.opacity(0.7) : Color.white.opacity(0.2), lineWidth: 1)
                    )
                }
                
                Spacer()
                
                // Controls
                VStack(spacing: 20) {
                    if viewModel.isHandsFreeMode {
                        // In Hands-Free Mode: Single Tap toggles send or speech
                        Button(action: {
                            let generator = UIImpactFeedbackGenerator(style: .medium)
                            generator.impactOccurred()
                            if viewModel.callState == .listening {
                                viewModel.finishTalkingAndSend()
                            } else if viewModel.callState == .idle {
                                viewModel.startTalking()
                            } else if viewModel.callState == .speaking || viewModel.callState == .thinking {
                                viewModel.startTalking()
                            }
                        }) {
                            ZStack {
                                Circle()
                                    .fill(viewModel.callState == .listening ? Color.green : Color.cyan)
                                    .frame(width: 86, height: 86)
                                    .shadow(color: (viewModel.callState == .listening ? Color.green : Color.cyan).opacity(0.5), radius: 15, x: 0, y: 5)
                                
                                Image(systemName: viewModel.callState == .listening ? "mic.fill" : "waveform.circle.fill")
                                    .font(.system(size: 36, weight: .semibold))
                                    .foregroundColor(.black)
                            }
                        }
                        
                        Text(viewModel.callState == .listening ? "🎤 Đang nghe... Dứt câu 0.8s là tự gửi" : "Chạm để nói hoặc đợi AI xong lượt")
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(viewModel.callState == .listening ? .green : .gray)
                    } else {
                        // Standard Push-To-Talk Button
                        Button(action: {}) {
                            ZStack {
                                Circle()
                                    .fill(isPressingTalk ? Color.red : Color.cyan)
                                    .frame(width: 86, height: 86)
                                    .shadow(color: isPressingTalk ? Color.red.opacity(0.5) : Color.cyan.opacity(0.4), radius: 15, x: 0, y: 5)
                                
                                Image(systemName: isPressingTalk ? "waveform.circle.fill" : "mic.fill")
                                    .font(.system(size: 36, weight: .semibold))
                                    .foregroundColor(.black)
                            }
                        }
                        .simultaneousGesture(
                            DragGesture(minimumDistance: 0)
                                .onChanged { _ in
                                    if !isPressingTalk {
                                        isPressingTalk = true
                                        let generator = UIImpactFeedbackGenerator(style: .medium)
                                        generator.impactOccurred()
                                        viewModel.startTalking()
                                    }
                                }
                                .onEnded { _ in
                                    isPressingTalk = false
                                    let generator = UIImpactFeedbackGenerator(style: .light)
                                    generator.impactOccurred()
                                    viewModel.finishTalkingAndSend()
                                }
                        )
                        
                        Text(isPressingTalk ? "Đang thu âm... Nhả tay để gửi" : "Giữ nút để nói chuyện trực tiếp")
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(.gray)
                    }
                }
                .padding(.bottom, 24)
            }
        }
        .onAppear {
            viewModel.onAppear()
        }
    }
}
