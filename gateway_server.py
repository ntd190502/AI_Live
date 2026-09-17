# -*- coding: utf-8 -*-
"""
Antigravity Live Gateway Server
--------------------------------
FastAPI + WebSocket Gateway server for Antigravity AI Agent.
Enables real-time duplex live voice calls and multimedia messaging from iOS (TrollStore app).
"""

import os
import sys
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass
import json
import time
import base64
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

# Add current directory to sys.path to import agent_core & antigravity_auth
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from agent_core import (
    AntigravitySession,
    run_agent_turn,
    generate_vietnamese_voice,
    IS_WINDOWS,
    PROJECT_ROOT
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [GATEWAY] %(levelname)s - %(message)s"
)
logger = logging.getLogger("AntigravityGateway")

app = FastAPI(
    title="Antigravity Live Gateway",
    description="Live Voice & Chat Gateway for iOS Antigravity Client",
    version="1.0.0"
)

# Allow all origins for local network & static IP access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active user sessions store (keyed by session_id)
sessions: Dict[str, AntigravitySession] = {}

def get_or_create_session(session_id: str = "default_ios") -> AntigravitySession:
    if session_id not in sessions:
        logger.info(f"Khởi tạo phiên hội thoại mới: {session_id}")
        sessions[session_id] = AntigravitySession(session_id=session_id)
    return sessions[session_id]

# Request Models
class ChatRequest(BaseModel):
    session_id: str = "default_ios"
    text: Optional[str] = ""
    image_b64: Optional[str] = None
    mime_type: Optional[str] = "image/jpeg"
    audio_b64: Optional[str] = None
    audio_mime: Optional[str] = "audio/wav"
    want_voice: bool = False
    model_name: str = "gemini-3.8-flash-tiered"
    thinking_level: str = "medium"

@app.get("/health")
async def health_check():
    """Health check endpoint to verify connectivity from iOS."""
    return {
        "status": "online",
        "service": "Antigravity Live Gateway",
        "platform": "Windows" if IS_WINDOWS else "Linux",
        "time": time.time(),
        "active_sessions": len(sessions)
    }

@app.get("/api/history/{session_id}")
async def get_history(session_id: str):
    """Retrieve chat history for a session."""
    session = sessions.get(session_id)
    if not session:
        return {"session_id": session_id, "messages": []}
    return {
        "session_id": session_id,
        "title": session.title,
        "history": session.history
    }

@app.post("/api/reset/{session_id}")
async def reset_session(session_id: str):
    """Reset a chat session."""
    if session_id in sessions:
        sessions[session_id].history.clear()
        sessions[session_id].title = "Phiên mới"
    return {"status": "ok", "message": f"Phiên {session_id} đã được làm mới."}

@app.post("/api/chat")
async def chat_api(req: ChatRequest):
    """
    Standard REST chat endpoint.
    Handles text, images, and audio payloads.
    """
    session = get_or_create_session(req.session_id)
    session.add_user_message(
        text=req.text or "",
        image_b64=req.image_b64,
        mime_type=req.mime_type or "image/jpeg",
        audio_b64=req.audio_b64,
        audio_mime=req.audio_mime or "audio/wav"
    )

    accumulated_text = []
    executed_tools = []
    sent_files = []
    status_updates = []

    try:
        async for event_type, data in run_agent_turn(
            session=session,
            model_name=req.model_name,
            thinking_level=req.thinking_level,
            is_live_call=req.want_voice
        ):
            if event_type == "text":
                accumulated_text.append(data)
            elif event_type == "status":
                status_updates.append(data)
            elif event_type == "tool_output":
                executed_tools.append(data)
            elif event_type == "send_file":
                sent_files.append(data)
            elif event_type == "error":
                raise HTTPException(status_code=500, detail=str(data))
    except Exception as e:
        logger.error(f"Lỗi khi chạy agent turn: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lỗi Agent: {str(e)}")

    full_reply = "".join(accumulated_text).strip()
    voice_b64 = None

    if req.want_voice and full_reply:
        try:
            voice_path = await generate_vietnamese_voice(full_reply)
            if voice_path and voice_path.exists():
                with open(voice_path, "rb") as vf:
                    voice_b64 = base64.b64encode(vf.read()).decode("utf-8")
        except Exception as ve:
            logger.warning(f"Không thể sinh giọng nói TTS: {ve}")

    return {
        "session_id": req.session_id,
        "reply": full_reply,
        "voice_b64": voice_b64,
        "tools_executed": executed_tools,
        "sent_files": sent_files,
        "status_updates": status_updates
    }

