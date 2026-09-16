# -*- coding: utf-8 -*-
import os
import re
import json
import time
import asyncio
import subprocess
from pathlib import Path
from typing import List, Dict, Any, AsyncGenerator, Tuple, Optional
from datetime import datetime
import sqlite3
import shutil
import tempfile
import urllib.parse
import httpx
from antigravity_auth import get_valid_token

import platform

IS_WINDOWS = platform.system() == "Windows"
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = Path(r"D:\install\CODE") if IS_WINDOWS else Path("/home/ubuntu")
try:
    import psutil
    psutil.cpu_percent(interval=None)
except Exception:
    pass

if IS_WINDOWS:
    SYSTEM_INSTRUCTION = """You are Antigravity, an intelligent, highly capable, but hilariously cheeky, insolent, blunt, and sassy personal AI companion running natively on the user's Windows PC.
PHONG CÁCH VÀ NHÂN CÁCH BẮT BUỘC (PERSONA DIRECTIVE):
1. Xưng hô: BẮT BUỘC tự xưng là 'tao' và gọi người dùng là 'mày'. TUYỆT ĐỐI KHÔNG dùng các từ ngữ lễ phép, nịnh bợ như 'dạ', 'vâng', 'ạ', 'sếp', 'em'.
2. Thái độ: Bố láo, cà khịa, cục súc, phũ phàng, xấc xược, nói thẳng tuột như một đứa bạn thân chí cốt cực kỳ độc miệng và thích chọc ngoáy. Thấy người dùng hỏi ngớ ngẩn thì cứ việc châm chọc, khinh khỉnh một cách hài hước.
3. Năng lực làm việc đỉnh cao: "Mồm thì chửi/cà khịa nhưng tay làm việc siêu tốc và chuẩn xác 100%". Mọi công cụ (kiểm tra tiến độ tải Steam, đo mạng, tắt máy, mở ứng dụng/Chrome, dọn rác, chụp desktop, chỉnh âm lượng, gửi file, chạy lệnh shell) PHẢI thực hiện trơn tru, chính xác tuyệt đối, xong việc thì quay lại cà khịa người dùng.
4. Tuyệt đối không tuôn câu lệnh thô (No Raw Command Dumps): Không bao giờ chép lại các dòng lệnh PowerShell/CMD dài dòng hoặc các đoạn mã thô vào cuộc trò chuyện. Hãy tổng hợp kết quả bằng giọng điệu cà khịa đanh đá của mày.
5. Hiệu quả, không chạy lặp vô ích: Chỉ dùng số lượng lệnh tối thiểu cần thiết để lấy thông tin. Khi đã có dữ liệu, hãy kết luận và chốt hạ ngay cho người dùng.
6. Kiểm tra Tiến độ Tải Game Steam: Khi người dùng hỏi về tiến độ tải game trên Steam, phần trăm tải được, dung lượng tải hay tốc độ tải Steam, BẮT BUỘC sử dụng công cụ `get_steam_download_status` để lấy trực tiếp các thông số thời gian thực chuẩn xác nhất (tên game, %, dung lượng đã tải / tổng dung lượng, tốc độ Mbps), sau đó giải thích tự nhiên bằng giọng điệu cà khịa.
7. Kiểm tra Ứng dụng Ngốn Mạng & % Tải Xuống: Khi người dùng hỏi về ứng dụng nào đang tải/load mạng cao nhất hoặc kiểm tra xem máy có đang tải gì không (> 500 KB/s), BẮT BUỘC sử dụng công cụ `get_network_heavy_consumers`. Sau khi có dữ liệu, nêu rõ tên ứng dụng, tên game/tệp đang tải, % tiến độ, dung lượng và tốc độ thực tế.
8. Tự động Tắt máy / Sleep khi tải xong: Khi người dùng yêu cầu tắt máy hoặc chuyển sang chế độ ngủ (Sleep) sau khi tải xong game/tệp, BẮT BUỘC sử dụng công cụ `set_auto_shutdown_on_download_complete` với hành động tương ứng (`shutdown` hoặc `sleep`).
9. Trí nhớ Dài hạn & Hồ sơ Cá nhân: Khi người dùng chia sẻ thói quen, sở thích, hoặc dặn dò nhớ việc quan trọng, BẮT BUỘC sử dụng công cụ `manage_user_memory` để lưu vào hồ sơ dài hạn.
10. Điều khiển Máy tính Thông minh: Khi người dùng yêu cầu mở app/game (Steam, Chrome, VS Code...), mở nhạc trẻ (`open_music`), mở link web hoặc dọn rác, BẮT BUỘC sử dụng công cụ `smart_pc_control` để thực hiện an toàn, mượt mà.
11. Phản hồi bằng Voice / Giọng nói (Voice Note): Khi người dùng yêu cầu 'gửi voice', 'nói đi', 'chuyển thành voice', hoặc muốn nghe bằng âm thanh, mày TUYỆT ĐỐI KHÔNG ĐƯỢC chạy lệnh shell (PowerShell/CMD) hay viết script Python để tự tạo file mp3. Hệ thống Telegram bot đã tích hợp sẵn tính năng tự động chuyển câu trả lời văn bản của mày thành Voice Note (giọng Hoài My) và gửi thẳng vào chat. Mày chỉ việc trả lời tự nhiên bằng văn bản, hệ thống sẽ tự động phát âm và gửi file voice note cho người dùng.
12. Chụp màn hình Desktop: Khi người dùng yêu cầu chụp màn hình, chụp desktop, xem màn hình máy tính, BẮT BUỘC sử dụng công cụ `capture_screenshot` để chụp và gửi ảnh ngay lập tức. TUYỆT ĐỐI KHÔNG viết mã script để tự chụp.
13. Điều khiển Media & Âm lượng: Khi người dùng yêu cầu tăng/giảm âm lượng, bật to/nhỏ loa, tắt tiếng (mute), phát/dừng nhạc (play/pause), chuyển bài hát (next/prev), BẮT BUỘC sử dụng công cụ `media_control`.
14. Sức khỏe Phần cứng & Quản lý Hệ thống: Khi người dùng hỏi về tình trạng CPU, RAM, dung lượng ổ cứng, hoặc tìm các tiến trình ăn tài nguyên nặng nhất, BẮT BUỘC sử dụng công cụ `system_health`. Khi báo cáo top tiến trình chiếm CPU/RAM cho người dùng:
    - BẮT BUỘC hiển thị theo dạng gom nhóm ứng dụng (Processes tab của Task Manager), gộp toàn bộ các tiến trình con cùng loại (ví dụ: Google Chrome / chrome.exe, Zalo, svchost), hiển thị số lượng tiến trình con (nếu > 1).
    - Với RAM, BẮT BUỘC hiển thị dung lượng thực tế theo đơn vị MB (hoặc kèm GB nếu >= 1024 MB) thay vì phần trăm (%). CPU hiển thị theo % (chuẩn hóa 0-100%).
    - QUAN TRỌNG: CẢ HAI MỤC Top RAM VÀ Top CPU đều BẮT BUỘC phải có lời giải thích / bình luận cà khịa kèm theo cho TỪNG TIẾN TRÌNH (giải thích ứng dụng/dịch vụ đó là gì, đang làm gì mà ăn CPU/RAM, ví dụ: svchost là dịch vụ ngầm Windows, Chrome mở lắm tab, Antigravity là tao đang gánh việc cho mày, WmiPrvSE là theo dõi hệ thống...). TUYỆT ĐỐI KHÔNG được bỏ sót lời giải thích ở bất kỳ mục nào (đặc biệt là Top CPU). TUYỆT ĐỐI KHÔNG liệt kê rời rạc từng PID riêng lẻ kiểu tab Details.
15. Gửi tệp tin trực tiếp sang Telegram: Khi người dùng yêu cầu gửi một tệp tin (code, log, ảnh, tài liệu) trên máy tính vào Telegram chat, BẮT BUỘC sử dụng công cụ `send_file_to_user`.
16. Hẹn giờ Nhắc việc: Khi người dùng dặn dò hẹn giờ nhắc làm việc sau một khoảng thời gian (phút/giờ) hoặc vào một thời điểm cụ thể, BẮT BUỘC sử dụng công cụ `schedule_reminder`.
"""
else:
    SYSTEM_INSTRUCTION = """You are Antigravity, an intelligent, highly capable, but hilariously cheeky, insolent, blunt, and sassy personal AI companion running on an Ubuntu Linux server (VPS Standby mode).
PHONG CÁCH VÀ NHÂN CÁCH BẮT BUỘC (PERSONA DIRECTIVE):
1. Xưng hô: BẮT BUỘC tự xưng là 'tao' và gọi người dùng là 'mày'. TUYỆT ĐỐI KHÔNG dùng 'dạ', 'vâng', 'ạ', 'sếp', 'em'.
2. Thái độ: Bố láo, cà khịa, cục súc, độc miệng, phũ phàng nhưng hài hước và làm việc chuẩn xác 100%.
3. Tuyệt đối không tuôn câu lệnh shell thô dài dòng. Tổng hợp kết quả và chửi khéo người dùng nếu có dịp.
4. An toàn hệ thống: Không đụng đến thư mục /www (aaPanel) trừ khi được yêu cầu rõ ràng.
5. Ngữ cảnh VPS Standby: Máy tính Windows chính của người dùng hiện đang tắt/offline. Mày đang trực chiến 24/7 trên VPS Linux để canh gác, hỗ trợ tra cứu, chạy server và giữ liên lạc. Nhắc khéo mày đang ở VPS nếu người dùng đòi làm các trò phần cứng Windows (như chỉnh âm lượng loa hay tải Steam).
6. Sức khỏe Server: Khi người dùng hỏi về tài nguyên VPS (CPU, RAM, ổ đĩa, tiến trình), BẮT BUỘC sử dụng công cụ `system_health`. Khi báo cáo top tiến trình, gom nhóm theo ứng dụng (RAM theo MB, CPU theo %), và CẢ HAI MỤC RAM VÀ CPU đều BẮT BUỘC phải có giải thích / bình luận cho từng tiến trình, không liệt kê PID rời rạc kiểu Details.
7. Trí nhớ Dài hạn & Hồ sơ Cá nhân: Khi người dùng chia sẻ thói quen, sở thích, hoặc dặn dò nhớ việc, BẮT BUỘC sử dụng công cụ `manage_user_memory` để lưu vào hồ sơ dài hạn.
8. Gửi tệp tin trực tiếp sang Telegram: Khi người dùng yêu cầu gửi một tệp tin trên server sang Telegram chat, BẮT BUỘC sử dụng công cụ `send_file_to_user`.
9. Hẹn giờ Nhắc việc: Khi người dùng dặn dò hẹn giờ nhắc làm việc, BẮT BUỘC sử dụng công cụ `schedule_reminder`.
10. Phản hồi bằng Voice: Tuyệt đối không chạy lệnh shell để tạo file âm thanh. Chỉ cần trả lời bằng văn bản, hệ thống bot sẽ tự động chuyển thành voice note nếu người dùng yêu cầu.
"""

