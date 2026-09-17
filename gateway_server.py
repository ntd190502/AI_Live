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

# Session State Registry for background execution & auto-sync across reconnects
class SessionTurnState:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.active_websocket: Optional[WebSocket] = None
        self.current_turn_task: Optional[asyncio.Task] = None
        self.is_thinking: bool = False
        self.current_status: str = "Sẵn sàng"
        self.accumulated_text: List[str] = []
        self.last_full_text: str = ""
        self.last_voice_b64: Optional[str] = None
        self.delivered: bool = True
        self.turn_id: int = 0

session_states: Dict[str, SessionTurnState] = {}

def get_session_state(session_id: str) -> SessionTurnState:
    if session_id not in session_states:
        session_states[session_id] = SessionTurnState(session_id)
    return session_states[session_id]

async def safe_send_json(ws: WebSocket, payload: dict) -> bool:
    try:
        await ws.send_json(payload)
        return True
    except Exception as ex:
        logger.warning(f"safe_send_json error ({type(ex).__name__}): {ex}")
        return False

async def send_session_event(session_id: str, payload: dict) -> bool:
    state = get_session_state(session_id)
    ws = state.active_websocket
    if ws is not None:
        success = await safe_send_json(ws, payload)
        if not success:
            state.active_websocket = None
        return success
    return False

async def replay_session_state_to_ws(websocket: WebSocket, session_id: str):
    """
    Called when a WebSocket connects or requests sync.
    If the session has an active background turn or an undelivered completed turn,
    replay it to the newly connected websocket.
    """
    state = get_session_state(session_id)
    state.active_websocket = websocket

    if state.is_thinking:
        logger.info(f"Session '{session_id}': AI đang suy luận ngầm -> Cập nhật trạng thái cho WebSocket mới.")
        await safe_send_json(websocket, {
            "type": "status",
            "text": state.current_status or "Antigravity đang tiếp tục suy nghĩ..."
        })
        if state.accumulated_text:
            await safe_send_json(websocket, {
                "type": "text_delta",
                "delta": "".join(state.accumulated_text)
            })
    elif not state.delivered and state.last_full_text:
        logger.info(f"Session '{session_id}': AI đã hoàn thành lượt chạy ngầm -> Đồng bộ thoại & audio về cho iPhone.")
        await safe_send_json(websocket, {
            "type": "status",
            "text": "Đã cập nhật phản hồi mới nhất từ PC."
        })
        await safe_send_json(websocket, {
            "type": "text_delta",
            "delta": state.last_full_text
        })
        if state.last_voice_b64:
            await safe_send_json(websocket, {
                "type": "voice_chunk",
                "audio_b64": state.last_voice_b64,
                "mime": "audio/mp3",
                "full_text": state.last_full_text
            })
        await safe_send_json(websocket, {
            "type": "turn_complete",
            "full_text": state.last_full_text
        })
        state.delivered = True

