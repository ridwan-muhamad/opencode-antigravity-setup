#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================================="
echo "   OpenCode + Antigravity (agy) Integration Setup Script  "
echo "========================================================="

# 1. Periksa apakah opencode terinstall
if ! command -v opencode &> /dev/null; then
    echo "[-] Error: 'opencode' tidak ditemukan di PATH."
    echo "    Silakan install OpenCode terlebih dahulu: https://opencode.ai"
    exit 1
fi
echo "[+] OpenCode terdeteksi: $(which opencode)"

# 2. Periksa apakah agy terinstall & sudah login
AGY_TOKEN="$HOME/.gemini/antigravity-cli/antigravity-oauth-token"
if [ ! -f "$AGY_TOKEN" ]; then
    echo "[-] Error: Token login Antigravity tidak ditemukan di: $AGY_TOKEN"
    echo "    Silakan jalankan 'agy' terlebih dahulu dan lakukan login Google."
    exit 1
fi
echo "[+] Token Antigravity (agy) terdeteksi!"

# 3. Install plugin opencode-antigravity-auth
echo "[*] Memasang plugin opencode-antigravity-auth..."
opencode plugin -g opencode-antigravity-auth@latest || true

# 4. Salin konfigurasi opencode.json
CONFIG_DIR="$HOME/.config/opencode"
mkdir -p "$CONFIG_DIR"
if [ -f "$CONFIG_DIR/opencode.json" ]; then
    cp "$CONFIG_DIR/opencode.json" "$CONFIG_DIR/opencode.json.bak.$(date +%s)"
    echo "[*] Backup konfigurasi lama dibuat di $CONFIG_DIR/opencode.json.bak"
fi
cp "$SCRIPT_DIR/config/opencode.json" "$CONFIG_DIR/opencode.json"
echo "[+] Konfigurasi berhasil disalin ke: $CONFIG_DIR/opencode.json"

# 5. Sinkronisasi token
echo "[*] Menyinkronkan kredensial dari agy ke OpenCode..."
python3 "$SCRIPT_DIR/scripts/sync-tokens.py"

# 6. Terapkan compatibility patch (Gemini 3.1 Pro & Gemini 3.8 Flash)
echo "[*] Menerapkan patch kompatibilitas model..."
python3 "$SCRIPT_DIR/scripts/patch-model-resolver.py"

echo ""
echo "========================================================="
echo "[V] SELESAI! Setup integrasi OpenCode & Antigravity sukses."
echo "========================================================="
echo "Contoh penggunaan:"
echo "  opencode                                              # Jalankan TUI"
echo "  opencode run 'Halo dunia'                              # Default: Gemini 3.1 Pro"
echo "  opencode run --model=google/antigravity-gemini-3.8-flash 'Halo' # Gemini 3.8 Flash"
echo "  opencode run --model=google/antigravity-claude-sonnet-4-6 'Halo' # Claude Sonnet 4.6"
echo "========================================================="