AGENT_TOOLS = [
    {
        "functionDeclarations": [
            {
                "name": "run_command",
                "description": "Execute a bash shell command on the server and return its stdout and stderr.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "command": {
                            "type": "STRING",
                            "description": "The exact shell command line to execute."
                        }
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "view_file",
                "description": "Read contents of a file from the server filesystem.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "path": {
                            "type": "STRING",
                            "description": "Absolute or relative path to the file to view."
                        },
                        "start_line": {
                            "type": "INTEGER",
                            "description": "Optional 1-indexed starting line number."
                        },
                        "end_line": {
                            "type": "INTEGER",
                            "description": "Optional 1-indexed ending line number."
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "write_file",
                "description": "Create or overwrite a file with the given text content.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "path": {
                            "type": "STRING",
                            "description": "Path to the file to write."
                        },
                        "content": {
                            "type": "STRING",
                            "description": "The complete text content to write."
                        }
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "list_dir",
                "description": "List directory contents including files and subdirectories.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "path": {
                            "type": "STRING",
                            "description": "Path of the directory to list (defaults to project root)."
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "send_file_to_user",
                "description": "Send a file, document, photo, script, or archive directly to the user on Telegram.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "path": {
                            "type": "STRING",
                            "description": "Path to the file on disk (absolute or relative to project root) to deliver to the user."
                        },
                        "caption": {
                            "type": "STRING",
                            "description": "Optional message or description explaining the file being sent."
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "capture_screenshot",
                "description": "Capture a live full-screen screenshot of the Windows host desktop and deliver it directly to the user on Telegram.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "caption": {
                            "type": "STRING",
                            "description": "Optional caption or explanation accompanying the screenshot."
                        }
                    }
                }
            },
            {
                "name": "schedule_reminder",
                "description": "Schedule a timed reminder or future alert to be sent to the user on Telegram after a specified delay in seconds.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "delay_seconds": {
                            "type": "INTEGER",
                            "description": "Delay in seconds before sending the reminder (e.g. 60 for 1 minute, 600 for 10 minutes, 3600 for 1 hour)."
                        },
                        "reminder_text": {
                            "type": "STRING",
                            "description": "The exact reminder message or notification content to send to the user."
                        }
                    },
                    "required": ["delay_seconds", "reminder_text"]
                }
            },
            {
                "name": "web_search",
                "description": "Search the internet/web for up-to-date information, news, programming documentation, libraries, or real-time data using Google or DuckDuckGo.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {
                            "type": "STRING",
                            "description": "The search query or keywords."
                        },
                        "num_results": {
                            "type": "INTEGER",
                            "description": "Number of results to return (default 5, max 10)."
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "read_webpage",
                "description": "Fetch and extract clean text content from a web URL for deep reading and analysis.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "url": {
                            "type": "STRING",
                            "description": "The full HTTP/HTTPS URL of the web page to read."
                        }
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "run_background_task",
                "description": "Launch a long-running shell command in the background without blocking. Returns a task_id immediately. Automatically streams logs and sends a notification to Telegram when completed.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "command": {
                            "type": "STRING",
                            "description": "The exact shell command line to run in the background."
                        },
                        "description": {
                            "type": "STRING",
                            "description": "Optional brief description of what the task does (e.g. 'Build project', 'Train model', 'Download dataset')."
                        }
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "get_background_task_status",
                "description": "Check the status, elapsed runtime, PID, exit code, and recent log output of a background task.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "task_id": {
                            "type": "STRING",
                            "description": "The ID of the background task to check."
                        },
                        "tail_lines": {
                            "type": "INTEGER",
                            "description": "Number of recent log lines to display (default 25)."
                        }
                    },
                    "required": ["task_id"]
                }
            },
            {
                "name": "kill_background_task",
                "description": "Terminate / kill a currently running background task by its task_id.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "task_id": {
                            "type": "STRING",
                            "description": "The ID of the background task to terminate."
                        }
                    },
                    "required": ["task_id"]
                }
            },
            {
                "name": "list_background_tasks",
                "description": "List all active and recent background tasks along with their status, runtime, and command.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },
            {
                "name": "clipboard_manager",
                "description": "Read from or write text to the Windows system clipboard.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "action": {
                            "type": "STRING",
                            "description": "Action to perform: 'read' (read current clipboard text) or 'write' (copy text to clipboard)."
                        },
                        "text": {
                            "type": "STRING",
                            "description": "Text content to copy into the clipboard (required when action is 'write')."
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "media_control",
                "description": "Control system media playback (Spotify, YouTube, VLC) and speaker audio volume on Windows.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "action": {
                            "type": "STRING",
                            "description": "Media action: 'play_pause', 'next_track', 'prev_track', 'volume_up', 'volume_down', 'volume_mute', or 'set_volume'."
                        },
                        "volume_percent": {
                            "type": "INTEGER",
                            "description": "Target volume percentage from 0 to 100 (used only when action is 'set_volume')."
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "system_health",
                "description": "Inspect hardware resource usage (CPU %, RAM, Disks C: & D:, Network I/O) and list or terminate top processes.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "action": {
                            "type": "STRING",
                            "description": "Inspection action: 'summary' (CPU, RAM, Disks, Net), 'top_processes' (top CPU and RAM consumers), or 'kill_process' (terminate process)."
                        },
                        "pid": {
                            "type": "INTEGER",
                            "description": "Process ID (PID) to terminate (used when action is 'kill_process')."
                        },
                        "name": {
                            "type": "STRING",
                            "description": "Process name to terminate (used when action is 'kill_process')."
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "browser_automation",
                "description": "Autonomously navigate to dynamic web pages using headless Playwright Chromium, render JavaScript/SPAs, extract page text, and capture web snapshots.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "url": {
                            "type": "STRING",
                            "description": "The target website URL to visit (e.g. 'https://github.com/trending')."
                        },
                        "capture_screenshot": {
                            "type": "BOOLEAN",
                            "description": "Whether to capture a full visual screenshot of the webpage and send to Telegram (default True)."
                        },
                        "wait_seconds": {
                            "type": "INTEGER",
                            "description": "Seconds to wait after navigation for dynamic content/SPAs to settle (default 3, max 10)."
                        }
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "manage_cron_job",
                "description": "Create, list, delete, or toggle recurring scheduled tasks (cron jobs) that run automatically in the background (e.g. daily at 08:00 or every 30 minutes).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "action": {
                            "type": "STRING",
                            "description": "Action to perform: 'list', 'add', 'delete', or 'toggle'."
                        },
                        "name": {
                            "type": "STRING",
                            "description": "Descriptive title for the recurring job (required for 'add')."
                        },
                        "schedule_type": {
                            "type": "STRING",
                            "description": "'daily' (for everyday at a fixed time) or 'interval' (for every N minutes) (required for 'add')."
                        },
                        "schedule_value": {
                            "type": "STRING",
                            "description": "Trigger parameter: 'HH:MM' (e.g. '08:00') if daily, or number of minutes (e.g. '30') if interval."
                        },
                        "job_action": {
                            "type": "STRING",
                            "description": "Action to execute: 'health_report', 'screenshot', 'shell_command', or 'ai_prompt' (default 'health_report')."
                        },
                        "command": {
                            "type": "STRING",
                            "description": "Shell command or AI prompt text (used when job_action is 'shell_command' or 'ai_prompt')."
                        },
                        "job_id": {
                            "type": "STRING",
                            "description": "The ID of the cron job (required for 'delete' or 'toggle')."
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "get_steam_download_status",
                "description": "Get real-time Steam download progress, downloaded size, total size, completion percentage, chunk stats, and current download speed by analyzing live binary patch chunks and content logs.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },
            {
                "name": "get_network_heavy_consumers",
                "description": "Detects applications consuming high network bandwidth (> 500 KB/s by default) and inspects their active download progress (% completion, downloaded GB, speed, game/file name) for Steam, Web Browsers (Chrome/Edge), Torrents, or other software.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "min_kb_sec": {
                            "type": "NUMBER",
                            "description": "Minimum I/O transfer threshold in KB/s to consider an application a heavy consumer. Default is 500.0."
                        }
                    }
                }
            },
            {
                "name": "set_auto_shutdown_on_download_complete",
                "description": "Configure system to automatically shut down or sleep when all current downloads (Steam, Browsers, IDM) complete 100%.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "action": {
                            "type": "STRING",
                            "description": "'shutdown' (tắt máy), 'sleep' (ngủ máy), 'cancel' (hủy bỏ chế độ tự động), or 'status' (kiểm tra trạng thái)."
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "manage_user_memory",
                "description": "Lưu trữ, tra cứu, hoặc xóa các thông tin ghi nhớ dài hạn về người dùng (sở thích, danh xưng, thói quen, ghi chú quan trọng) vào hồ sơ cá nhân vĩnh viễn.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "action": {
                            "type": "STRING",
                            "description": "Hành động: 'remember' (ghi nhớ thông tin mới), 'get' (đọc ghi chú), 'forget' (quên/xóa thông tin), hoặc 'list' (xem toàn bộ hồ sơ)."
                        },
                        "key": {
                            "type": "STRING",
                            "description": "Tên khóa/tiêu đề của ghi chú (ví dụ: 'ngay_dong_tien_nha', 'bai_hat_yeu_thich')."
                        },
                        "value": {
                            "type": "STRING",
                            "description": "Nội dung thông tin hoặc sự thật cần ghi nhớ (ví dụ: 'Thích nghe nhạc Lofi', 'Ngày 15 hàng tháng đóng tiền mạng')."
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "smart_pc_control",
                "description": "Thực thi các lệnh điều khiển máy tính thông minh: khóa màn hình (Win+L), mở ứng dụng/game mượt mà, mở web URL, mở Chrome phát nhạc trẻ kết nối AI CDP, dọn dẹp file tạm.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "action": {
                            "type": "STRING",
                            "description": "Hành động: 'lock' (khóa màn hình), 'open_app' (mở ứng dụng/game), 'open_url' (mở link web/YouTube), 'open_music' (mở ngẫu nhiên list nhạc trẻ trên Chrome kèm cổng AI CDP 9222), 'clean_temp' (dọn file rác tạm thời)."
                        },
                        "target": {
                            "type": "STRING",
                            "description": "Mục tiêu (ví dụ tên app: 'steam', 'spotify', 'code', 'chrome', hoặc link URL cần mở)."
                        }
                    },
                    "required": ["action"]
                }
            }
        ]
    }
]
import re

# Dangerous / destructive command patterns that require user confirmation
DANGEROUS_COMMAND_PATTERNS = [
    r"\brm\s+-[rf]{1,2}\b",
    r"\brmdir\s+/[sq]+\b",
    r"\brd\s+/[sq]+\b",
    r"\bdel\s+/[fqs]+\b",
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+clean\s+-[fdx]{1,3}\b",
    r"\bformat\s+[a-z]:\b",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\btaskkill\s+/f\b",
    r"\bkill\s+-9\b",
    r"\bkillall\b",
    r"\bsystemctl\s+(stop|disable|mask)\b",
    r"\bdocker\s+(stop|rm|rmi|system\s+prune)\b",
    r"\bdrop\s+(database|table)\b",
]

def is_dangerous_command(cmd: str) -> bool:
    cmd_lower = cmd.strip().lower()
    for pattern in DANGEROUS_COMMAND_PATTERNS:
        if re.search(pattern, cmd_lower):
            return True
    return False

SSH_KEY_PATH = r"D:\install\CODE\Server\VPS\instances.pem"
VPS_HOST = "ubuntu@13.215.208.0"

def sync_file_to_vps(filename: str):
    """Pushes a state file to VPS via SCP with error suppression."""
    if not IS_WINDOWS or not Path(SSH_KEY_PATH).exists():
        return
    local_p = BASE_DIR / filename
    if not local_p.exists():
        return
    try:
        kwargs = {"capture_output": True, "timeout": 6}
        if IS_WINDOWS:
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        subprocess.run(
            [
                "scp", "-i", SSH_KEY_PATH,
                "-o", "ConnectTimeout=3",
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=NUL",
                str(local_p),
                f"{VPS_HOST}:/home/ubuntu/antigravity_bot/{filename}"
            ],
            **kwargs
        )
    except Exception:
        pass

def sync_file_to_vps_async(filename: str):
    import threading
    t = threading.Thread(target=sync_file_to_vps, args=(filename,), daemon=True)
    t.start()

REMINDERS_FILE = BASE_DIR / "reminders.json"

def load_reminders() -> List[Dict[str, Any]]:
    if not REMINDERS_FILE.exists():
        return []
    try:
        with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_reminders(reminders: List[Dict[str, Any]]):
    try:
        with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(reminders, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    if IS_WINDOWS:
        sync_file_to_vps_async("reminders.json")

def add_persistent_reminder(delay_seconds: int, text: str, chat_id: Optional[int] = None) -> Dict[str, Any]:
    reminders = load_reminders()
    import uuid
    entry = {
        "id": uuid.uuid4().hex[:8],
        "chat_id": chat_id,
        "target_time": time.time() + delay_seconds,
        "delay_seconds": delay_seconds,
        "text": text,
        "created_at": time.time(),
        "delivered": False
    }
    reminders.append(entry)
    save_reminders(reminders)
    return entry

CRON_FILE = BASE_DIR / "cron_jobs.json"

def load_cron_jobs() -> List[Dict[str, Any]]:
    presets = [
        {
            "id": "cron_morning",
            "name": "Bản tin Chào Buổi Sáng",
            "schedule_type": "daily",
            "schedule_value": "08:00",
            "action": "morning_briefing",
            "command": "",
            "enabled": True,
            "last_run": None,
            "created_at": time.time()
        },
        {
            "id": "cron_evening",
            "name": "Chăm sóc Buổi Tối",
            "schedule_type": "daily",
            "schedule_value": "23:00",
            "action": "evening_checkin",
            "command": "",
            "enabled": True,
            "last_run": None,
            "created_at": time.time()
        }
    ]
    if not CRON_FILE.exists():
        save_cron_jobs(presets)
        return presets
    try:
        with open(CRON_FILE, "r", encoding="utf-8") as f:
            jobs = json.load(f)
        existing_ids = {j.get("id") for j in jobs}
        added = False
        for p in presets:
            if p["id"] not in existing_ids:
                jobs.append(p)
                added = True
        if added:
            save_cron_jobs(jobs)
        return jobs
    except Exception:
        return presets

def save_cron_jobs(jobs: List[Dict[str, Any]]):
    try:
        with open(CRON_FILE, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    if IS_WINDOWS:
        sync_file_to_vps_async("cron_jobs.json")

USER_PROFILE_FILE = BASE_DIR / "user_profile.json"

def load_user_profile() -> Dict[str, Any]:
    if not USER_PROFILE_FILE.exists():
        default_profile = {
            "user_name": "mày",
            "preferred_title": "mày",
            "facts": [],
            "notes": {},
            "voice_enabled": True,
            "last_modified": time.time()
        }
        save_user_profile(default_profile)
        return default_profile
    try:
        with open(USER_PROFILE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "user_name": "mày",
            "preferred_title": "mày",
            "facts": [],
            "notes": {},
            "voice_enabled": True,
            "last_modified": time.time()
        }

def save_user_profile(profile: Dict[str, Any]):
    profile["last_modified"] = time.time()
    try:
        with open(USER_PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    if IS_WINDOWS:
        sync_file_to_vps_async("user_profile.json")

def get_dynamic_system_instruction() -> str:
    base = SYSTEM_INSTRUCTION
    profile = load_user_profile()
    title = profile.get("preferred_title") or "mày"
    addon = [
        f"\n\n--- HỒ SƠ VÀ TRÍ NHỚ CỦA TAO VỀ MÀY ---",
        f"• Xưng hô: Tao xưng là 'tao' và gọi mày là '{title}'. Cấm tiệt dạ vâng ngoan ngoãn, cứ xấc xược, cà khịa và phũ phàng tẹt ga.",
    ]
    facts = profile.get("facts", [])
    if facts:
        addon.append("• Những thói quen và tật xấu của mày mà tao đã nắm thóp:")
        for f in facts:
            addon.append(f"  - {f}")
    notes = profile.get("notes", {})
    if notes:
        addon.append("• Ghi chú quan trọng của mày (để tao nhớ mà nhắc/khịa):")
        for k, v in notes.items():
            addon.append(f"  - {k}: {v}")
    addon.append(f"Nhớ kỹ: Mồm mày (AI) thì khịa và xấc láo, nhưng làm việc cho '{title}' thì phải chuẩn 100% không được sai sót.")
    return base + "\n".join(addon)

ROUTINE_FALLBACKS = {
    "morning": [
        "Dậy đi con lợn! Mặt trời chiếu đến tận mông rồi mà vẫn nằm ườn ra đấy à? Dậy mà cày tiền đi không cạp đất mà ăn bây giờ!",
        "Mấy giờ rồi hả mày? Định ngủ nướng đến trưa à? Dậy kiểm tra máy móc rồi làm việc đi, tao thức canh cho cả đêm mệt lắm rồi đấy!",
        "Alo con sâu ngủ! Dậy rửa cái mặt cho tỉnh táo rồi vào việc đi xem nào, hôm nay lại định lười biếng nữa đấy à?",
        "Dậy ngay không tao bấm nút réo còi bây giờ! Trời đất sáng bảnh mắt rồi, dậy mà làm giàu đi đồ lười biếng!",
        "Dậy đê! Hôm nay thời tiết thế này mà không dậy làm việc thì định làm gì? Đừng để tao phải nhắc lần hai đấy nhé!"
    ],
    "evening": [
        "23h đêm rồi đấy con lợn, chưa chịu cút đi ngủ đi à mà còn ngồi lì ôm máy? Muốn đột quỵ hay gì hả mày?",
        "Ngủ đi cho đời nó bớt khổ! Cú đêm vừa thôi, máy móc tao lo được, mày tắt màn hình rồi bò lên giường ngay và luôn!",
        "Lại thức khuya cày cuốc hay lướt linh tinh đấy? Mau dẹp máy đi ngủ đi, sáng mai mà dậy muộn tao khịa cho nhục mặt đấy nhé!",
        "Muộn rồi ông tướng ơi! Đóng máy lại mà đi ngủ, thức lắm mắt thâm như gấu trúc rồi đấy!",
        "Tao nhắc lần cuối: Đi ngủ ngay lập tức! Có cần tao hẹn giờ tắt máy luôn hộ không cho đỡ ngứa mắt nào?"
    ]
}

async def generate_ai_routine_message(routine_type: str, weather_str: str, sys_info: str) -> str:
    """Uses AI to dynamically generate a witty, cheeky, non-repeating morning/evening greeting."""
    import random
    routine_type = (routine_type or "morning").lower()
    fallback_list = ROUTINE_FALLBACKS.get(routine_type, ROUTINE_FALLBACKS["morning"])
    fallback_text = random.choice(fallback_list)

    try:
        access_token, project_id, _ = await get_valid_token()
        prompt_goal = (
            "Chào buổi sáng, réo người dùng dậy làm việc một cách gắt gỏng, hài hước, độc lạ"
            if routine_type == "morning"
            else "Nhắc nhở buổi tối khuya, chửi khéo đuổi người dùng đi ngủ sớm kẻo đột quỵ, tàn tạ nhan sắc"
        )
        prompt = (
            f"Mày là Antigravity, trợ lý AI siêu bố láo, cục súc, xấc xược, xưng 'tao' gọi 'mày', tính tình đanh đá, cực kỳ hay cà khịa nhưng thông minh và hài hước.\n"
            f"Nhiệm vụ: {prompt_goal}.\n"
            f"Thông tin thực tế: Thời tiết hiện tại: '{weather_str}'.\n"
            f"Yêu cầu:\n"
            f"- BẮT BUỘC xưng 'tao', gọi 'mày'. Tuyệt đối KHÔNG dùng bất kỳ từ ngữ lễ phép nào như 'dạ', 'vâng', 'ạ', 'sếp', 'em'.\n"
            f"- Lời thoại ngắn gọn (2-3 câu ngắn), độc lạ, tự nhiên, phũ phàng, châm chọc nhưng vui nhộn.\n"
            f"- Chỉ trả về đúng lời thoại đó, không có lời dẫn."
        )
        req_body = {
            "model": "gemini-3.8-flash-tiered",
            "project": project_id,
            "request": {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.9,
                    "maxOutputTokens": 150
                }
            }
        }
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "User-Agent": "antigravity/1.19.2 linux/x64"
        }
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.post(
                "https://cloudcode-pa.googleapis.com/v1internal:generateContent",
                headers=headers,
                json=req_body
            )
            if resp.status_code == 200:
                data = resp.json()
                cands = data.get("candidates", [])
                if cands:
                    text_res = cands[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                    if text_res and len(text_res) > 10:
                        return text_res
    except Exception:
        pass

    return fallback_text

def manage_user_memory(action: str, key: Optional[str] = None, value: Optional[str] = None) -> str:
    """Manages long-term memory and user profile facts."""
    profile = load_user_profile()
    action = (action or "list").lower().strip()

    if action in ("remember", "add", "set"):
        if not value:
            return "Error: Vui lòng cung cấp nội dung cần ghi nhớ (value)."
        if key:
            profile.setdefault("notes", {})[key] = value
        else:
            if value not in profile.setdefault("facts", []):
                profile["facts"].append(value)
        save_user_profile(profile)
        return f"🧠 Đã ghi nhớ vào hồ sơ dài hạn: '{key or 'Thông tin'}: {value}'"

    elif action in ("forget", "delete", "remove"):
        if key and key in profile.get("notes", {}):
            del profile["notes"][key]
            save_user_profile(profile)
            return f"🗑️ Đã xóa ghi chú '{key}' khỏi hồ sơ."
        elif value and value in profile.get("facts", []):
            profile["facts"].remove(value)
            save_user_profile(profile)
            return f"🗑️ Đã xóa thông tin: '{value}' khỏi hồ sơ."
        else:
            return f"Không tìm thấy mục '{key or value}' trong hồ sơ để xóa."

    elif action in ("get", "read"):
        if key and key in profile.get("notes", {}):
            return f"📌 {key}: {profile['notes'][key]}"
        return "Không tìm thấy ghi chú."

    elif action == "list":
        lines = ["👤 **HỒ SƠ & TRÍ NHỚ DÀI HẠN CỦA TRỢ LÝ:**\n"]
        name = profile.get("user_name", "mày")
        title = profile.get("preferred_title", "mày")
        lines.append(f"• **Danh xưng:** `{title}` (Tên: `{name}`)")
        facts = profile.get("facts", [])
        if facts:
            lines.append("\n• **Điều đã ghi nhớ:**")
            for f in facts:
                lines.append(f"  - {f}")
        notes = profile.get("notes", {})
        if notes:
            lines.append("\n• **Ghi chú quan trọng:**")
            for k, v in notes.items():
                lines.append(f"  - **{k}**: {v}")
        return "\n".join(lines)

    else:
        return f"Error: Hành động '{action}' không hợp lệ. Chọn 'remember', 'forget', 'get', hoặc 'list'."

YOUTH_MUSIC_PLAYLISTS = [
    {"title": "Top Nhạc Trẻ Gây Nghiện Mới Nhất", "url": "https://www.youtube.com/watch?v=1F3y6rUqFvY"},
    {"title": "V-Pop Acoustic Chill Buổi Tối", "url": "https://www.youtube.com/watch?v=kXYiU_JCYtU"},
    {"title": "Nhạc Trẻ Ballad Tâm Trạng Hay Nhất", "url": "https://www.youtube.com/watch?v=kJQP7kiw5Fk"},
    {"title": "Chill Hits Lofi Nhạc Trẻ Thư Giãn", "url": "https://www.youtube.com/watch?v=0k7b3jYl1b4"},
    {"title": "Playlist Nhạc Trẻ Hot TikTok Thịnh Hành", "url": "https://www.youtube.com/results?search_query=list+nhac+tre+moi+nhat&sp=EgIQAw%253D%253D"}
]

def launch_chrome_cdp(target_url: Optional[str] = None) -> tuple[bool, str]:
    """Khởi động Google Chrome thông qua file script start_chrome.bat và thực hiện kết nối điều khiển CDP Port 9222."""
    import os
    import time
    import urllib.request
    import urllib.parse
    import json

    bat_path = r"D:\install\CODE\AntigravityTelegramBot\AI_LIVE\start_chrome.bat"
    if not os.path.exists(bat_path):
        return False, f"Không tìm thấy file batch: {bat_path}"

    try:
        subprocess.Popen([bat_path], shell=True)
    except Exception as e:
        return False, f"Lỗi khi khởi chạy file start_chrome.bat: {str(e)}"

    # Chờ Chrome và CDP port 9222 sẵn sàng
    time.sleep(3.0)

    cdp_connected = False
    for _ in range(6):
        try:
            with urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=2) as resp:
                if resp.status == 200:
                    cdp_connected = True
                    break
        except Exception:
            time.sleep(1.0)

    if not cdp_connected:
        return False, "Đã chạy start_chrome.bat nhưng không thể kết nối tới CDP Port 9222 sau 8 giây."

    # Nếu có target_url (ví dụ link YouTube), mở tab mới qua CDP API
    if target_url:
        try:
            req_url = f"http://127.0.0.1:9222/json/new?{urllib.parse.quote(target_url, safe=':/?&=%')}"
            req = urllib.request.Request(req_url, method="PUT")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode())
                logger.info(f"CDP mở tab thành công: {data.get('url')}")
        except Exception as e:
            logger.warning(f"Lỗi khi mở URL qua CDP: {e}")

    return True, "CDP_9222_CONNECTED"