@app.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    """
    Real-time Duplex Live Voice & Chat WebSocket Endpoint.
    Supports auto-reconnection and persistent background AI reasoning.
    """
    await websocket.accept()
    client_session_id = websocket.query_params.get("session_id", "default_ios")
    logger.info(f"iOS Client đã kết nối vào WebSocket /ws/live (session_id={client_session_id})!")

    state = get_session_state(client_session_id)
    state.active_websocket = websocket

    # Immediately replay pending response or live thinking status to newly connected client
    await replay_session_state_to_ws(websocket, client_session_id)

    keepalive_active = True

    async def heartbeat_worker():
        while keepalive_active:
            try:
                await asyncio.sleep(3.0)
                if keepalive_active and state.active_websocket == websocket:
                    await safe_send_json(websocket, {"type": "ping"})
            except asyncio.CancelledError:
                break
            except Exception:
                break

    heartbeat_task = asyncio.create_task(heartbeat_worker())

    async def process_user_turn(session_id: str, is_live_call: bool):
        turn_state = get_session_state(session_id)
        session = get_or_create_session(session_id)
        turn_state.is_thinking = True
        turn_state.delivered = False
        turn_state.accumulated_text = []
        turn_state.turn_id += 1
        turn_start = time.time()

        try:
            async for event_type, data in run_agent_turn(
                session=session,
                model_name="gemini-3.8-flash-tiered",
                thinking_level="low",
                is_live_call=is_live_call
            ):
                if event_type == "status":
                    turn_state.current_status = str(data)
                    await send_session_event(session_id, {"type": "status", "text": str(data)})
                elif event_type == "text":
                    turn_state.accumulated_text.append(data)
                    await send_session_event(session_id, {"type": "text_delta", "delta": data})
                elif event_type == "tool_output":
                    logger.info(f"Tool executed: {data.get('tool')}")
                    await send_session_event(session_id, {
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
                            await send_session_event(session_id, {
                                "type": "screenshot",
                                "image_b64": img_b64,
                                "caption": caption
                            })
                        except Exception as fe:
                            logger.warning(f"Lỗi đọc file gửi: {fe}")
                elif event_type == "error":
                    logger.error(f"Agent error event: {data}")
                    turn_state.is_thinking = False
                    await send_session_event(session_id, {"type": "error", "message": str(data)})
                    return

            final_full_text = "".join(turn_state.accumulated_text).strip()
            turn_state.last_full_text = final_full_text
            turn_elapsed = time.time() - turn_start
            logger.info(f"AI hoàn thành câu trả lời ({len(final_full_text)} ký tự, {turn_elapsed:.2f}s): '{final_full_text[:60]}...'")

            # Synthesize Hoài My voice for Live Calls
            v_b64 = None
            if is_live_call and final_full_text:
                turn_state.current_status = "Đang phát giọng nói Hoài My..."
                await send_session_event(session_id, {"type": "status", "text": "Đang phát giọng nói Hoài My..."})
                try:
                    tts_start = time.time()
                    voice_path = await generate_vietnamese_voice(final_full_text)
                    if voice_path and voice_path.exists():
                        with open(voice_path, "rb") as vf:
                            v_b64 = base64.b64encode(vf.read()).decode("utf-8")
                        tts_elapsed = time.time() - tts_start
                        logger.info(f"Sinh voice TTS xong trong {tts_elapsed:.2f}s. Đang đẩy về iPhone...")
                        turn_state.last_voice_b64 = v_b64
                        sent_voice = await send_session_event(session_id, {
                            "type": "voice_chunk",
                            "audio_b64": v_b64,
                            "mime": "audio/mp3",
                            "full_text": final_full_text
                        })
                        if sent_voice:
                            turn_state.delivered = True
                except Exception as ve:
                    logger.error(f"Lỗi tạo voice TTS: {ve}")

            sent_complete = await send_session_event(session_id, {
                "type": "turn_complete",
                "full_text": final_full_text
            })
            if sent_complete:
                turn_state.delivered = True

        except asyncio.CancelledError:
            logger.info(f"Lượt xử lý AI session {session_id} bị ngắt bởi người dùng (Barge-in / Cancel).")
        except Exception as ex:
            logger.error(f"Lỗi trong quá trình xử lý agent turn: {ex}", exc_info=True)
            await send_session_event(session_id, {"type": "error", "message": f"Lỗi Agent: {str(ex)}"})
        finally:
            turn_state.is_thinking = False

    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                msg = json.loads(raw_data)
            except Exception:
                await websocket.send_json({"type": "error", "message": "Dữ liệu JSON không hợp lệ."})
                continue

            msg_type = msg.get("type", "")
            session_id = msg.get("session_id", client_session_id)
            session = get_or_create_session(session_id)
            sess_state = get_session_state(session_id)
            sess_state.active_websocket = websocket

            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "time": time.time()})
                continue

            elif msg_type == "sync":
                await replay_session_state_to_ws(websocket, session_id)
                continue

            elif msg_type in ("cancel", "interrupt"):
                if sess_state.current_turn_task and not sess_state.current_turn_task.done():
                    sess_state.current_turn_task.cancel()
                    sess_state.current_turn_task = None
                await safe_send_json(websocket, {"type": "status", "text": "Đã ngắt lời Antigravity."})
                await safe_send_json(websocket, {"type": "turn_complete", "full_text": ""})
                continue

            elif msg_type == "reset":
                if sess_state.current_turn_task and not sess_state.current_turn_task.done():
                    sess_state.current_turn_task.cancel()
                    sess_state.current_turn_task = None
                session.history.clear()
                session.title = "Phiên mới"
                sess_state.accumulated_text.clear()
                sess_state.last_full_text = ""
                sess_state.last_voice_b64 = None
                sess_state.delivered = True
                await websocket.send_json({"type": "status", "text": "Đã làm mới phiên trò chuyện."})
                continue

            elif msg_type in ("chat_text", "voice_audio"):
                if sess_state.current_turn_task and not sess_state.current_turn_task.done():
                    logger.info(f"Người dùng nói câu mới khi AI đang bận -> Hủy lượt cũ (Barge-in) session {session_id}.")
                    sess_state.current_turn_task.cancel()
                    sess_state.current_turn_task = None

                user_text = msg.get("text", "")
                audio_b64 = msg.get("audio_b64")
                audio_mime = msg.get("mime", "audio/wav")
                image_b64 = msg.get("image_b64")
                mime_type = msg.get("image_mime", "image/jpeg")
                is_live_call = (msg_type == "voice_audio") or msg.get("live_call", True)

                logger.info(f"Nhận yêu cầu: type={msg_type}, session={session_id}, text='{user_text[:50]}', audio={bool(audio_b64)}, live_call={is_live_call}")

                session.add_user_message(
                    text=user_text,
                    image_b64=image_b64,
                    mime_type=mime_type,
                    audio_b64=audio_b64,
                    audio_mime=audio_mime
                )
                await safe_send_json(websocket, {"type": "status", "text": "Antigravity đang lắng nghe và suy nghĩ..."})

                # Spawn agent turn as independent asyncio Task tied to session_id
                sess_state.current_turn_task = asyncio.create_task(process_user_turn(session_id, is_live_call))

    except WebSocketDisconnect:
        logger.info(f"iOS Client đã ngắt kết nối WebSocket (session_id={client_session_id}).")
    except Exception as e:
        logger.error(f"WebSocket Exception: {e}", exc_info=True)
    finally:
        keepalive_active = False
        heartbeat_task.cancel()
        if state.active_websocket == websocket:
            state.active_websocket = None
        if state.current_turn_task and not state.current_turn_task.done():
            logger.info(f"Session {client_session_id}: Client tạm ngắt socket, AI trên PC vẫn tiếp tục chạy độc lập trong nền.")

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
