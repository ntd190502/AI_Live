import Foundation
import AVFoundation

class AudioEngineManager: NSObject, ObservableObject, AVAudioPlayerDelegate, AVAudioRecorderDelegate {
    @Published var isRecording: Bool = false
    @Published var isPlaying: Bool = false
    @Published var audioLevel: Float = 0.0 // 0.0 to 1.0 for visualizer
    
    private var audioRecorder: AVAudioRecorder?
    private var audioPlayer: AVAudioPlayer?
    private var levelTimer: Timer?
    private var recordingURL: URL?
    private var playCompletion: (() -> Void)?
    
    // Voice Activity Detection (VAD) for 1vs1 Hands-Free Mode
    var isVADEnabled: Bool = false
    var onVADDetectedEndOfSpeech: (() -> Void)?
    private var vadSpeechStarted: Bool = false
    private var vadSilenceStartTime: Date?
    
    override init() {
        super.init()
        setupAudioSession()
    }
    
    deinit {
        NotificationCenter.default.removeObserver(self)
    }
    
    private func setupAudioSession() {
        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.playAndRecord, mode: .voiceChat, options: [.defaultToSpeaker, .allowBluetooth, .allowBluetoothA2DP])
            try session.setActive(true)
            
            // Listen for system interruptions (phone calls, Siri, alarms)
            NotificationCenter.default.addObserver(
                self,
                selector: #selector(handleAudioSessionInterruption),
                name: AVAudioSession.interruptionNotification,
                object: nil
            )
            
