# -*- coding: utf-8 -*-
import os
import json
import time
import secrets
import hashlib
import base64
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
import httpx

BASE_DIR = Path(__file__).resolve().parent
AUTH_FILE = BASE_DIR / "auth_token.json"

SECRET_FILE = BASE_DIR / "google_client_secret.json"

_client_id = ""
_client_secret = ""
if SECRET_FILE.exists():
    try:
        with open(SECRET_FILE, "r", encoding="utf-8") as f:
            _sec_data = json.load(f)
            _client_id = _sec_data.get("client_id", "")
            _client_secret = _sec_data.get("client_secret", "")
    except Exception:
        pass

CLIENT_ID = os.getenv("ANTIGRAVITY_CLIENT_ID", _client_id)
CLIENT_SECRET = os.getenv("ANTIGRAVITY_CLIENT_SECRET", _client_secret)

REDIRECT_URI = "http://127.0.0.1:8085/callback"

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/cclog",
    "https://www.googleapis.com/auth/experimentsandconfigs",
]

_pending_oauth: Dict[str, Any] = {}

def generate_pkce() -> Tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return verifier, challenge

def create_auth_url() -> Tuple[str, str]:
    verifier, challenge = generate_pkce()
    state = secrets.token_urlsafe(16)
    
    _pending_oauth["verifier"] = verifier
    _pending_oauth["state"] = state
    _pending_oauth["created_at"] = time.time()
    
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return url, state

def extract_code(input_str: str) -> Optional[str]:
    s = input_str.strip()
    if "code=" in s:
        try:
            parsed = urllib.parse.urlparse(s)
            qs = urllib.parse.parse_qs(parsed.query)
            if "code" in qs:
                return qs["code"][0]
        except Exception:
            pass
        import re
        m = re.search(r"code=([^&\s]+)", s)
        if m:
            return urllib.parse.unquote(m.group(1))
    return s if len(s) > 15 and not s.startswith("http") else None

async def exchange_code(raw_input: str) -> Dict[str, Any]:
    code = extract_code(raw_input)
    if not code:
        raise ValueError("Không tìm thấy authorization code hợp lệ trong tin nhắn.")
    
    verifier = _pending_oauth.get("verifier")
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    if verifier:
        data["code_verifier"] = verifier
        
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            TOKEN_URL,
            data=data,
            headers={"User-Agent": "antigravity/1.19.2 linux/x64"}
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Lỗi trao đổi mã OAuth ({resp.status_code}): {resp.text}")
        
        token_data = resp.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)
        
        user_email = ""
        user_name = ""
        try:
            u_resp = await client.get(
                USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if u_resp.status_code == 200:
                u_info = u_resp.json()
                user_email = u_info.get("email", "")
                user_name = u_info.get("name", "")
        except Exception:
            pass
        
        project_id = await resolve_project_id(access_token)
        
        saved = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expiry": time.time() + expires_in,
            "user_email": user_email,
            "user_name": user_name,
            "project_id": project_id,
            "updated_at": time.time()
        }
        with open(AUTH_FILE, "w", encoding="utf-8") as f:
            json.dump(saved, f, indent=2, ensure_ascii=False)
            
        _pending_oauth.clear()
        return saved

async def resolve_project_id(access_token: str) -> str:
    url = "https://cloudcode-pa.googleapis.com/v1internal:loadCodeAssist"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "antigravity/1.19.2 linux/x64",
        "X-Goog-Api-Client": "antigravity/1.19.2 gl-node/20.0.0",
    }
    body = {
        "metadata": {
            "ideType": "ANTIGRAVITY",
            "platform": "PLATFORM_UNSPECIFIED",
            "pluginType": "GEMINI"
        }
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            r = await client.post(url, headers=headers, json=body)
            if r.status_code == 200:
                data = r.json()
                pid = (
                    data.get("cloudaicompanionProject") or
                    data.get("cloudaicompanionProjectId") or
                    data.get("projectId")
                )
                if pid:
                    return pid
            onboard_url = "https://cloudcode-pa.googleapis.com/v1internal:onboardUser"
            ob_body = {
                "tierId": "FREE",
                "metadata": {
                    "ideType": "ANTIGRAVITY",
                    "platform": "PLATFORM_UNSPECIFIED",
                    "pluginType": "GEMINI"
                }
            }
            ob_r = await client.post(onboard_url, headers=headers, json=ob_body)
            if ob_r.status_code == 200:
                ob_data = ob_r.json()
                pid = ob_data.get("cloudaicompanionProject") or ob_data.get("projectId")
                if pid:
                    return pid
        except Exception:
            pass
    return "outside-of-project"

async def get_valid_token() -> Tuple[str, str, str]:
    if not AUTH_FILE.exists():
        raise RuntimeError("Chưa đăng nhập tài khoản Antigravity. Dùng lệnh /login để đăng nhập.")
    
    with open(AUTH_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    access_token = data.get("access_token", "")
    refresh_token = data.get("refresh_token", "")
    expiry = data.get("expiry", 0)
    project_id = data.get("project_id", "outside-of-project")
    user_email = data.get("user_email", "")
    
    if time.time() > (expiry - 300) and refresh_token:
        async with httpx.AsyncClient(timeout=20.0) as client:
            ref_data = {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            }
            resp = await client.post(
                TOKEN_URL,
                data=ref_data,
                headers={"User-Agent": "antigravity/1.19.2 linux/x64"}
            )
            if resp.status_code == 200:
                ref_res = resp.json()
                access_token = ref_res.get("access_token", access_token)
                expires_in = ref_res.get("expires_in", 3600)
                data["access_token"] = access_token
                data["expiry"] = time.time() + expires_in
                data["updated_at"] = time.time()
                with open(AUTH_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
    return access_token, project_id, user_email

def is_logged_in() -> bool:
    if not AUTH_FILE.exists():
        return False
    try:
        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return bool(data.get("access_token") and data.get("refresh_token"))
    except Exception:
        return False

def get_auth_info() -> Dict[str, Any]:
    if not AUTH_FILE.exists():
        return {"logged_in": False}
    try:
        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "logged_in": True,
                "email": data.get("user_email", "Ẩn"),
                "name": data.get("user_name", ""),
                "project_id": data.get("project_id", "outside-of-project"),
                "expiry": data.get("expiry", 0),
            }
    except Exception:
        return {"logged_in": False}

def logout() -> bool:
    if AUTH_FILE.exists():
        try:
            os.remove(AUTH_FILE)
            return True
        except Exception:
            return False
    return True

async def get_user_quota_summary() -> Dict[str, Any]:
    """Retrieves weekly and rolling hourly quotas from Google Cloud Code Assist."""
    access_token, project_id, user_email = await get_valid_token()
    
    endpoints = [
        "https://cloudcode-pa.googleapis.com/v1internal:retrieveUserQuotaSummary",
        "https://daily-cloudcode-pa.googleapis.com/v1internal:retrieveUserQuotaSummary",
    ]
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "antigravity/1.19.2 linux/x64",
        "X-Goog-Api-Client": "antigravity/1.19.2 gl-node/20.0.0",
    }
    body = {"project": project_id}
    
    last_err = None
    data = None
    for ep in endpoints:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(ep, headers=headers, json=body)
                if r.status_code == 200:
                    data = r.json()
                    break
                else:
                    last_err = f"{r.status_code}: {r.text[:200]}"
        except Exception as e:
            last_err = str(e)
            
    if not data:
        raise RuntimeError(f"Không thể lấy hạn mức ({last_err})")
        
    return {
        "email": user_email,
        "project_id": project_id,
        "raw": data
    }