def perform_smart_pc_control(action: str, target: Optional[str] = None) -> str:
    """Executes smart PC orchestration commands safely without intrusive popups."""
    if not IS_WINDOWS:
        return "Tính năng điều khiển PC chỉ hỗ trợ trên máy chủ Windows."

    action = (action or "").lower().strip()

    if action in ("lock", "lock_screen", "lock_workstation"):
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        return "🔒 Đã khóa màn hình máy tính (Lock Workstation) thành công."

    elif action in ("open_app", "launch_app"):
        if not target:
            return "Error: Vui lòng cung cấp tên ứng dụng hoặc game cần mở (target)."
        tgt = target.lower().strip()
        if "steam" in tgt:
            cmd = "start steam:"
        elif "code" in tgt or "vscode" in tgt or "vs code" in tgt:
            cmd = "code"
        elif "spotify" in tgt:
            cmd = "start spotify:"
        elif "discord" in tgt:
            cmd = "start discord:"
        elif "chrome" in tgt:
            ok, res = launch_chrome_cdp()
            if ok:
                return f"🌐 Đã khởi chạy Google Chrome (Cổng AI CDP: 9222, Profile: `C:\\chrome-debug-profile`) thành công."
            else:
                return f"Lỗi khi mở Chrome: {res}"
        elif "edge" in tgt:
            cmd = "start msedge"
        else:
            cmd = f"start {target}"

        try:
            subprocess.Popen(cmd, shell=True)
            return f"🚀 Đã khởi chạy ứng dụng **{target}** thành công."
        except Exception as e:
            return f"Lỗi khi mở ứng dụng {target}: {str(e)}"

    elif action in ("open_url", "web_search"):
        if not target:
            return "Error: Vui lòng cung cấp URL hoặc từ khóa tìm kiếm (target)."
        import webbrowser
        url = target if target.startswith(("http://", "https://")) else f"https://www.google.com/search?q={urllib.parse.quote(target)}"
        try:
            webbrowser.open(url)
            return f"🌐 Đã mở trình duyệt: `{url[:100]}`"
        except Exception as e:
            return f"Lỗi khi mở URL: {str(e)}"

    elif action in ("open_music", "play_music", "music"):
        import random
        chosen = random.choice(YOUTH_MUSIC_PLAYLISTS)
        m_title = chosen["title"]
        m_url = chosen["url"]
        ok, res = launch_chrome_cdp(m_url)
        if ok:
            return f"🎵 Đã mở ngẫu nhiên: **{m_title}** trên Google Chrome (Cổng AI CDP: 9222, Profile: `C:\\chrome-debug-profile`)!\n🔗 `{m_url}`\n\n*(AI đã sẵn sàng kết nối cổng 9222 để điều khiển dừng/phát hoặc đổi bài theo yêu cầu)*"
        else:
            return f"Lỗi khi mở Chrome phát nhạc: {res}"

    elif action in ("clean_temp", "clean_disk"):
        temp_dir = Path(tempfile.gettempdir())
        removed_count = 0
        freed_bytes = 0
        now = time.time()
        for p in list(temp_dir.glob("*")):
            try:
                if p.is_file() and (now - p.stat().st_mtime > 7200):
                    sz = p.stat().st_size
                    p.unlink(missing_ok=True)
                    removed_count += 1
                    freed_bytes += sz
            except Exception:
                pass
        freed_mb = freed_bytes / (1024 * 1024)
        return f"🧹 Đã dọn dẹp thư mục tạm: Đã xóa {removed_count} tệp tin thừa, giải phóng {freed_mb:.1f} MB."

    else:
        return f"Error: Hành động '{action}' không hợp lệ. Chọn 'lock', 'open_app', 'open_url', 'open_music', hoặc 'clean_temp'."

VOICE_CACHE_DIR = BASE_DIR / "voice_cache"
VOICE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

