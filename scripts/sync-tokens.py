#!/usr/bin/env python3
"""
sync-tokens.py
Synchronizes OAuth tokens from Antigravity CLI (~/.gemini/antigravity-cli/antigravity-oauth-token)
directly into OpenCode credentials (~/.local/share/opencode/auth.json)
and Antigravity Accounts storage (~/.config/opencode/antigravity-accounts.json).
"""

import json
import os
import sys
import time
import urllib.request

def main():
    token_path = os.path.expanduser("~/.gemini/antigravity-cli/antigravity-oauth-token")
    if not os.path.exists(token_path):
        print(f"[-] File token agy tidak ditemukan di: {token_path}", file=sys.stderr)
        print("    Pastikan Anda sudah login ke Antigravity CLI dengan menjalankan: agy", file=sys.stderr)
        sys.exit(1)

    try:
        with open(token_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[-] Gagal membaca file token agy: {e}", file=sys.stderr)
        sys.exit(1)

    token_info = data.get("token", {})
    refresh_token = token_info.get("refresh_token")
    access_token = token_info.get("access_token")

    if not refresh_token:
        print("[-] Refresh token tidak ditemukan di token agy.", file=sys.stderr)
        sys.exit(1)

    # Dapatkan email akun dari tokeninfo Google
    email = "antigravity-user@gmail.com"
    if access_token:
        try:
            req = urllib.request.Request(
                f"https://oauth2.googleapis.com/tokeninfo?access_token={access_token}"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                info = json.loads(resp.read().decode("utf-8"))
                email = info.get("email", email)
        except Exception:
            pass

    project_id = "rising-fact-p41fc"
    now_ms = int(time.time() * 1000)
    expires_at = now_ms + (3600 * 1000)

    # 1. Update ~/.local/share/opencode/auth.json
    auth_dir = os.path.expanduser("~/.local/share/opencode")
    os.makedirs(auth_dir, exist_ok=True)
    auth_file = os.path.join(auth_dir, "auth.json")

    auth_data = {}
    if os.path.exists(auth_file):
        try:
            with open(auth_file, "r", encoding="utf-8") as f:
                auth_data = json.load(f)
        except Exception:
            auth_data = {}

    auth_data["google"] = {
        "type": "oauth",
        "refresh": f"{refresh_token}|{project_id}",
        "access": access_token or "",
        "expires": expires_at,
    }

    with open(auth_file, "w", encoding="utf-8") as f:
        json.dump(auth_data, f, indent=2)
    print(f"[+] Berhasil mengupdate OpenCode auth: {auth_file}")

    # 2. Update ~/.config/opencode/antigravity-accounts.json
    config_dir = os.path.expanduser("~/.config/opencode")
    os.makedirs(config_dir, exist_ok=True)
    accounts_file = os.path.join(config_dir, "antigravity-accounts.json")

    accounts_data = {
        "version": 4,
        "accounts": [
            {
                "email": email,
                "refreshToken": f"{refresh_token}|{project_id}",
                "projectId": project_id,
                "addedAt": now_ms,
                "lastUsed": now_ms,
                "enabled": True,
            }
        ],
        "activeIndex": 0,
        "activeIndexByFamily": {
            "claude": 0,
            "gemini": 0,
        },
    }

    with open(accounts_file, "w", encoding="utf-8") as f:
        json.dump(accounts_data, f, indent=2)
    print(f"[+] Berhasil mengupdate Antigravity accounts: {accounts_file}")
    print(f"[+] Kredensial akun ({email}) berhasil disinkronkan ke OpenCode!")

if __name__ == "__main__":
    main()