            // Listen for audio route changes (AirPods connected, headset plugged/unplugged)
            NotificationCenter.default.addObserver(
                self,
                selector: #selector(handleAudioRouteChange),
                name: AVAudioSession.routeChangeNotification,
                object: nil
            )
        } catch {
            print("[AudioEngine] Error configuring audio session: \(error.localizedDescription)")
        }
    }
    
    @objc private func handleAudioSessionInterruption(notification: Notification) {
        guard let userInfo = notification.userInfo,
              let typeValue = userInfo[AVAudioSessionInterruptionTypeKey] as? UInt,
              let type = AVAudioSession.InterruptionType(rawValue: typeValue) else { return }
        
        if type == .began {
            print("[AudioEngine] Hệ thống tạm ngắt AudioSession (cuộc gọi / Siri / báo thức)...")
            stopRecording()
            stopPlayback()
        } else if type == .ended {
            if let optionsValue = userInfo[AVAudioSessionInterruptionOptionKey] as? UInt {
                let options = AVAudioSession.InterruptionOptions(rawValue: optionsValue)
                if options.contains(.shouldResume) {
                    print("[AudioEngine] Hết gián đoạn, tự động khôi phục AudioSession...")
                    try? AVAudioSession.sharedInstance().setActive(true)
                }
            }
        }
    }
    
    @objc private func handleAudioRouteChange(notification: Notification) {
        print("[AudioEngine] Thay đổi cổng âm thanh (AirPods / tai nghe)...")
        try? AVAudioSession.sharedInstance().setActive(true)
    }
    
    private var recordingStartTime: Date?
    
    func startRecording() {
        let tempDir = FileManager.default.temporaryDirectory
        recordingURL = tempDir.appendingPathComponent("live_input_\(Date().timeIntervalSince1970).wav")
        recordingStartTime = Date()
        vadSpeechStarted = false
        vadSilenceStartTime = nil
        
        guard let url = recordingURL else { return }
        
        let settings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatLinearPCM),
            AVSampleRateKey: 16000.0,
            AVNumberOfChannelsKey: 1,
            AVLinearPCMBitDepthKey: 16,
            AVLinearPCMIsBigEndianKey: false,
            AVLinearPCMIsFloatKey: false
        ]
        
        do {
            audioRecorder = try AVAudioRecorder(url: url, settings: settings)
            audioRecorder?.delegate = self
            audioRecorder?.isMeteringEnabled = true
            audioRecorder?.record()
            
            isRecording = true
            startMetering()
        } catch {
            print("[AudioEngine] Recording start error: \(error)")
        }
    }
    
    func stopRecording() -> Data? {
        guard isRecording else { return nil }
        
        stopMetering()
        audioRecorder?.stop()
        isRecording = false
        vadSpeechStarted = false
        vadSilenceStartTime = nil
        
        let duration = Date().timeIntervalSince(recordingStartTime ?? Date())
        
        guard let url = recordingURL, FileManager.default.fileExists(atPath: url.path) else {
            return nil
        }
        
        defer {
            try? FileManager.default.removeItem(at: url)
        }
        
        do {
            let data = try Data(contentsOf: url)
            // Guardrail: Ignore accidental brief taps or tiny audio packets (< 0.4s or < 2KB)
            if duration < 0.4 || data.count < 2048 {
                print("[AudioEngine] Ignored short/empty recording: \(duration)s, \(data.count) bytes")
                return nil
            }
            return data
        } catch {
            print("[AudioEngine] Error reading recorded data: \(error)")
            return nil
        }
    }
    
    func playVoiceData(_ data: Data, completion: (() -> Void)? = nil) {
        do {
            stopPlayback()
            self.playCompletion = completion
            audioPlayer = try AVAudioPlayer(data: data)
            audioPlayer?.delegate = self
            audioPlayer?.isMeteringEnabled = true
            audioPlayer?.prepareToPlay()
            audioPlayer?.play()
            
            isPlaying = true
            startPlaybackMetering()
        } catch {
            print("[AudioEngine] Playback error: \(error)")
            completion?()
        }
    }
    
    func stopPlayback() {
        if isPlaying {
            audioPlayer?.stop()
            audioPlayer = nil
            isPlaying = false
            stopMetering()
            audioLevel = 0.0
            let comp = playCompletion
            playCompletion = nil
            comp?()
        }
    }
    
    private func startMetering() {
        levelTimer?.invalidate()
        vadSpeechStarted = false
        vadSilenceStartTime = nil
        
        levelTimer = Timer.scheduledTimer(withTimeInterval: 0.05, repeats: true) { [weak self] _ in
            guard let self = self, let recorder = self.audioRecorder, recorder.isRecording else { return }
            recorder.updateMeters()
            let power = recorder.averagePower(forChannel: 0)
            self.updateLevel(from: power)
            
            // Real-time Voice Activity Detection (VAD)
            if self.isVADEnabled {
                let level = self.audioLevel
                let now = Date()
                let recordingDuration = now.timeIntervalSince(self.recordingStartTime ?? now)
                
                // Only evaluate VAD after at least 0.3s of recording to ignore initial click noises
                if recordingDuration > 0.3 {
                    if level > 0.15 {
                        // User is actively speaking
                        self.vadSpeechStarted = true
                        self.vadSilenceStartTime = nil
                    } else if self.vadSpeechStarted && level < 0.07 {
                        // User has started speaking previously and is now silent
                        if self.vadSilenceStartTime == nil {
                            self.vadSilenceStartTime = now
                        } else if now.timeIntervalSince(self.vadSilenceStartTime!) >= 0.85 {
                            // Silence sustained for >= 0.85 seconds -> End of speech!
                            print("[AudioEngine] VAD phát hiện dứt câu (im lặng 0.85s) -> Tự động dừng thu âm và gửi!")
                            self.vadSpeechStarted = false
                            self.vadSilenceStartTime = nil
                            DispatchQueue.main.async {
                                self.onVADDetectedEndOfSpeech?()
                            }
                        }
                    }
                }
            }
        }
    }
    
    private func startPlaybackMetering() {
        levelTimer?.invalidate()
        levelTimer = Timer.scheduledTimer(withTimeInterval: 0.05, repeats: true) { [weak self] _ in
            guard let self = self, let player = self.audioPlayer, player.isPlaying else { return }
            player.updateMeters()
            let power = player.averagePower(forChannel: 0)
            self.updateLevel(from: power)
        }
    }
    
    private func stopMetering() {
        levelTimer?.invalidate()
        levelTimer = nil
        audioLevel = 0.0
    }
    
    private func updateLevel(from power: Float) {
        // Normalize dB power (-60dB to 0dB) to 0.0 - 1.0
        let minDb: Float = -60.0
        let level = max(0.0, min(1.0, (power - minDb) / (-minDb)))
        DispatchQueue.main.async {
            self.audioLevel = level
        }
    }
    
    // MARK: - AVAudioPlayerDelegate
    func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        DispatchQueue.main.async {
            self.isPlaying = false
            self.stopMetering()
            let comp = self.playCompletion
            self.playCompletion = nil
            comp?()
        }
    }
}