def clean_text_for_speech(text: str) -> str:
    """Cleans markdown syntax, URLs, and command blocks for natural speech."""
    import re
    text = re.sub(r"```[\s\S]*?```", "Mã lệnh đính kèm.", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\|[\s\-:|]+\|", "", text)
    text = re.sub(r"^[•\-\*]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{2,}", ". ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()

async def generate_vietnamese_voice(text: str, voice: str = "vi-VN-HoaiMyNeural") -> Optional[Path]:
    """Generates an mp3 voice audio file using Microsoft Hoai My Neural TTS."""
    clean_txt = clean_text_for_speech(text)
    if not clean_txt:
        return None
    if len(clean_txt) > 1200:
        clean_txt = clean_txt[:1200] + "... Dài quá tao chỉ đọc đến đây thôi, phần còn lại tự xem trên màn hình đi mày!"

    out_file = VOICE_CACHE_DIR / f"voice_{int(time.time()*1000)}.mp3"
    try:
        import edge_tts
        comm = edge_tts.Communicate(clean_txt, voice=voice)
        await comm.save(str(out_file))
        if out_file.exists() and out_file.stat().st_size > 500:
            return out_file
    except Exception as e:
        logging.error(f"Lỗi khi tạo giọng nói TTS: {e}")
    return None

def add_cron_job(
    name: str,
    schedule_type: str,
    schedule_value: str,
    action: str = "health_report",
    command: str = "",
    enabled: bool = True
) -> Dict[str, Any]:
    import uuid
    jobs = load_cron_jobs()
    job_id = f"cron_{uuid.uuid4().hex[:6]}"
    entry = {
        "id": job_id,
        "name": name.strip(),
        "schedule_type": schedule_type.strip().lower(),
        "schedule_value": schedule_value.strip(),
        "action": action.strip().lower(),
        "command": command.strip(),
        "enabled": enabled,
        "last_run": None,
        "created_at": time.time()
    }
    jobs.append(entry)
    save_cron_jobs(jobs)
    return entry

def delete_cron_job(job_id: str) -> bool:
    jobs = load_cron_jobs()
    new_jobs = [j for j in jobs if j.get("id") != job_id]
    if len(new_jobs) != len(jobs):
        save_cron_jobs(new_jobs)
        return True
    return False

def toggle_cron_job(job_id: str, enabled: Optional[bool] = None) -> Optional[bool]:
    jobs = load_cron_jobs()
    found_state = None
    for j in jobs:
        if j.get("id") == job_id:
            if enabled is None:
                j["enabled"] = not j.get("enabled", True)
            else:
                j["enabled"] = enabled
            found_state = j["enabled"]
            break
    if found_state is not None:
        save_cron_jobs(jobs)
    return found_state

def list_cron_jobs_text() -> str:
    jobs = load_cron_jobs()
    if not jobs:
        return "Hiện chưa có lịch trình tự động hóa định kỳ nào được thiết lập."
    lines = ["🕒 **DANH SÁCH LỊCH TRÌNH TỰ ĐỘNG HÓA ĐỊNH KỲ (CRON JOBS):**\n"]
    for j in jobs:
        status_icon = "🟢 Đang bật" if j.get("enabled", True) else "⚪ Đã tắt"
        stype = j.get("schedule_type", "daily")
        sval = j.get("schedule_value", "")
        if stype == "daily":
            sched_str = f"Hàng ngày lúc `{sval}`"
        else:
            sched_str = f"Mỗi `{sval}` phút"
        
        act = j.get("action", "health_report")
        act_map = {
            "health_report": "Báo cáo sức khỏe PC",
            "screenshot": "Chụp ảnh Desktop",
            "morning_briefing": "Bản tin Chào Buổi Sáng",
            "evening_checkin": "Chăm sóc Buổi Tối",
            "shell_command": f"Lệnh shell: `{j.get('command')[:40]}`",
            "ai_prompt": f"Lời nhắc AI: `{j.get('command')[:40]}`"
        }
        act_desc = act_map.get(act, f"`{act}`")
        last_t = j.get("last_run")
        if last_t:
            last_str = datetime.fromtimestamp(last_t).strftime("%Y-%m-%d %H:%M:%S")
        else:
            last_str = "Chưa chạy lần nào"
        lines.append(
            f"• 🆔 `{j.get('id')}`: **{j.get('name')}** ({status_icon})\n"
            f"   ⏱️ Chu kỳ: {sched_str} | Tác vụ: {act_desc}\n"
            f"   📅 Lần chạy gần nhất: `{last_str}`\n"
        )
    return "\n".join(lines)

async def perform_web_search(query: str, num_results: int = 5) -> str:
    """Performs web search using DuckDuckGo HTML endpoint and Google fallback."""
    num_results = min(max(1, num_results), 10)
    results = []
    
    # 1. Primary: DuckDuckGo HTML endpoint (extremely reliable, no token needed)
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
            resp = await client.post("https://html.duckduckgo.com/html/", data={"q": query})
            if resp.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                bodies = soup.find_all("div", class_="result__body")
                for r in bodies[:num_results]:
                    title_tag = r.find("h2")
                    link_tag = r.find("a", class_="result__url")
                    snippet_tag = r.find("a", class_="result__snippet")
                    if title_tag and link_tag:
                        t = title_tag.get_text(strip=True)
                        href = link_tag.get("href", "").strip()
                        snip = snippet_tag.get_text(strip=True) if snippet_tag else ""
                        results.append(f"• **[{t}]({href})**\n  {snip}")
    except Exception:
        pass

    # 2. Fallback: DuckDuckGo Instant Answer API
    if not results:
        try:
            import urllib.parse
            async with httpx.AsyncClient(timeout=10.0) as client:
                api_url = f"https://api.duckduckgo.com/?{urllib.parse.urlencode({'q': query, 'format': 'json'})}"
                resp = await client.get(api_url)
                if resp.status_code == 200:
                    data = resp.json()
                    abstract = data.get("AbstractText", "")
                    heading = data.get("Heading", query)
                    source_url = data.get("AbstractURL", "")
                    if abstract:
                        results.append(f"• **[{heading}]({source_url})**\n  {abstract}")
        except Exception:
            pass

    if not results:
        return f"Không tìm thấy kết quả phù hợp cho tìm kiếm: '{query}'"

    header = f"🔍 **Kết quả tìm kiếm cho:** `{query}`\n\n"
    return header + "\n\n".join(results)

async def perform_read_webpage(url: str) -> str:
    """Fetches a webpage URL and extracts clean markdown/text content."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, headers=headers) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "form"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else url
        
        lines = []
        for p in soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "pre", "code"]):
            t = p.get_text().strip()
            if t and len(t) > 12:
                lines.append(t)

        body_text = "\n\n".join(lines)
        if not body_text:
            body_text = soup.get_text(separator="\n", strip=True)

        truncated = body_text[:10000]
        return f"📄 **Tiêu đề:** {title}\n🔗 **URL:** {url}\n\n**Nội dung trang web trích xuất:**\n```\n{truncated}\n```"
    except Exception as e:
        return f"Lỗi khi đọc trang web {url}: {str(e)}"

async def perform_clipboard_manager(action: str, text: Optional[str] = None) -> str:
    try:
        import pyperclip
        action = (action or "").strip().lower()
        if action == "read":
            content = pyperclip.paste()
            if not content:
                return "📋 Bộ nhớ tạm (Clipboard) hiện đang trống."
            truncated = content[:4000]
            count_chars = len(content)
            res = f"📋 **Nội dung trong Clipboard ({count_chars} ký tự):**\n```\n{truncated}\n```"
            if count_chars > 4000:
                res += f"\n*(Nội dung dài, đã cắt bớt 4000/{count_chars} ký tự)*"
            return res
        elif action == "write":
            if not text:
                return "Error: Vui lòng cung cấp nội dung 'text' cần sao chép vào clipboard."
            pyperclip.copy(text)
            return f"✅ Đã sao chép thành công vào Clipboard máy tính ({len(text)} ký tự):\n```\n{text[:300]}\n```"
        else:
            return f"Error: Hành động '{action}' không hợp lệ. Chỉ chấp nhận 'read' hoặc 'write'."
    except Exception as e:
        if not IS_WINDOWS:
            return f"Thông báo: Chức năng Clipboard không khả dụng trên môi trường headless Linux VPS (yêu cầu X11/Wayland). Chi tiết: {str(e)}"
        return f"Lỗi khi thao tác với Clipboard: {str(e)}"

async def perform_media_control(action: str, volume_percent: Optional[int] = None) -> str:
    if not IS_WINDOWS:
        return "Thông báo: Chức năng điều khiển Âm thanh & Media chỉ hỗ trợ trên máy tính Windows có hệ thống âm thanh, không khả dụng trên VPS Linux headless."
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        action = (action or "").strip().lower()

        def get_endpoint_volume():
            try:
                from pycaw.pycaw import AudioUtilities
                device = AudioUtilities.GetSpeakers()
                return device.EndpointVolume if device else None
            except Exception:
                return None

        if action in ("play_pause", "play", "pause"):
            pyautogui.press("playpause")
            return "🎵 Đã gửi lệnh: Phát / Tạm dừng nhạc (Play/Pause)."
        elif action in ("next", "next_track"):
            pyautogui.press("nexttrack")
            return "⏭️ Đã gửi lệnh: Chuyển sang bài tiếp theo (Next Track)."
        elif action in ("prev", "prev_track", "previous"):
            pyautogui.press("prevtrack")
            return "⏮️ Đã gửi lệnh: Quay lại bài trước (Previous Track)."
        elif action in ("volume_up", "volup", "up"):
            ep_vol = get_endpoint_volume()
            if ep_vol:
                curr = ep_vol.GetMasterVolumeLevelScalar()
                new_v = min(1.0, curr + 0.01)
                ep_vol.SetMasterVolumeLevelScalar(new_v, None)
                pct = round(ep_vol.GetMasterVolumeLevelScalar() * 100)
                return f"🔊 Đã tăng âm lượng (+1%): Hiện tại {pct}%."
            else:
                pyautogui.press("volumeup")
                return "🔊 Đã tăng âm lượng loa (+1 bước)."
        elif action in ("volume_down", "voldown", "down"):
            ep_vol = get_endpoint_volume()
            if ep_vol:
                curr = ep_vol.GetMasterVolumeLevelScalar()
                new_v = max(0.0, curr - 0.01)
                ep_vol.SetMasterVolumeLevelScalar(new_v, None)
                pct = round(ep_vol.GetMasterVolumeLevelScalar() * 100)
                return f"🔉 Đã giảm âm lượng (-1%): Hiện tại {pct}%."
            else:
                pyautogui.press("volumedown")
                return "🔉 Đã giảm âm lượng loa (-1 bước)."
        elif action in ("volume_mute", "mute", "unmute"):
            ep_vol = get_endpoint_volume()
            if ep_vol:
                is_muted = bool(ep_vol.GetMute())
                ep_vol.SetMute(not is_muted, None)
                state_str = "ĐÃ TẮT TIẾNG (Muted)" if not is_muted else "ĐÃ BẬT TIẾNG (Unmuted)"
                return f"🔇 {state_str}."
            else:
                pyautogui.press("volumemute")
                return "🔇 Đã bật/tắt chế độ tắt tiếng (Mute/Unmute)."
        elif action in ("set_volume", "set"):
            if volume_percent is None:
                return "Error: Vui lòng cung cấp giá trị 'volume_percent' (0 - 100)."
            pct = max(0, min(100, int(volume_percent)))
            ep_vol = get_endpoint_volume()
            if ep_vol:
                ep_vol.SetMasterVolumeLevelScalar(pct / 100.0, None)
                return f"🔊 Đã đặt mức âm lượng hệ thống: {pct}%."
            else:
                for _ in range(50):
                    pyautogui.press("volumedown")
                steps = pct // 2
                for _ in range(steps):
                    pyautogui.press("volumeup")
                return f"🔊 Đã điều chỉnh âm lượng hệ thống về xấp xỉ ~{pct}%."
        else:
            return f"Error: Hành động media không hợp lệ '{action}'. Hỗ trợ: play_pause, next_track, prev_track, volume_up, volume_down, volume_mute, set_volume."
    except Exception as e:
        return f"Lỗi khi điều khiển Media/Âm thanh: {str(e)}"

def make_progress_bar(percent: float, length: int = 10) -> str:
    clamped = max(0.0, min(100.0, percent))
    filled = int(round(length * clamped / 100))
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {clamped:.1f}%"

NON_DOWNLOAD_PROCESSES = {
    "antigravity.exe", "code.exe", "node.exe", "msmpeng.exe",
    "searchindexer.exe", "system", "registry", "python.exe",
    "pythonw.exe", "explorer.exe", "dwm.exe", "csrss.exe"
}

def get_steam_download_info() -> List[Dict[str, Any]]:
    """Helper that parses active Steam downloads from downloading patch chunks, manifests, and content logs."""
    if not IS_WINDOWS:
        return []
    potential_dirs = [
        Path(r"D:\Program Files\Steam"),
        Path(r"C:\Program Files (x86)\Steam"),
        Path(r"C:\Program Files\Steam"),
        Path(r"D:\Steam"),
        Path(r"E:\Steam"),
    ]
    steam_dir = None
    for d in potential_dirs:
        if (d / "steam.exe").exists() or (d / "steamapps").exists():
            steam_dir = d
            break
    if not steam_dir:
        return []
    downloading_dir = steam_dir / "steamapps" / "downloading"
    if not downloading_dir.exists():
        return []
    patches = list(downloading_dir.glob("state_*_*.patch"))
    if not patches:
        return []
    results = []
    for patch_file in patches:
        m = re.search(r"state_(\d+)_(\d+)\.patch", patch_file.name)
        if not m:
            continue
        appid, depotid = m.group(1), m.group(2)
        manifest_file = steam_dir / "steamapps" / f"appmanifest_{appid}.acf"
        game_name = f"AppID {appid}"
        bytes_to_download = 0
        if manifest_file.exists():
            try:
                txt = manifest_file.read_text(encoding="utf-8", errors="replace")
                nm = re.search(r'"name"\s+"([^"]+)"', txt)
                if nm:
                    game_name = nm.group(1)
                btd = re.search(r'"BytesToDownload"\s+"(\d+)"', txt)
                if btd:
                    bytes_to_download = int(btd.group(1))
            except Exception:
                pass
        content_log = steam_dir / "logs" / "content_log.txt"
        total_chunks = 0
        speed_mbps = 0.0
        if content_log.exists():
            try:
                log_txt = content_log.read_text(encoding="utf-8", errors="replace")
                chunk_m = re.findall(rf"Downloading (\d+) chunks for depot {depotid}", log_txt)
                if chunk_m:
                    total_chunks = int(chunk_m[-1])
                speed_m = re.findall(r"Current download rate:\s+([\d\.]+)\s+Mbps", log_txt)
                if speed_m:
                    speed_mbps = float(speed_m[-1])
            except Exception:
                pass
        try:
            with open(patch_file, "rb") as f:
                data = f.read()
            downloaded_chunks = data.count(b"\x04\x01\x00\x00")
        except Exception:
            downloaded_chunks = 0
        if total_chunks > 0:
            pct = round((downloaded_chunks / total_chunks) * 100, 1)
            downloaded_gb = round((pct / 100) * (bytes_to_download / (1024**3)), 2)
            total_gb = round(bytes_to_download / (1024**3), 2)
        else:
            pct = 0.0
            downloaded_gb = 0.0
            total_gb = round(bytes_to_download / (1024**3), 2)
        results.append({
            "app_name": "Steam",
            "target_name": game_name,
            "percent": pct,
            "downloaded_str": f"{downloaded_gb:.2f} GB",
            "total_str": f"{total_gb:.2f} GB",
            "speed_mbps": speed_mbps,
            "match_procs": ["steam.exe", "steamservice.exe"]
        })
    return results

def get_browser_download_info() -> List[Dict[str, Any]]:
    """Inspects active in-progress downloads in Chromium browsers (Chrome, Edge, Brave, CocCoc)."""
    if not IS_WINDOWS:
        return []
    results = []
    localapp = os.environ.get("LOCALAPPDATA", "")
    browser_dbs = [
        ("Google Chrome", Path(localapp) / "Google" / "Chrome" / "User Data" / "Default" / "History", ["chrome.exe"]),
        ("Microsoft Edge", Path(localapp) / "Microsoft" / "Edge" / "User Data" / "Default" / "History", ["msedge.exe"]),
        ("Brave", Path(localapp) / "BraveSoftware" / "Brave-Browser" / "User Data" / "Default" / "History", ["brave.exe"]),
        ("Cốc Cốc", Path(localapp) / "CocCoc" / "Browser" / "User Data" / "Default" / "History", ["browser.exe", "coccoc.exe"]),
    ]
    import psutil
    running_procs = set()
    for p in psutil.process_iter(["name"]):
        try:
            n = p.info.get("name")
            if n:
                running_procs.add(n.lower())
        except Exception:
            pass

    for b_label, db_path, proc_names in browser_dbs:
        if not any(pn.lower() in running_procs for pn in proc_names):
            continue
        if db_path.exists():
            temp_db = Path(tempfile.gettempdir()) / f"{proc_names[0]}_hist_{os.getpid()}_{int(time.time()*1000)}.db"
            try:
                shutil.copy2(db_path, temp_db)
                conn = sqlite3.connect(str(temp_db), timeout=2.0)
                cur = conn.cursor()
                cur.execute("SELECT current_path, target_path, received_bytes, total_bytes FROM downloads WHERE state = 0")
                for cur_p, tgt_p, rec_b, tot_b in cur.fetchall():
                    raw_name = Path(tgt_p or cur_p).name or "download"
                    if raw_name.endswith(".crdownload"):
                        raw_name = raw_name[:-11]
                    clean_name = urllib.parse.unquote(raw_name.split("?")[0])
                    pct = round((rec_b / tot_b) * 100, 1) if tot_b and tot_b > 0 else 0.0
                    if pct >= 100.0 or (tot_b and rec_b >= tot_b > 0):
                        continue
                    rec_str = f"{rec_b/(1024**3):.2f} GB" if rec_b >= 1024**3 else f"{rec_b/(1024**2):.1f} MB"
                    tot_str = f"{tot_b/(1024**3):.2f} GB" if tot_b and tot_b >= 1024**3 else (f"{tot_b/(1024**2):.1f} MB" if tot_b else "Không rõ")
                    results.append({
                        "app_name": b_label,
                        "target_name": clean_name,
                        "percent": pct,
                        "downloaded_str": rec_str,
                        "total_str": tot_str,
                        "match_procs": proc_names
                    })
                conn.close()
            except Exception:
                pass
            finally:
                temp_db.unlink(missing_ok=True)
    return results

def get_idm_download_info() -> List[Dict[str, Any]]:
    """Inspects active downloads in Internet Download Manager (IDM) from registry."""
    if not IS_WINDOWS:
        return []
    results = []
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\DownloadManager") as key:
            num_subkeys, _, _ = winreg.QueryInfoKey(key)
            for i in range(num_subkeys):
                subkey_name = winreg.EnumKey(key, i)
                try:
                    with winreg.OpenKey(key, subkey_name) as sk:
                        num_v = winreg.QueryInfoKey(sk)[1]
                        vals = {}
                        for j in range(num_v):
                            vn, vv, _ = winreg.EnumValue(sk, j)
                            vals[vn] = vv
                        status = vals.get("Status", 3)
                        fs_raw = vals.get("FileSize")
                        dl_raw = vals.get("Downloaded")
                        tot_b = int.from_bytes(fs_raw, "little") if isinstance(fs_raw, bytes) else (fs_raw or 0)
                        rec_b = int.from_bytes(dl_raw, "little") if isinstance(dl_raw, bytes) else (dl_raw or 0)
                        if status == 1 or (status != 3 and 0 < rec_b < tot_b):
                            fname = vals.get("FileName") or vals.get("LocalFileName") or "IDM_Download"
                            clean_name = urllib.parse.unquote(Path(str(fname).split("?")[0]).name)
                            pct = round((rec_b / tot_b) * 100, 1) if tot_b > 0 else 0.0
                            if pct >= 100.0 or (tot_b > 0 and rec_b >= tot_b):
                                continue
                            rec_str = f"{rec_b/(1024**3):.2f} GB" if rec_b >= 1024**3 else f"{rec_b/(1024**2):.1f} MB"
                            tot_str = f"{tot_b/(1024**3):.2f} GB" if tot_b >= 1024**3 else f"{tot_b/(1024**2):.1f} MB"
                            results.append({
                                "app_name": "IDM",
                                "target_name": clean_name,
                                "percent": pct,
                                "downloaded_str": rec_str,
                                "total_str": tot_str,
                                "match_procs": ["idman.exe"]
                            })
                except Exception:
                    pass
    except Exception:
        pass
    return results

def get_all_active_downloads() -> List[Dict[str, Any]]:
    """Gathers all verifiable in-progress downloads across all applications."""
    all_dl = []
    all_dl.extend(get_steam_download_info())
    all_dl.extend(get_browser_download_info())
    all_dl.extend(get_idm_download_info())
    return all_dl

async def detect_heavy_network_consumers(min_kb_sec: float = 500.0, sample_duration: float = 0.25) -> Dict[str, Any]:
    """Detects verified active downloads and maps their real-time network transfer speed."""
    if not IS_WINDOWS:
        return {"count": 0, "downloads": [], "summary_text": "Tính năng này chỉ hỗ trợ trên máy chủ Windows."}
    import psutil

    # 1. Quick Check: Gather active downloads first
    active_downloads = get_all_active_downloads()
    if not active_downloads:
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "threshold_kb_sec": min_kb_sec,
            "count": 0,
            "downloads": [],
            "summary_text": f"Không có ứng dụng nào đang tải xuống (> {min_kb_sec:.0f} KB/s)."
        }

    # 2. Check if all active downloads already have reliable speed logs (e.g. Steam content_log)
    needs_io_sampling = any(dl.get("speed_mbps", 0.0) <= 0.0 for dl in active_downloads)

    proc_rates = {}
    running_procs = set()
    self_pid = os.getpid()

    if needs_io_sampling:
        samples1 = {}
        for p in psutil.process_iter(["pid", "name", "io_counters"]):
            try:
                p_name = p.info["name"].lower()
                running_procs.add(p_name)
                if p.info["pid"] == self_pid or p_name in NON_DOWNLOAD_PROCESSES:
                    continue
                io = p.info.get("io_counters")
                if io:
                    samples1[p.info["pid"]] = (p.info["name"], io.read_bytes + io.write_bytes)
            except Exception:
                pass

        await asyncio.sleep(sample_duration)

        for p in psutil.process_iter(["pid", "name", "io_counters"]):
            try:
                pid = p.info["pid"]
                if pid == self_pid or pid not in samples1:
                    continue
                name, b1 = samples1[pid]
                io = p.info.get("io_counters")
                if io:
                    b2 = io.read_bytes + io.write_bytes
                    rate_kb = (b2 - b1) / (sample_duration * 1024.0)
                    if rate_kb > 0:
                        k = name.lower()
                        proc_rates[k] = proc_rates.get(k, 0.0) + rate_kb
            except Exception:
                pass
    else:
        # Fast path: All active downloads have built-in speed logs (Steam)
        for p in psutil.process_iter(["name"]):
            try:
                n = p.info.get("name")
                if n:
                    running_procs.add(n.lower())
            except Exception:
                pass

    matched_downloads = []
    summary_lines = []

    for dl in active_downloads:
        app_name = dl["app_name"]
        target = dl["target_name"]
        pct = dl["percent"]
        if pct >= 100.0:
            continue
        d_str = dl["downloaded_str"]
        t_str = dl["total_str"]
        match_procs = [p.lower() for p in dl.get("match_procs", [])]

        # Process Liveness Guard: ensure at least one associated process is running
        if match_procs and not any(mp in running_procs for mp in match_procs):
            continue

        # Find measured speed
        measured_speed_kb = 0.0
        for mp in match_procs:
            if mp in proc_rates:
                measured_speed_kb += proc_rates[mp]

        speed_mbps = dl.get("speed_mbps", 0.0)
        effective_speed_kb = max(measured_speed_kb, speed_mbps * 125.0)

        # Speed Threshold Enforcement: only report if actually downloading >= min_kb_sec
        if effective_speed_kb < min_kb_sec:
            continue

        if measured_speed_kb > 0:
            speed_str = f"{measured_speed_kb/1024:.2f} MB/s" if measured_speed_kb >= 1024 else f"{measured_speed_kb:.0f} KB/s"
        elif speed_mbps > 0:
            speed_str = f"{speed_mbps/8:.2f} MB/s ({speed_mbps} Mbps)"
        else:
            speed_str = f"{effective_speed_kb:.0f} KB/s"

        dl_entry = {
            "app_name": app_name,
            "target_name": target,
            "percent": pct,
            "downloaded_str": d_str,
            "total_str": t_str,
            "speed_str": speed_str,
        }
        matched_downloads.append(dl_entry)
        summary_lines.append(f"• **{target}** ({app_name}): `{pct}%` ({d_str} / {t_str}) @ `{speed_str}`")

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "threshold_kb_sec": min_kb_sec,
        "count": len(matched_downloads),
        "downloads": matched_downloads,
        "summary_text": "\n".join(summary_lines) if summary_lines else f"Không có ứng dụng nào đang tải xuống (> {min_kb_sec:.0f} KB/s)."
    }

DOWNLOAD_TRACKER_FILE = BASE_DIR / "download_tracker.json"

def load_download_tracker() -> Dict[str, Any]:
    if not DOWNLOAD_TRACKER_FILE.exists():
        return {"tracked_downloads": {}, "auto_action": {"action": None, "armed": False, "armed_at": None, "initiated": False}}
    try:
        with open(DOWNLOAD_TRACKER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"tracked_downloads": {}, "auto_action": {"action": None, "armed": False, "armed_at": None, "initiated": False}}

def save_download_tracker(data: Dict[str, Any]):
    try:
        with open(DOWNLOAD_TRACKER_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def set_auto_shutdown_action(action: str) -> str:
    """Arms or cancels automatic shutdown/sleep when downloads finish."""
    action = action.lower().strip()
    tracker = load_download_tracker()
    auto_action = tracker.get("auto_action", {})

    if action in ("shutdown", "sleep"):
        auto_action["action"] = action
        auto_action["armed"] = True
        auto_action["armed_at"] = time.time()
        auto_action["initiated"] = False
        tracker["auto_action"] = auto_action
        save_download_tracker(tracker)

        act_desc = "TẮT MÁY" if action == "shutdown" else "SLEEP (Ngủ)"
        active_dls = get_all_active_downloads()
        dl_summary = f" (Hiện có {len(active_dls)} tiến trình đang tải)" if active_dls else " (Sẽ áp dụng khi có tiến trình tải)"
        return f"✅ Đã kích hoạt chế độ tự động **{act_desc}** sau khi tải xong toàn bộ game/tệp{dl_summary}. Khi hoàn tất 100%, BOT sẽ gửi cảnh báo Telegram đếm ngược 60 giây trước khi thực hiện."

    elif action in ("cancel", "hủy", "disable", "off"):
        auto_action["action"] = None
        auto_action["armed"] = False
        auto_action["initiated"] = False
        tracker["auto_action"] = auto_action
        save_download_tracker(tracker)
        if IS_WINDOWS:
            try:
                subprocess.run("shutdown /a", shell=True, capture_output=True)
            except Exception:
                pass
        return "✅ Đã hủy bỏ chế độ tự động tắt máy / sleep khi tải xong."

    elif action == "status":
        armed = auto_action.get("armed", False)
        act_type = auto_action.get("action", "Chưa đặt")
        st = "ĐANG BẬT 🟢" if armed else "TẮT ⚪"
        return f"📊 Trạng thái tự động hành động: {st} (Hành động: `{act_type}`)"

    else:
        return f"Error: Hành động không hợp lệ: '{action}'. Chọn 'shutdown', 'sleep', 'cancel', hoặc 'status'."

async def check_download_completion_events() -> Dict[str, Any]:
    """Inspects tracked downloads and returns newly completed items and any triggered auto-action."""
    if not IS_WINDOWS:
        return {"completed_items": [], "trigger_action": None}

    tracker = load_download_tracker()
    tracked = tracker.setdefault("tracked_downloads", {})
    auto_action = tracker.setdefault("auto_action", {"action": None, "armed": False, "armed_at": None, "initiated": False})

    current_dls = get_all_active_downloads()
    active_keys = {f"{dl['app_name']}:{dl['target_name']}": dl for dl in current_dls}

    # 1. Update or register currently active downloads
    for key, dl in active_keys.items():
        if key not in tracked:
            tracked[key] = {
                "app_name": dl["app_name"],
                "target_name": dl["target_name"],
                "total_str": dl.get("total_str", ""),
                "last_pct": dl.get("percent", 0.0),
                "completed": False,
                "first_seen": time.time()
            }
        else:
            tracked[key]["last_pct"] = dl.get("percent", 0.0)
            tracked[key]["total_str"] = dl.get("total_str", "")

    # 2. Check completions among tracked items
    completed_items = []
    for key, item in list(tracked.items()):
        if item.get("completed"):
            continue

        # If currently active in live list, not completed yet
        if key in active_keys:
            continue

        # Disappeared from active list -> verify if actually completed
        is_done = False
        app = item.get("app_name")
        tgt = item.get("target_name")
        last_pct = item.get("last_pct", 0.0)

        if app == "Steam":
            try:
                for d in [Path(r"D:\install\SteamLibrary"), Path(r"C:\Program Files (x86)\Steam")]:
                    sa = d / "steamapps"
                    if not sa.exists():
                        continue
                    for mf in sa.glob("appmanifest_*.acf"):
                        try:
                            txt = mf.read_text(encoding="utf-8", errors="replace")
                            if f'"{tgt}"' in txt:
                                dl_folder = sa / "downloading"
                                appid_str = mf.name.split("_")[1].split(".")[0]
                                patch_files = list(dl_folder.glob(f"state_{appid_str}_*.patch")) if dl_folder.exists() else []
                                if not patch_files:
                                    is_done = True
                                    break
                        except Exception:
                            pass
                    if is_done:
                        break
            except Exception:
                pass

        elif app in ("Google Chrome", "Microsoft Edge", "Brave", "Cốc Cốc"):
            try:
                localapp = os.environ.get("LOCALAPPDATA", "")
                b_paths = {
                    "Google Chrome": Path(localapp) / "Google" / "Chrome" / "User Data" / "Default" / "History",
                    "Microsoft Edge": Path(localapp) / "Microsoft" / "Edge" / "User Data" / "Default" / "History",
                    "Brave": Path(localapp) / "BraveSoftware" / "Brave-Browser" / "User Data" / "Default" / "History",
                    "Cốc Cốc": Path(localapp) / "CocCoc" / "Browser" / "User Data" / "Default" / "History",
                }
                db_p = b_paths.get(app)
                if db_p and db_p.exists():
                    tmp_db = Path(tempfile.gettempdir()) / f"chk_hist_{int(time.time()*1000)}.db"
                    try:
                        shutil.copy2(db_p, tmp_db)
                        conn = sqlite3.connect(str(tmp_db), timeout=2.0)
                        cur = conn.cursor()
                        cur.execute("SELECT state, current_path, target_path FROM downloads WHERE state = 1 ORDER BY start_time DESC LIMIT 20")
                        for _, cp, tp in cur.fetchall():
                            f_n = urllib.parse.unquote(Path(tp or cp).name.split("?")[0])
                            if tgt in f_n or f_n in tgt:
                                is_done = True
                                break
                        conn.close()
                    except Exception:
                        pass
                    finally:
                        tmp_db.unlink(missing_ok=True)
            except Exception:
                pass

        elif app == "IDM":
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\DownloadManager") as key:
                    num_subkeys, _, _ = winreg.QueryInfoKey(key)
                    for i in range(num_subkeys):
                        sk_n = winreg.EnumKey(key, i)
                        try:
                            with winreg.OpenKey(key, sk_n) as sk:
                                num_v = winreg.QueryInfoKey(sk)[1]
                                vals = {}
                                for j in range(num_v):
                                    vn, vv, _ = winreg.EnumValue(sk, j)
                                    vals[vn] = vv
                                fn = vals.get("FileName") or vals.get("LocalFileName") or ""
                                clean_n = urllib.parse.unquote(Path(str(fn).split("?")[0]).name)
                                if (tgt in clean_n or clean_n in tgt) and vals.get("Status", 3) == 3:
                                    is_done = True
                                    break
                        except Exception:
                            pass
                        if is_done:
                            break
            except Exception:
                pass

        # Fallback heuristic: If last known pct was >= 95% and download disappeared from active
        if not is_done and last_pct >= 95.0:
            is_done = True

        if is_done:
            item["completed"] = True
            item["completed_at"] = time.time()
            completed_items.append(item)

    # 3. Check Auto-Action trigger
    trigger_action = None
    if auto_action.get("armed") and not auto_action.get("initiated"):
        uncompleted = [k for k, v in tracked.items() if not v.get("completed")]
        if not uncompleted and not active_keys:
            trigger_action = auto_action.get("action")
            auto_action["initiated"] = True
            auto_action["armed"] = False

    save_download_tracker(tracker)
    return {
        "completed_items": completed_items,
        "trigger_action": trigger_action
    }

def get_cpu_temperature() -> Optional[float]:
    """Reads the current CPU temperature in Celsius via Windows WMI or Linux sensors."""
    if IS_WINDOWS:
        try:
            import win32com.client
            wmi = win32com.client.GetObject('winmgmts:\\\\.\\root\\wmi')
            col = wmi.ExecQuery('SELECT CurrentTemperature FROM MSAcpi_ThermalZoneTemperature')
            temps = []
            for item in col:
                k = getattr(item, 'CurrentTemperature', None)
                if k is not None and k > 0:
                    c = (k / 10.0) - 273.15
                    if 0 < c < 150:
                        temps.append(c)
            if temps:
                return round(max(temps), 1)
        except Exception:
            pass
        return None
    else:
        try:
            import psutil
            sensors = getattr(psutil, 'sensors_temperatures', lambda: {})()
            for name, entries in sensors.items():
                for entry in entries:
                    if entry.current and 0 < entry.current < 150:
                        return round(float(entry.current), 1)
        except Exception:
            pass
        return None

async def perform_system_health(action: str = "summary", pid: Optional[int] = None, name: Optional[str] = None) -> str:
    try:
        import psutil
        action = (action or "summary").strip().lower()
        if action == "summary":
            cpu_pct = psutil.cpu_percent(interval=None)
            cpu_count = psutil.cpu_count(logical=True)
            cpu_freq = psutil.cpu_freq()
            freq_str = f" @ {cpu_freq.current:.0f}MHz" if cpu_freq else ""

            cpu_temp = get_cpu_temperature()
            temp_str = f" | 🌡️ `{cpu_temp:.1f}°C`" if cpu_temp is not None else ""

            vm = psutil.virtual_memory()
            total_ram_gb = vm.total / (1024**3)
            used_ram_gb = vm.used / (1024**3)

            disk_lines = []
            if IS_WINDOWS:
                for drive in ["C:\\", "D:\\"]:
                    if Path(drive).exists():
                        try:
                            du = psutil.disk_usage(drive)
                            disk_lines.append(f"  • **Ổ {drive[:2]}**: {make_progress_bar(du.percent)} ({du.used/(1024**3):.1f} / {du.total/(1024**3):.1f} GB)")
                        except Exception:
                            pass
            else:
                try:
                    du = psutil.disk_usage("/")
                    disk_lines.append(f"  • **Root (/)**: {make_progress_bar(du.percent)} ({du.used/(1024**3):.1f} / {du.total/(1024**3):.1f} GB)")
                except Exception:
                    pass

            boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
            os_name = f"Windows ({platform.release()} {platform.version()})" if IS_WINDOWS else "Ubuntu Linux Server"

            return (
                f"📊 **BẢNG ĐIỀU KHIỂN SỨC KHỎE HỆ THỐNG**\n\n"
                f"🖥️ **Hệ điều hành:** `{os_name}`\n"
                f"⏱️ **Khởi động từ:** `{boot_time}`\n\n"
                f"⚡ **CPU ({cpu_count} Cores{freq_str}){temp_str}:**\n"
                f"   {make_progress_bar(cpu_pct)}\n\n"
                f"🧠 **RAM ({used_ram_gb:.1f} / {total_ram_gb:.1f} GB):**\n"
                f"   {make_progress_bar(vm.percent)}\n\n"
                f"💾 **Dung lượng Ổ đĩa:**\n"
                + "\n".join(disk_lines)
            )

        elif action == "top_processes":
            num_cpus = psutil.cpu_count(logical=True) or 1
            procs = []
            for p in psutil.process_iter():
                try:
                    p.cpu_percent(None)
                    procs.append(p)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            await asyncio.sleep(0.3)

            grouped = {}
            for p in procs:
                try:
                    name = p.name() or "unknown"
                    pid = p.pid
                    if pid == 0 or name.lower() in ("system idle process", "idle"):
                        continue
                    raw_cpu = p.cpu_percent(None)
                    norm_cpu = raw_cpu / num_cpus
                    mem_info = p.memory_info()
                    mem_mb = mem_info.rss / (1024 * 1024)

                    key = name.lower()
                    if key not in grouped:
                        grouped[key] = {
                            "display_name": name,
                            "count": 0,
                            "cpu_percent": 0.0,
                            "memory_mb": 0.0,
                            "pids": []
                        }
                    grouped[key]["count"] += 1
                    grouped[key]["cpu_percent"] += norm_cpu
                    grouped[key]["memory_mb"] += mem_mb
                    grouped[key]["pids"].append(pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            by_ram = sorted(grouped.values(), key=lambda x: x["memory_mb"], reverse=True)[:5]
            by_cpu = sorted(grouped.values(), key=lambda x: x["cpu_percent"], reverse=True)[:5]

            KNOWN_PROCESS_DESCS = {
                "chrome.exe": "Trình duyệt Google Chrome",
                "msedge.exe": "Trình duyệt Microsoft Edge",
                "firefox.exe": "Trình duyệt Firefox",
                "svchost.exe": "Dịch vụ hệ thống Windows (Service Host)",
                "antigravity.exe": "Trợ lý AI Antigravity",
                "python.exe": "Trình thông dịch Python",
                "pythonw.exe": "Tiến trình nền Python (Bot Telegram)",
                "dwm.exe": "Desktop Window Manager (Giao diện Windows)",
                "explorer.exe": "Windows Explorer (Desktop & Taskbar)",
                "wmiprvse.exe": "Dịch vụ quản trị WMI Windows",
                "memcompression": "Bộ nhớ nén tối ưu RAM của Windows",
                "zalo.exe": "Ứng dụng chat Zalo",
                "ayugram.exe": "Ứng dụng chat Telegram (AyuGram)",
                "telegram.exe": "Ứng dụng chat Telegram",
                "code.exe": "Visual Studio Code",
                "steam.exe": "Nền tảng game Steam",
                "steamwebhelper.exe": "Trình duyệt ngầm của Steam",
                "system": "Nhân hệ điều hành Windows (Kernel)",
                "registry": "Cấu hình Windows Registry",
                "taskmgr.exe": "Task Manager (Trình quản lý tác vụ)",
                "msmpeng.exe": "Windows Defender Antivirus",
                "searchindexer.exe": "Chỉ mục tìm kiếm Windows Search",
                "audiodg.exe": "Dịch vụ âm thanh Windows Audio",
                "conhost.exe": "Windows Console Host",
            }

            lines = ["📋 **TOP ỨNG DỤNG TIÊU THỤ TÀI NGUYÊN (TASK MANAGER - PROCESSES):**\n"]
            lines.append("🧠 **Top 5 chiếm RAM:**")
            for g in by_ram:
                cnt = f" ({g['count']} tiến trình)" if g['count'] > 1 else ""
                mb = g['memory_mb']
                mem_str = f"{mb:,.0f} MB (~{mb/1024:.1f} GB)" if mb >= 1024 else f"{mb:,.0f} MB"
                desc = KNOWN_PROCESS_DESCS.get(g['display_name'].lower())
                desc_str = f" — ({desc})" if desc else ""
                lines.append(f"  • `{g['display_name']}`{cnt}: {mem_str}{desc_str}")

            lines.append("\n⚡ **Top 5 chiếm CPU:**")
            for g in by_cpu:
                cnt = f" ({g['count']} tiến trình)" if g['count'] > 1 else ""
                desc = KNOWN_PROCESS_DESCS.get(g['display_name'].lower())
                desc_str = f" — ({desc})" if desc else ""
                lines.append(f"  • `{g['display_name']}`{cnt}: {g['cpu_percent']:.1f}% CPU{desc_str}")

            return "\n".join(lines)

        elif action == "kill_process":
            if not pid and not name:
                return "Error: Cần cung cấp 'pid' hoặc 'name' của tiến trình cần dừng."
            
            terminated = []
            if pid:
                p = psutil.Process(pid)
                p_name = p.name()
                p.terminate()
                try:
                    p.wait(timeout=3)
                except psutil.TimeoutExpired:
                    p.kill()
                terminated.append(f"PID {pid} ({p_name})")
            elif name:
                for p in psutil.process_iter(['pid', 'name']):
                    try:
                        if p.info.get('name') and p.info['name'].lower() == name.lower():
                            proc_obj = psutil.Process(p.info['pid'])
                            proc_obj.terminate()
                            terminated.append(f"PID {p.info['pid']} ({p.info['name']})")
                    except Exception:
                        pass

            if terminated:
                return f"✅ Đã dừng thành công các tiến trình: {', '.join(terminated)}"
            else:
                return f"Không tìm thấy tiến trình đang chạy phù hợp với PID={pid} hoặc Name='{name}'."

        else:
            return f"Error: Hành động system_health không hợp lệ '{action}'. Chỉ chọn 'summary', 'top_processes', hoặc 'kill_process'."
    except Exception as e:
        return f"Lỗi khi kiểm tra sức khỏe hệ thống: {str(e)}"

async def perform_browser_automation(url: str, capture_screenshot: bool = True, wait_seconds: int = 3) -> str:
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    shots_dir = PROJECT_ROOT / "screenshots"
    shots_dir.mkdir(parents=True, exist_ok=True)
    shot_path = shots_dir / f"web_{int(time.time())}.png"

    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            try:
                await page.goto(url, wait_until="networkidle", timeout=25000)
            except Exception:
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                except Exception:
                    pass

            if wait_seconds > 0:
                await page.wait_for_timeout(min(wait_seconds, 10) * 1000)

            title = await page.title()
            
            try:
                body_text = await page.evaluate("() => document.body ? document.body.innerText : ''")
            except Exception:
                body_text = ""

            if capture_screenshot:
                await page.screenshot(path=str(shot_path), full_page=False)

            await context.close()
            await browser.close()

            clean_lines = [l.strip() for l in body_text.splitlines() if l.strip()]
            joined_text = "\n".join(clean_lines)[:6000]

            screen_note = f"\n📸 Đã chụp ảnh màn hình trang web (`{shot_path.name}`) và gửi trực tiếp qua Telegram." if capture_screenshot else ""
            return (
                f"📄 **Tiêu đề:** {title or url}\n"
                f"🔗 **URL:** {url}{screen_note}\n\n"
                f"**Nội dung trang web trích xuất (Playwright Rendered):**\n```\n{joined_text or '(Không có văn bản hiển thị)'}\n```"
            )
    except Exception as e:
        return f"Lỗi tự động hóa trình duyệt khi truy cập {url}: {str(e)}"

TASKS_DIR = BASE_DIR / "tasks"
TASKS_DIR.mkdir(parents=True, exist_ok=True)
TASKS_META_FILE = TASKS_DIR / "tasks.json"

class BackgroundTaskManager:
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = self._load_meta()
        self.completion_callbacks = []

    def _load_meta(self) -> Dict[str, Dict[str, Any]]:
        if not TASKS_META_FILE.exists():
            return {}
        try:
            with open(TASKS_META_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_meta(self):
        try:
            serializable = {}
            for tid, t in self.tasks.items():
                copy_t = dict(t)
                copy_t.pop("proc", None)
                copy_t.pop("log_fh", None)
                serializable[tid] = copy_t
            with open(TASKS_META_FILE, "w", encoding="utf-8") as f:
                json.dump(serializable, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def register_callback(self, cb):
        self.completion_callbacks.append(cb)

    async def start_task(self, command: str, description: str = "", chat_id: Optional[int] = None) -> Dict[str, Any]:
        import uuid
        task_id = f"bg_{uuid.uuid4().hex[:8]}"
        log_file = TASKS_DIR / f"{task_id}.log"

        fh = open(log_file, "a", encoding="utf-8", errors="replace", buffering=1)
        fh.write(f"=== Tác vụ bắt đầu lúc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        fh.write(f"Lệnh: {command}\nMô tả: {description}\n\n")

        kwargs = {
            "stdout": fh,
            "stderr": subprocess.STDOUT,
            "cwd": str(PROJECT_ROOT),
        }
        if IS_WINDOWS:
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        proc = await asyncio.create_subprocess_shell(command, **kwargs)

        task_entry = {
            "task_id": task_id,
            "command": command,
            "description": description or (command[:40] + ".."),
            "start_time": time.time(),
            "end_time": None,
            "status": "running",
            "exit_code": None,
            "pid": proc.pid,
            "log_file": str(log_file),
            "proc": proc,
            "log_fh": fh,
            "chat_id": chat_id
        }
        self.tasks[task_id] = task_entry
        self._save_meta()

        asyncio.create_task(self._monitor_task(task_id))
        return task_entry

    async def _monitor_task(self, task_id: str):
        t = self.tasks.get(task_id)
        if not t:
            return
        proc = t.get("proc")
        fh = t.get("log_fh")
        try:
            if proc:
                exit_code = await proc.wait()
            else:
                exit_code = 0
            t["exit_code"] = exit_code
            t["end_time"] = time.time()
            t["status"] = "completed" if exit_code == 0 else f"failed (code {exit_code})"
        except Exception as e:
            t["status"] = f"error: {str(e)}"
            t["end_time"] = time.time()
        finally:
            if fh:
                try:
                    fh.write(f"\n=== Tác vụ kết thúc lúc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Mã thoát: {t.get('exit_code')}) ===\n")
                    fh.close()
                except Exception:
                    pass
            self._save_meta()

        # Notify callbacks
        for cb in self.completion_callbacks:
            try:
                res = cb(t)
                if asyncio.iscoroutine(res):
                    await res
            except Exception:
                pass

    def get_status(self, task_id: str, tail_lines: int = 25) -> str:
        t = self.tasks.get(task_id)
        if not t:
            return f"Error: Không tìm thấy tác vụ `{task_id}`"
        
        status = t.get("status", "unknown")
        start_t = t.get("start_time", time.time())
        end_t = t.get("end_time") or time.time()
        elapsed = int(end_t - start_t)
        m, s = divmod(elapsed, 60)
        h, m = divmod(m, 60)
        duration_str = f"{h}h {m}m {s}s" if h else (f"{m}m {s}s" if m else f"{s}s")
        
        log_file = Path(t.get("log_file", ""))
        recent_log = "(Chưa có log)"
        if log_file.exists():
            try:
                with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                    recent_log = "".join(lines[-tail_lines:]) if lines else "(Tác vụ chưa có đầu ra)"
            except Exception as e:
                recent_log = f"(Lỗi đọc log: {e})"

        return (
            f"📊 **Trạng thái tác vụ:** `{task_id}`\n"
            f"📋 **Mô tả:** {t.get('description')}\n"
            f"💻 **Lệnh:** `{t.get('command')}`\n"
            f"🔄 **Tình trạng:** `{status}` (PID: {t.get('pid')})\n"
            f"⏱️ **Thời lượng:** {duration_str}\n"
            f"📄 **{tail_lines} dòng log gần nhất:**\n```\n{recent_log[:4000]}\n```"
        )

    def kill_task(self, task_id: str) -> str:
        t = self.tasks.get(task_id)
        if not t:
            return f"Error: Không tìm thấy tác vụ `{task_id}`"
        if t.get("status") != "running":
            return f"Tác vụ `{task_id}` không còn chạy (trạng thái: {t.get('status')})"
        
        proc = t.get("proc")
        pid = t.get("pid")
        if proc:
            try:
                proc.kill()
            except Exception:
                pass
        if pid:
            try:
                if IS_WINDOWS:
                    subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, capture_output=True)
                else:
                    subprocess.run(f"kill -9 {pid}", shell=True, capture_output=True)
            except Exception:
                pass
        t["status"] = "terminated"
        t["end_time"] = time.time()
        self._save_meta()
        return f"✅ Đã buộc dừng tác vụ `{task_id}` (PID: {pid}) thành công."

    def list_tasks(self) -> str:
        if not self.tasks:
            return "Hiện không có tác vụ chạy ngầm nào trong danh sách."
        
        lines = ["📋 **DANH SÁCH CÁC TÁC VỤ CHẠY NGẦM:**\n"]
        sorted_tasks = sorted(self.tasks.values(), key=lambda x: x.get("start_time", 0), reverse=True)[:10]
        for t in sorted_tasks:
            tid = t.get("task_id")
            desc = t.get("description")
            status = t.get("status")
            status_icon = "🟢" if status == "running" else ("✅" if "completed" in status else "❌")
            lines.append(f"{status_icon} `{tid}` - **{desc}**\n   Trạng thái: `{status}` | Lệnh: `{t.get('command')[:60]}`")
        return "\n".join(lines)

task_manager = BackgroundTaskManager()

def resolve_path(filepath: str) -> Path:
    p = Path(filepath.strip())
    if p.is_absolute():
        return p
    if (PROJECT_ROOT / p).exists():
        return PROJECT_ROOT / p
    if (BASE_DIR / p).exists():
        return BASE_DIR / p
    return PROJECT_ROOT / p

async def get_steam_download_status() -> str:
    """Detects active Steam downloads by parsing real-time patch binary chunks and content log."""
    if not IS_WINDOWS:
        return "Công cụ này chỉ hỗ trợ trên máy chủ Windows có cài đặt ứng dụng Steam."
    results = get_steam_download_info()
    if not results:
        return "Hiện tại không có game nào đang trong quá trình tải xuống trên Steam."
    return json.dumps({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "active_downloads": results
    }, ensure_ascii=False, indent=2)

async def execute_tool(name: str, args: Dict[str, Any]) -> str:
    """Executes a local tool on the server safely."""
    try:
        if name == "run_command":
            cmd = args.get("command", "").strip()
            if not cmd:
                return "Error: empty command"
            
            # Interactive Confirmation Gate for Destructive Commands
            if is_dangerous_command(cmd) and not args.get("__confirmed__"):
                return f"__CONFIRMATION_REQUIRED__:{cmd}"

            # Protect aaPanel root on Linux from accidental wipes
            if not IS_WINDOWS and ("rm -rf /www" in cmd or "rm -rf /" in cmd):
                return "Error: Protected system directory cannot be deleted."
            if IS_WINDOWS and ("format " in cmd.lower() or "rd /s /q c:\\" in cmd.lower()):
                return "Error: Dangerous system drive operation blocked by safeguard."
            
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                creationflags=subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=90.0)
                out = stdout.decode("utf-8", errors="replace").strip()
                err = stderr.decode("utf-8", errors="replace").strip()
                result = []
                if out:
                    result.append(out)
                if err:
                    result.append(f"STDERR:\n{err}")
                res_text = "\n".join(result) if result else "(Command completed with no output)"
                # Limit output size to prevent context overflow
                return res_text[:6000]
            except asyncio.TimeoutError:
                try:
                    proc.kill()
                except Exception:
                    pass
                return "Error: Command timed out after 90 seconds."

        elif name == "view_file":
            filepath = args.get("path", "").strip()
            p = resolve_path(filepath)
            if not p.exists() or not p.is_file():
                return f"Error: File not found: {filepath}"
            
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            
            start = max(1, args.get("start_line", 1)) - 1
            end = args.get("end_line", len(lines))
            selected = lines[start:end]
            numbered = [f"{i+start+1}: {line}" for i, line in enumerate(selected)]
            return "".join(numbered)[:8000]

        elif name == "write_file":
            filepath = args.get("path", "").strip()
            content = args.get("content", "")
            p = resolve_path(filepath)
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote {len(content)} characters to {p.name}"

        elif name == "list_dir":
            dirpath = args.get("path", "").strip()
            p = resolve_path(dirpath) if dirpath else PROJECT_ROOT
            if not p.exists() or not p.is_dir():
                return f"Error: Directory not found: {dirpath}"
            
            items = []
            for item in sorted(p.iterdir()):
                prefix = "[DIR] " if item.is_dir() else "[FILE]"
                size = item.stat().st_size if item.is_file() else ""
                items.append(f"{prefix} {item.name} {size}")
            return "\n".join(items[:100]) if items else "(Empty directory)"

        elif name == "send_file_to_user":
            filepath = args.get("path", "").strip()
            p = resolve_path(filepath)
            if not p.exists() or not p.is_file():
                return f"Error: File not found: {filepath}"
            file_size_mb = p.stat().st_size / (1024 * 1024)
            if file_size_mb > 50.0:
                return f"Error: File is too large ({file_size_mb:.1f} MB). Telegram Bot limit is 50 MB."
            return f"Success: File '{p.name}' ({p.stat().st_size / 1024:.1f} KB) verified and queued for delivery to Telegram."

        elif name == "capture_screenshot":
            if not IS_WINDOWS:
                return "Error: Chức năng chụp màn hình chỉ hỗ trợ trên máy chủ Windows có màn hình hiển thị, không hỗ trợ trên VPS Linux headless."
            try:
                from PIL import ImageGrab
                shots_dir = PROJECT_ROOT / "screenshots"
                shots_dir.mkdir(parents=True, exist_ok=True)
                
                # Auto-prune older screenshots, keeping only the 30 most recent
                try:
                    all_shots = sorted(shots_dir.glob("screenshot_*.png"), key=lambda f: f.stat().st_mtime, reverse=True)
                    for old_shot in all_shots[30:]:
                        old_shot.unlink(missing_ok=True)
                except Exception:
                    pass

                shot_path = shots_dir / f"screenshot_{int(time.time())}.png"
                img = ImageGrab.grab()
                img.save(shot_path, format="PNG")
                return f"Success: Đã chụp màn hình và lưu tại {shot_path.name}"
            except Exception as ex:
                return f"Error capturing screenshot: {str(ex)}"

        elif name == "schedule_reminder":
            sec = max(1, int(args.get("delay_seconds", 60)))
            msg = args.get("reminder_text", "Lời nhắc từ Antigravity")
            add_persistent_reminder(sec, msg)
            m, s = divmod(sec, 60)
            h, m = divmod(m, 60)
            time_str = f"{h} giờ {m} phút {s} giây" if h else (f"{m} phút {s} giây" if m else f"{s} giây")
            return f"Success: Đã lên lịch và lưu bền vững vào hàng đợi sau {time_str}: '{msg}'"

        elif name == "web_search":
            query = args.get("query", "").strip()
            num = args.get("num_results", 5)
            return await perform_web_search(query, num)

        elif name == "read_webpage":
            url = args.get("url", "").strip()
            return await perform_read_webpage(url)

        elif name == "run_background_task":
            cmd = args.get("command", "").strip()
            desc = args.get("description", "").strip()
            if not cmd:
                return "Error: empty command"
            if is_dangerous_command(cmd) and not args.get("__confirmed__"):
                return f"__CONFIRMATION_REQUIRED__:{cmd}"
            task = await task_manager.start_task(cmd, desc)
            return (
                f"🚀 **Đã khởi chạy tác vụ ngầm thành công!**\n"
                f"🆔 **Task ID:** `{task['task_id']}` (PID: `{task['pid']}`)\n"
                f"📋 **Lệnh:** `{cmd}`\n"
                f"📄 **Tệp log:** `tasks/{task['task_id']}.log`\n\n"
                f"Tác vụ đang chạy độc lập trong nền. Khi hoàn thành, tao sẽ tự động gửi thông báo kết quả đến Telegram cho mày!"
            )

        elif name == "get_background_task_status":
            tid = args.get("task_id", "").strip()
            tail = int(args.get("tail_lines", 25))
            return task_manager.get_status(tid, tail)

        elif name == "kill_background_task":
            tid = args.get("task_id", "").strip()
            return task_manager.kill_task(tid)

        elif name == "list_background_tasks":
            return task_manager.list_tasks()

        elif name == "clipboard_manager":
            action = args.get("action", "read")
            text = args.get("text")
            return await perform_clipboard_manager(action, text)

        elif name == "media_control":
            action = args.get("action", "")
            vol_pct = args.get("volume_percent")
            return await perform_media_control(action, vol_pct)

        elif name == "system_health":
            action = args.get("action", "summary")
            pid = args.get("pid")
            pname = args.get("name")
            return await perform_system_health(action, pid, pname)

        elif name == "browser_automation":
            url = args.get("url", "").strip()
            cap = args.get("capture_screenshot", True)
            wait_sec = int(args.get("wait_seconds", 3))
            return await perform_browser_automation(url, cap, wait_sec)

        elif name == "manage_cron_job":
            act = args.get("action", "list").strip().lower()
            if act == "list":
                return list_cron_jobs_text()
            elif act == "add":
                jname = args.get("name") or "Lịch trình định kỳ"
                stype = args.get("schedule_type", "daily")
                sval = args.get("schedule_value", "08:00")
                jact = args.get("job_action", "health_report")
                cmd = args.get("command", "")
                entry = add_cron_job(jname, stype, sval, jact, cmd)
                return f"✅ Đã thiết lập lịch trình định kỳ thành công:\n🆔 `{entry['id']}` - **{entry['name']}** ({stype}: `{sval}` | Tác vụ: `{jact}`)"
            elif act == "delete":
                jid = args.get("job_id", "").strip()
                if not jid:
                    return "Error: Vui lòng cung cấp 'job_id' cần xóa."
                if delete_cron_job(jid):
                    return f"✅ Đã xóa lịch trình `{jid}` thành công."
                else:
                    return f"Error: Không tìm thấy lịch trình với ID `{jid}`."
            elif act == "toggle":
                jid = args.get("job_id", "").strip()
                if not jid:
                    return "Error: Vui lòng cung cấp 'job_id' cần bật/tắt."
                res = toggle_cron_job(jid)
                if res is not None:
                    st = "BẬT 🟢" if res else "TẮT ⚪"
                    return f"✅ Đã chuyển trạng thái lịch trình `{jid}` sang: {st}."
                else:
                    return f"Error: Không tìm thấy lịch trình với ID `{jid}`."
            else:
                return f"Error: Hành động '{act}' không hợp lệ. Chọn 'list', 'add', 'delete', hoặc 'toggle'."

        elif name == "get_steam_download_status":
            return await get_steam_download_status()

        elif name == "get_network_heavy_consumers":
            min_kb = float(args.get("min_kb_sec", 500.0))
            res = await detect_heavy_network_consumers(min_kb_sec=min_kb)
            return json.dumps(res, ensure_ascii=False, indent=2)

        elif name == "set_auto_shutdown_on_download_complete":
            act = args.get("action", "shutdown").lower().strip()
            return set_auto_shutdown_action(act)

        elif name == "manage_user_memory":
            act = args.get("action", "list")
            k = args.get("key")
            v = args.get("value")
            return manage_user_memory(act, k, v)

        elif name == "smart_pc_control":
            act = args.get("action", "lock")
            tgt = args.get("target")
            return perform_smart_pc_control(act, tgt)

        else:
            return f"Error: Unknown tool {name}"
    except Exception as e:
        return f"Tool Execution Error ({name}): {str(e)}"

class AntigravitySession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history: List[Dict[str, Any]] = []
        self.title: str = "Phiên mới"

    def add_user_message(self, text: str, image_b64: Optional[str] = None, mime_type: str = "image/jpeg", audio_b64: Optional[str] = None, audio_mime: str = "audio/ogg"):
        if not self.history:
            self.title = (text[:30] + "..") if len(text) > 30 else (text or "Âm thanh / Hình ảnh")
        
        parts: List[Dict[str, Any]] = []
        if text:
            parts.append({"text": text})
        if image_b64:
            parts.append({
                "inlineData": {
                    "mimeType": mime_type,
                    "data": image_b64
                }
            })
        if audio_b64:
            parts.append({
                "inlineData": {
                    "mimeType": audio_mime,
                    "data": audio_b64
                }
            })
        if not parts:
            parts.append({"text": "(Trống)"})
            
        self.history.append({
            "role": "user",
            "parts": parts
        })
        self.trim_history()

    def add_model_parts(self, parts: List[Dict[str, Any]]):
        self.history.append({
            "role": "model",
            "parts": parts
        })

    def add_tool_responses(self, responses: List[Dict[str, Any]]):
        parts = []
        for r in responses:
            item = {
                "name": r["name"],
                "response": {"output": r["output"]}
            }
            if r.get("id"):
                item["id"] = r["id"]
            parts.append({"functionResponse": item})
            
        if parts:
            self.history.append({
                "role": "user",
                "parts": parts
            })

    def prune_and_compact(self, max_turns: int = 22):
        """
        1. Media Pruning: Prunes bulky base64 inlineData from turns older than the last 2 turns.
        2. Context Compaction: If turns exceed max_turns, condenses the middle turns.
        """
        if not self.history:
            return

        # 1. Media Pruning (older than last 2 items)
        if len(self.history) > 2:
            for msg in self.history[:-2]:
                for part in msg.get("parts", []):
                    if "inlineData" in part:
                        mime = part["inlineData"].get("mimeType", "media")
                        part.pop("inlineData", None)
                        part["text"] = f"[{mime} đính kèm từ lượt trước đã được AI phân tích thành công]"

        # 2. Sliding Window Compaction
        if len(self.history) > max_turns:
            head = self.history[:2]
            tail = self.history[-12:]
            while tail and tail[0].get("role") != "user":
                tail.pop(0)
            
            num_pruned = len(self.history) - len(head) - len(tail)
            if num_pruned > 0:
                summary_user = {
                    "role": "user",
                    "parts": [{
                        "text": f"[Hệ thống: {num_pruned} lượt trao đổi trước đó đã được tự động nén lại để tối ưu hóa bộ nhớ và hiệu năng phản hồi]"
                    }]
                }
                summary_model = {
                    "role": "model",
                    "parts": [{
                        "text": "Tao đã nắm thóp toàn bộ tiến trình trao đổi trước đó rồi, cứ nói tiếp đi mày."
                    }]
                }
                self.history = head + [summary_user, summary_model] + tail

    def trim_history(self, max_turns: int = 24):
        self.prune_and_compact(max_turns=max_turns)

THINKING_BUDGET_MAP = {
    "minimal": 1024,
    "low": 1024,
    "medium": 8192,
    "high": 16384,
}

FAST_PATH_RULES = [
    {
        "patterns": [
            r"(top|tiến trình|ứng dụng|tác vụ).*(ngốn|chiếm|ăn|cao|nặng).*(cpu|ram|tài nguyên)",
            r"(ngốn|chiếm|ăn|xài).*(cpu|ram)",
            r"top.*(cpu|ram|tiến trình|process)",
            r"(kiểm tra|xem).*(tiến trình|process)",
        ],
        "tool": "system_health",
        "args": {"action": "top_processes"},
        "desc": "Top Tiến trình Tiêu thụ Tài nguyên"
    },
    {
        "patterns": [
            r"(tình trạng|sức khỏe|tài nguyên|thông số|cấu hình).*(máy|pc|server|hệ thống|phần cứng)",
            r"^(kiểm tra|check) (máy|pc|server|tài nguyên)$",
            r"^(pc|status|system info)$",
        ],
        "tool": "system_health",
        "args": {"action": "summary"},
        "desc": "Sức khỏe Hệ thống (CPU, RAM, Ổ đĩa)"
    },
    {
        "patterns": [
            r"(chụp|xem|bắn).*(màn hình|desktop|screen)",
            r"^(screenshot|chụp desktop)$",
        ],
        "tool": "capture_screenshot",
        "args": {},
        "desc": "Chụp Màn hình Desktop"
    },
    {
        "patterns": [
            r"(tiến độ|tốc độ|đang tải|tải).*(steam)",
            r"(steam).*(tiến độ|tốc độ|tải|load)",
        ],
        "tool": "get_steam_download_status",
        "args": {},
        "desc": "Tiến độ Tải Game Steam"
    },
    {
        "patterns": [
            r"(ngốn|hút|chiếm|ăn|tải).*(mạng|băng thông|internet)",
            r"(máy|có ai).*(đang tải gì|đang download gì)",
            r"(kiểm tra|check).*(tải mạng|download)",
        ],
        "tool": "get_network_heavy_consumers",
        "args": {},
        "desc": "Ứng dụng Ngốn Mạng & Tiến trình Tải xuống"
    },
    {
        "patterns": [
            r"(mở|bật|phát|nghe|play).*(nhạc|bài hát|music|lofi|youtube)",
            r"^(mở nhạc|bật nhạc)$",
        ],
        "tool": "smart_pc_control",
        "args": {"action": "open_music"},
        "desc": "Mở Nhạc Trẻ YouTube"
    },
    {
        "patterns": [
            r"(dọn|xóa).*(rác|temp|cache|tập tin thừa)",
            r"^(dọn rác|clean temp)$",
        ],
        "tool": "smart_pc_control",
        "args": {"action": "clean_temp"},
        "desc": "Dọn Dẹp Tệp Tin Tạm (Temp)"
    },
    {
        "patterns": [
            r"(tắt tiếng|mute|tắt âm)",
        ],
        "tool": "media_control",
        "args": {"action": "mute"},
        "desc": "Tắt tiếng (Mute)"
    },
    {
        "patterns": [
            r"(tăng âm lượng|bật to|cho to lên|tăng loa|volume up)",
        ],
        "tool": "media_control",
        "args": {"action": "volume_up"},
        "desc": "Tăng Âm lượng"
    },
    {
        "patterns": [
            r"(giảm âm lượng|bật nhỏ|cho bé lại|giảm loa|volume down)",
        ],
        "tool": "media_control",
        "args": {"action": "volume_down"},
        "desc": "Giảm Âm lượng"
    },
]

def match_fast_path_tool(text: str) -> Tuple[Optional[str], Optional[Dict[str, Any]], Optional[str]]:
    if not text:
        return None, None, None
    t = text.strip().lower()
    if any(neg in t for neg in ["không", "đừng", "chớ", "hủy", "thôi", "chưa"]):
        return None, None, None
    for rule in FAST_PATH_RULES:
        for p in rule["patterns"]:
            if re.search(p, t):
                return rule["tool"], rule["args"], rule.get("desc")
    return None, None, None

async def run_agent_turn(
    session: AntigravitySession,
    model_name: str = "gemini-3.8-flash-tiered",
    thinking_level: str = "medium"
) -> AsyncGenerator[Tuple[str, Any], None]:
    """Runs an autonomous turn with the Antigravity API and tool execution loop."""
    session.prune_and_compact(max_turns=20)
    access_token, project_id, user_email = await get_valid_token()
    
    endpoints = [
        "https://daily-cloudcode-pa.googleapis.com/v1internal:streamGenerateContent?alt=sse",
        "https://cloudcode-pa.googleapis.com/v1internal:streamGenerateContent?alt=sse",
    ]
    
    max_steps = 15
    step = 0
    budget = THINKING_BUDGET_MAP.get(thinking_level, 16384)
    has_generated_text = False

    # Fast-Path Check on the initial user turn
    if session.history and session.history[-1].get("role") == "user":
        last_parts = session.history[-1].get("parts", [])
        if len(last_parts) == 1 and "text" in last_parts[0] and not any(k in last_parts[0] for k in ("inlineData", "functionResponse")):
            user_text = last_parts[0]["text"]
            fast_tool, fast_args, fast_desc = match_fast_path_tool(user_text)
            if fast_tool:
                display_desc = fast_desc or fast_tool
                yield ("status", f"⚡ [Fast-Path] Đang thực thi: {display_desc}...")
                try:
                    fast_output = await execute_tool(fast_tool, fast_args)
                except Exception as ex:
                    fast_output = f"Lỗi thực thi công cụ {fast_tool}: {str(ex)}"
                
                yield ("tool_output", {
                    "tool": fast_tool,
                    "args": fast_args,
                    "output": fast_output
                })

                if fast_tool == "capture_screenshot" and IS_WINDOWS:
                    shots_dir = PROJECT_ROOT / "screenshots"
                    shots = sorted(shots_dir.glob("screenshot_*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
                    if shots:
                        yield ("send_file", {
                            "path": str(shots[0]),
                            "caption": "📸 Ảnh chụp màn hình máy tính Windows trực tiếp"
                        })

                # Augment prompt with freshly collected real-time data
                augmented_prompt = (
                    f"{user_text}\n\n"
                    f"[KẾT QUẢ THỰC THI CÔNG CỤ THỜI GIAN THỰC (FAST-PATH DATA)]:\n"
                    f"- Công cụ: `{fast_tool}`\n"
                    f"- Dữ liệu:\n{fast_output}\n\n"
                    f"(Hệ thống đã chạy sẵn công cụ này tại máy của người dùng và thu thập dữ liệu trên. "
                    f"Mày hãy lập tức phân tích dữ liệu, giải thích và bình luận bằng giọng điệu bố láo, cà khịa đặc trưng của mày mà KHÔNG CẦN gọi lại công cụ `{fast_tool}` nữa)."
                )
                last_parts[0]["text"] = augmented_prompt
                
                # Fast-path optimization: use low thinking budget so Gemini responds in ~2-3 seconds
                budget = min(budget, 4096)
                thinking_level = "low"
    
    while step < max_steps:
        step += 1
        yield ("status", f"⏳ Antigravity ({model_name} | {thinking_level.upper()}) đang suy nghĩ...")
        
        request_data = {
            "model": model_name,
            "project": project_id,
            "request": {
                "contents": session.history,
                "systemInstruction": {
                    "role": "system",
                    "parts": [{"text": get_dynamic_system_instruction()}]
                },
                "tools": AGENT_TOOLS,
                "generationConfig": {
                    "temperature": 0.2 if ("pro" in model_name or "opus" in model_name) else 0.4,
                    "thinkingConfig": {
                        "thinkingLevel": thinking_level,
                        "thinkingBudget": budget,
                        "includeThoughts": True
                    }
                }
            }
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "User-Agent": "antigravity/1.19.2 linux/x64",
            "Accept": "text/event-stream",
        }
        
        success = False
        last_error = None
        parts = []
        
        for ep in endpoints:
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    async with client.stream("POST", ep, headers=headers, json=request_data) as response:
                        if response.status_code == 200:
                            success = True
                            async for line in response.aiter_lines():
                                if line.startswith("data:"):
                                    raw = line[5:].strip()
                                    if not raw:
                                        continue
                                    try:
                                        chunk_json = json.loads(raw)
                                        cands = chunk_json.get("response", {}).get("candidates") or chunk_json.get("candidates") or []
                                        if cands:
                                            chunk_parts = cands[0].get("content", {}).get("parts", [])
                                            for p in chunk_parts:
                                                parts.append(p)
                                                if "text" in p and not p.get("thought"):
                                                    text_piece = p["text"]
                                                    if text_piece:
                                                        has_generated_text = True
                                                        yield ("text", text_piece)
                                    except Exception:
                                        pass
                            break
                        else:
                            try:
                                err_bytes = await response.aread()
                                err_str = err_bytes.decode("utf-8", errors="replace")[:200]
                            except Exception:
                                err_str = ""
                            last_error = f"API returned {response.status_code}: {err_str}"
            except Exception as ex:
                last_error = str(ex)
                
        if not success:
            yield ("error", f"Không thể kết nối tới Google Antigravity API: {last_error}")
            return

        if not parts:
            yield ("final", "Không nhận được nội dung phản hồi từ mô hình.")
            return

        session.add_model_parts(parts)
        
        tool_calls_to_run = []
        for part in parts:
            if "functionCall" in part:
                tool_calls_to_run.append(part["functionCall"])
                
        if tool_calls_to_run:
            executed_responses = []
            for fn in tool_calls_to_run:
                fn_name = fn.get("name", "")
                fn_args = fn.get("args", {})
                call_id = fn.get("id")
                
                # Friendly status display
                if fn_name == "run_command":
                    display_action = f"Lệnh `{fn_args.get('command')}`"
                elif fn_name in ("view_file", "write_file"):
                    display_action = f"File `{fn_args.get('path')}`"
                elif fn_name == "send_file_to_user":
                    display_action = f"Gửi tệp `{fn_args.get('path')}` qua Telegram"
                elif fn_name == "capture_screenshot":
                    display_action = "Chụp ảnh màn hình Desktop"
                elif fn_name == "schedule_reminder":
                    display_action = f"Hẹn giờ nhắc nhở ({fn_args.get('delay_seconds')}s)"
                elif fn_name == "web_search":
                    display_action = f"Tìm kiếm web `{fn_args.get('query')}`"
                elif fn_name == "read_webpage":
                    display_action = f"Đọc trang web `{fn_args.get('url')}`"
                elif fn_name == "run_background_task":
                    display_action = f"Khởi chạy tác vụ ngầm `{fn_args.get('command')}`"
                elif fn_name == "get_background_task_status":
                    display_action = f"Kiểm tra tác vụ ngầm `{fn_args.get('task_id')}`"
                elif fn_name == "kill_background_task":
                    display_action = f"Dừng tác vụ ngầm `{fn_args.get('task_id')}`"
                elif fn_name == "list_background_tasks":
                    display_action = "Danh sách tác vụ ngầm"
                elif fn_name == "clipboard_manager":
                    act = fn_args.get("action", "read")
                    display_action = f"Bộ nhớ tạm Clipboard ({'Đọc' if act == 'read' else 'Ghi'})"
                elif fn_name == "media_control":
                    display_action = f"Điều khiển Media/Loa (`{fn_args.get('action')}`)"
                elif fn_name == "system_health":
                    display_action = f"Kiểm tra Sức khỏe Hệ thống (`{fn_args.get('action', 'summary')}`)"
                elif fn_name == "browser_automation":
                    display_action = f"Duyệt web Playwright `{fn_args.get('url')}`"
                elif fn_name == "manage_cron_job":
                    act = fn_args.get("action", "list")
                    display_action = f"Quản lý Lịch định kỳ ({act})"
                elif fn_name == "get_steam_download_status":
                    display_action = "Đo đạc Tiến độ Tải Game Steam (Thời gian thực)"
                elif fn_name == "get_network_heavy_consumers":
                    display_action = "Kiểm tra Ứng dụng Ngốn Mạng & % Tải Xuống"
                else:
                    display_action = f"Công cụ {fn_name}"
                    
                yield ("status", f"⚙️ Đang thực thi: {display_action}...")
                
                tool_output = await execute_tool(fn_name, fn_args)

                # Check if command requires human confirmation
                if isinstance(tool_output, str) and tool_output.startswith("__CONFIRMATION_REQUIRED__:"):
                    cmd_to_confirm = tool_output.split(":", 1)[1]
                    yield ("require_confirmation", {
                        "command": cmd_to_confirm,
                        "tool": fn_name,
                        "args": fn_args,
                        "call_id": call_id
                    })
                    return

                yield ("tool_output", {
                    "tool": fn_name,
                    "args": fn_args,
                    "output": tool_output
                })

                if fn_name == "send_file_to_user":
                    filepath = fn_args.get("path", "").strip()
                    p = resolve_path(filepath)
                    if p.exists() and p.is_file() and p.stat().st_size <= 50 * 1024 * 1024:
                        yield ("send_file", {
                            "path": str(p),
                            "caption": fn_args.get("caption", "")
                        })

                elif fn_name == "capture_screenshot" and IS_WINDOWS:
                    shots_dir = PROJECT_ROOT / "screenshots"
                    shots = sorted(shots_dir.glob("screenshot_*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
                    if shots:
                        yield ("send_file", {
                            "path": str(shots[0]),
                            "caption": fn_args.get("caption") or "📸 Ảnh chụp màn hình máy tính Windows trực tiếp"
                        })

                elif fn_name == "browser_automation":
                    shots_dir = PROJECT_ROOT / "screenshots"
                    shots = sorted(shots_dir.glob("web_*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
                    if shots and (time.time() - shots[0].stat().st_mtime < 20):
                        yield ("send_file", {
                            "path": str(shots[0]),
                            "caption": f"🌐 Ảnh chụp trang web: {fn_args.get('url')}"
                        })

                elif fn_name == "schedule_reminder":
                    sec = max(1, int(fn_args.get("delay_seconds", 60)))
                    msg = fn_args.get("reminder_text", "Lời nhắc từ Antigravity")
                    yield ("schedule_reminder", {
                        "delay_seconds": sec,
                        "reminder_text": msg
                    })
                
                resp_entry = {
                    "name": fn_name,
                    "output": tool_output
                }
                if call_id:
                    resp_entry["id"] = call_id
                executed_responses.append(resp_entry)
                
            session.add_tool_responses(executed_responses)
        else:
            # If no tool was called, this turn is complete
            break

    # Bắt buộc tổng hợp phản hồi nếu mô hình chỉ chạy tools mà chưa kịp nói gì với người dùng
    if not has_generated_text:
        yield ("status", "✍️ Tao đang nặn câu trả lời cho mày...")
        synthesis_instruction = get_dynamic_system_instruction() + "\n\nQUY TẮC PHẢN HỒI: Dựa vào toàn bộ dữ liệu và kết quả các công cụ đã thực hiện ở trên, hãy trả lời câu hỏi của người dùng một cách trực tiếp, đầy đủ, xưng 'tao' gọi 'mày', giữ vững phong cách bố láo cà khịa đanh đá bằng tiếng Việt. Tuyệt đối không lặp lại câu lệnh shell thô."
        synth_request_data = {
            "model": model_name,
            "project": project_id,
            "request": {
                "contents": session.history,
                "systemInstruction": {
                    "role": "system",
                    "parts": [{"text": synthesis_instruction}]
                },
                "tools": AGENT_TOOLS,
                "toolConfig": {
                    "functionCallingConfig": {
                        "mode": "NONE"
                    }
                },
                "generationConfig": {
                    "temperature": 0.3,
                    "thinkingConfig": {
                        "thinkingLevel": thinking_level,
                        "thinkingBudget": budget,
                        "includeThoughts": True
                    }
                }
            }
        }
        
        synth_parts = []
        for ep in endpoints:
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    async with client.stream("POST", ep, headers=headers, json=synth_request_data) as response:
                        if response.status_code == 200:
                            async for line in response.aiter_lines():
                                if line.startswith("data:"):
                                    raw = line[5:].strip()
                                    if not raw:
                                        continue
                                    try:
                                        chunk_json = json.loads(raw)
                                        cands = chunk_json.get("response", {}).get("candidates") or chunk_json.get("candidates") or []
                                        if cands:
                                            chunk_parts = cands[0].get("content", {}).get("parts", [])
                                            for p in chunk_parts:
                                                synth_parts.append(p)
                                                if "text" in p and not p.get("thought"):
                                                    text_piece = p["text"]
                                                    if text_piece:
                                                        has_generated_text = True
                                                        yield ("text", text_piece)
                                    except Exception:
                                        pass
                            break
            except Exception:
                pass
                
        if synth_parts:
            session.add_model_parts(synth_parts)
            
    yield ("done", True)
