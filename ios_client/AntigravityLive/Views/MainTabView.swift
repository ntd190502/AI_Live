import SwiftUI

struct MainTabView: View {
    @State private var selectedTab = 0
    
    var body: some View {
        TabView(selection: $selectedTab) {
            LiveCallView()
                .tabItem {
                    Label("Live Call", systemImage: "waveform.circle.fill")
                }
                .tag(0)
            
            ChatView()
                .tabItem {
                    Label("Tin Nhắn", systemImage: "message.fill")
                }
                .tag(1)
            
            SettingsView()
                .tabItem {
                    Label("Cài Đặt", systemImage: "gearshape.fill")
                }
                .tag(2)
        }
        .accentColor(.cyan)
    }
}
