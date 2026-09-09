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

# 4. Salin konfigurasi opencode.json & antigravity.json
CONFIG_DIR="$HOME/.config/opencode"
mkdir -p "$CONFIG_DIR"
if [ -f "$CONFIG_DIR/opencode.json" ]; then
    cp "$CONFIG_DIR/opencode.json" "$CONFIG_DIR/opencode.json.bak.$(date +%s)"
    echo "[*] Backup konfigurasi lama dibuat di $CONFIG_DIR/opencode.json.bak"
fi
if [ -f "$CONFIG_DIR/opencode.jsonc" ]; then
    cp "$CONFIG_DIR/opencode.jsonc" "$CONFIG_DIR/opencode.jsonc.bak.$(date +%s)"
    mv "$CONFIG_DIR/opencode.jsonc" "$CONFIG_DIR/opencode.jsonc.disabled"
    echo "[*] Ditemukan opencode.jsonc lama; berhasil dibackup & dinonaktifkan agar tidak konflik."
fi
cp "$SCRIPT_DIR/config/opencode.json" "$CONFIG_DIR/opencode.json"
echo "[+] Konfigurasi model berhasil disalin ke: $CONFIG_DIR/opencode.json"

if [ -f "$SCRIPT_DIR/config/antigravity.json" ]; then
    cp "$SCRIPT_DIR/config/antigravity.json" "$CONFIG_DIR/antigravity.json"
    echo "[+] Konfigurasi tuning stabilitas berhasil disalin ke: $CONFIG_DIR/antigravity.json"
fi

# 5. Sinkronisasi token
echo "[*] Menyinkronkan kredensial dari agy ke OpenCode..."
python3 "$SCRIPT_DIR/scripts/sync-tokens.py"

# 6. Terapkan compatibility & stability patch
echo "[*] Menerapkan patch kompatibilitas model & stabilitas endpoint..."
python3 "$SCRIPT_DIR/scripts/patch-model-resolver.py"

echo ""
echo "========================================================="
echo "[V] SELESAI! Setup integrasi OpenCode & Antigravity sukses."
echo "========================================================="
echo "Contoh penggunaan:"
echo "  opencode                                              # Jalankan TUI"
echo "  opencode run 'Halo dunia'                              # Default model"
echo "  opencode run -m google/antigravity-gemini-3.8-flash 'Halo' # Gemini 3.8 Flash (Responsif & Cepat)"
echo "  opencode run -m google/antigravity-gemini-3.1-pro 'Analisa kode...' # Gemini 3.1 Pro (Deep Reasoning)"
echo "  opencode run -m google/antigravity-claude-sonnet-4-6 'Halo' # Claude Sonnet 4.6"
echo "========================================================="