async def safe_send_json(ws: WebSocket, payload: dict) -> bool:
    try:
        await ws.send_json(payload)
        return True
    except Exception as ex:
        logger.warning(f"safe_send_json error ({type(ex).__name__}): {ex}")
        return False

@app.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    """
    Real-time Duplex Live Voice & Chat WebSocket Endpoint.
    
    Incoming Messages (JSON):
      - {"type": "chat_text", "session_id": "...", "text": "..."}
      - {"type": "voice_audio", "session_id": "...", "audio_b64": "...", "mime": "audio/wav", "live_call": true}
      - {"type": "cancel"} / {"type": "interrupt"}
      - {"type": "ping"}
      - {"type": "reset", "session_id": "..."}
      
    Outgoing Messages (JSON):
      - {"type": "status", "text": "..."}
      - {"type": "text_delta", "delta": "..."}
      - {"type": "tool_executed", "tool": "...", "output": "..."}
      - {"type": "voice_chunk", "audio_b64": "...", "full_text": "..."}
      - {"type": "screenshot", "image_b64": "...", "caption": "..."}
      - {"type": "turn_complete", "full_text": "..."}
      - {"type": "error", "message": "..."}
      - {"type": "pong", "time": ...}
    """
    await websocket.accept()
    logger.info("iOS Client đã kết nối vào WebSocket /ws/live!")

    current_turn_task: Optional[asyncio.Task] = None
    keepalive_active = True

    async def heartbeat_worker():
        while keepalive_active:
            try:
                await asyncio.sleep(3.0)
                if keepalive_active:
                    await safe_send_json(websocket, {"type": "ping"})
            except asyncio.CancelledError:
                break
            except Exception:
                break

    heartbeat_task = asyncio.create_task(heartbeat_worker())

    async def process_user_turn(session: AntigravitySession, is_live_call: bool):
        accumulated_text = []
        turn_start = time.time()
        try:
            async for event_type, data in run_agent_turn(
                session=session,
                model_name="gemini-3.8-flash-tiered",
                thinking_level="low",
                is_live_call=is_live_call
            ):
                if event_type == "status":
                    await safe_send_json(websocket, {"type": "status", "text": str(data)})
                elif event_type == "text":
                    accumulated_text.append(data)
                    await safe_send_json(websocket, {"type": "text_delta", "delta": data})
                elif event_type == "tool_output":
                    logger.info(f"Tool executed: {data.get('tool')}")
                    await safe_send_json(websocket, {
                        "type": "tool_executed",
                        "tool": data.get("tool"),
                        "output": str(data.get("output"))[:1000]
                    })
                elif event_type == "send_file":
                    f_path = data.get("path")
                    caption = data.get("caption", "")
                    if f_path and Path(f_path).exists():
                        try:
                            with open(f_path, "rb") as f:
                                img_b64 = base64.b64encode(f.read()).decode("utf-8")
                            await safe_send_json(websocket, {
                                "type": "screenshot",
                                "image_b64": img_b64,
                                "caption": caption
                            })
                        except Exception as fe:
                            logger.warning(f"Lỗi đọc file gửi: {fe}")
                elif event_type == "error":
                    logger.error(f"Agent error event: {data}")
                    await safe_send_json(websocket, {"type": "error", "message": str(data)})
                    return

            final_full_text = "".join(accumulated_text).strip()
            turn_elapsed = time.time() - turn_start
            logger.info(f"AI hoàn thành câu trả lời ({len(final_full_text)} ký tự, {turn_elapsed:.2f}s): '{final_full_text[:60]}...'")

            # Synthesize Hoài My voice for Live Calls
            if is_live_call and final_full_text:
                await safe_send_json(websocket, {"type": "status", "text": "Đang phát giọng nói Hoài My..."})
                try:
                    tts_start = time.time()
                    voice_path = await generate_vietnamese_voice(final_full_text)
                    if voice_path and voice_path.exists():
                        with open(voice_path, "rb") as vf:
                            v_b64 = base64.b64encode(vf.read()).decode("utf-8")
                        tts_elapsed = time.time() - tts_start
                        logger.info(f"Sinh voice TTS xong trong {tts_elapsed:.2f}s. Đang đẩy về iPhone...")
                        await safe_send_json(websocket, {
                            "type": "voice_chunk",
                            "audio_b64": v_b64,
                            "mime": "audio/mp3",
                            "full_text": final_full_text
                        })
                except Exception as ve:
                    logger.error(f"Lỗi tạo voice TTS: {ve}")

            await safe_send_json(websocket, {
                "type": "turn_complete",
                "full_text": final_full_text
            })

        except asyncio.CancelledError:
            logger.info("Lượt xử lý AI bị ngắt bởi người dùng (Barge-in / Cancel).")
        except Exception as ex:
            logger.error(f"Lỗi trong quá trình xử lý agent turn: {ex}", exc_info=True)
            await safe_send_json(websocket, {"type": "error", "message": f"Lỗi Agent: {str(ex)}"})

    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                msg = json.loads(raw_data)
            except Exception:
                await websocket.send_json({"type": "error", "message": "Dữ liệu JSON không hợp lệ."})
                continue

            msg_type = msg.get("type", "")
            session_id = msg.get("session_id", "default_ios")
            session = get_or_create_session(session_id)

            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "time": time.time()})
                continue

            elif msg_type in ("cancel", "interrupt"):
                if current_turn_task and not current_turn_task.done():
                    current_turn_task.cancel()
                    current_turn_task = None
                await safe_send_json(websocket, {"type": "status", "text": "Đã ngắt lời Antigravity."})
                await safe_send_json(websocket, {"type": "turn_complete", "full_text": ""})
                continue

            elif msg_type == "reset":
                if current_turn_task and not current_turn_task.done():
                    current_turn_task.cancel()
                    current_turn_task = None
                session.history.clear()
                session.title = "Phiên mới"
                await websocket.send_json({"type": "status", "text": "Đã làm mới phiên trò chuyện."})
                continue

            elif msg_type in ("chat_text", "voice_audio"):
                # If a previous turn is still computing, cancel it to support immediate barge-in / interruption
                if current_turn_task and not current_turn_task.done():
                    logger.info("Người dùng nói câu mới khi AI đang bận -> Hủy lượt cũ ngay lập tức (Barge-in).")
                    current_turn_task.cancel()
                    current_turn_task = None

                user_text = msg.get("text", "")
                audio_b64 = msg.get("audio_b64")
                audio_mime = msg.get("mime", "audio/wav")
                image_b64 = msg.get("image_b64")
                mime_type = msg.get("image_mime", "image/jpeg")
                is_live_call = (msg_type == "voice_audio") or msg.get("live_call", True)

                logger.info(f"Nhận yêu cầu: type={msg_type}, text='{user_text[:50]}', audio={bool(audio_b64)}, live_call={is_live_call}")

                session.add_user_message(
                    text=user_text,
                    image_b64=image_b64,
                    mime_type=mime_type,
                    audio_b64=audio_b64,
                    audio_mime=audio_mime
                )
                await safe_send_json(websocket, {"type": "status", "text": "Antigravity đang lắng nghe và suy nghĩ..."})

                # Spawn agent turn as independent asyncio Task to keep receive_text loop active
                current_turn_task = asyncio.create_task(process_user_turn(session, is_live_call))

    except WebSocketDisconnect:
        logger.info("iOS Client đã ngắt kết nối WebSocket (hoặc ẩn app).")
    except Exception as e:
        logger.error(f"WebSocket Exception: {e}", exc_info=True)
    finally:
        keepalive_active = False
        heartbeat_task.cancel()
        if current_turn_task and not current_turn_task.done():
            logger.info("Client tạm ngắt socket, AI trên PC vẫn tiếp tục chạy độc lập trong nền cho xong nhiệm vụ.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Antigravity Live Gateway Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host IP to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    args = parser.parse_args()

    print("=" * 60)
    print(f"[*] Antigravity Live Gateway dang khoi dong...")
    print(f"[*] Lang nghe tren: http://{args.host}:{args.port}")
    print(f"[*] WebSocket Live: ws://{args.host}:{args.port}/ws/live")
    print(f"[*] Health check:   http://{args.host}:{args.port}/health")
    print("=" * 60)

    uvicorn.run(app, host=args.host, port=args.port)
