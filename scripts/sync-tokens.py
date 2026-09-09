#!/usr/bin/env python3
"""
sync-tokens.py
Synchronizes OAuth tokens from Antigravity CLI (~/.gemini/antigravity-cli/antigravity-oauth-token)
directly into OpenCode credentials (~/.local/share/opencode/auth.json)
and Antigravity Accounts storage (~/.config/opencode/antigravity-accounts.json).
"""

import glob
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

def get_antigravity_oauth_client():
    """
    Dynamically loads OAuth Client ID and Secret from the installed
    opencode-antigravity-auth plugin constants.js to avoid storing secrets in git.
    """
    home = os.path.expanduser("~")
    search_dirs = [
        os.path.join(home, ".cache/opencode/packages"),
        os.path.join(home, ".opencode"),
        os.path.join(home, ".config/opencode"),
    ]
    for sdir in search_dirs:
        if not os.path.isdir(sdir):
            continue
        for path in glob.glob(os.path.join(sdir, "**/constants.js"), recursive=True):
            if "node_modules/opencode-antigravity-auth/dist/src/constants.js" in path:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        c = f.read()
                        cid = re.search(r'ANTIGRAVITY_CLIENT_ID\s*=\s*["\']([^"\']+)', c)
                        csec = re.search(r'ANTIGRAVITY_CLIENT_SECRET\s*=\s*["\']([^"\']+)', c)
                        if cid and csec:
                            return cid.group(1), csec.group(1)
                except Exception:
                    pass

    return (
        os.environ.get("ANTIGRAVITY_CLIENT_ID"),
        os.environ.get("ANTIGRAVITY_CLIENT_SECRET"),
    )

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

    client_id, client_secret = get_antigravity_oauth_client()
    now_ms = int(time.time() * 1000)
    expires_at = 0

    if client_id and client_secret:
        try:
            data_post = urllib.parse.urlencode({
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
            }).encode("utf-8")
            req_token = urllib.request.Request(
                "https://oauth2.googleapis.com/token",
                data=data_post,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            with urllib.request.urlopen(req_token, timeout=10) as resp:
                token_payload = json.loads(resp.read().decode("utf-8"))
                access_token = token_payload.get("access_token", access_token)
                expires_in = token_payload.get("expires_in", 3600)
                expires_at = now_ms + (expires_in * 1000)
                print("[+] Token OAuth berhasil di-refresh langsung ke Google.")
        except Exception as e:
            print(f"[*] Warning: Token refresh langsung gagal ({e}), mengatur expiry=0 untuk auto-refresh.", file=sys.stderr)
            expires_at = 0

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
