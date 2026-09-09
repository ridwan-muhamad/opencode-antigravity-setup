# OpenCode + Google Antigravity (agy) Integration Guide & Bridge

Repositori ini berisi panduan lengkap, script otomatisasi, dan konfigurasi agar **[OpenCode](https://opencode.ai)** dapat menggunakan model-model AI dari **Google Antigravity (`agy`)** menggunakan akun dan token OAuth yang sudah terotentikasi di `agy`.

---

## 📑 Daftar Isi
1. [Fitur & Keunggulan](#-fitur--keunggulan)
2. [Model yang Didukung](#-model-yang-didukung)
3. [Latar Belakang & Analisis Masalah](#-latar-belakang--analisis-masalah)
4. [Persyaratan Sistem](#-persyaratan-sistem)
5. [Panduan Cepat (One-Click Setup)](#-panduan-cepat-one-click-setup)
6. [Panduan Manual (Langkah demi Langkah)](#-panduan-manual-langkah-demi-langkah)
   - [Langkah 1: Instalasi Plugin](#langkah-1-instalasi-plugin)
   - [Langkah 2: Konfigurasi opencode.json](#langkah-2-konfigurasi-opencodejson)
   - [Langkah 3: Sinkronisasi Token dari agy](#langkah-3-sinkronisasi-token-dari-agy)
   - [Langkah 4: Penerapan Patch Kompatibilitas Model](#langkah-4-penerapan-patch-kompatibilitas-model)
7. [Cara Penggunaan](#-cara-penggunaan)
8. [Pemeliharaan & Troubleshooting](#-pemeliharaan--troubleshooting)
9. [Struktur Repositori](#-struktur-repositori)
10. [Lisensi & Disclaimer](#-lisensi--disclaimer)

---

## 🚀 Fitur & Keunggulan
- **Tanpa Login Ulang di Browser**: Kredensial OAuth diambil langsung dari session aktif Antigravity CLI (`agy`) di komputer Anda (`~/.gemini/antigravity-cli/antigravity-oauth-token`).
- **Mendukung Model Unggulan**:
  - `google/antigravity-gemini-3.1-pro` (Reasoning / Thinking)
  - `google/antigravity-gemini-3.8-flash` (Fast Thinking)
  - `google/antigravity-gemini-3-flash`
  - `google/antigravity-claude-sonnet-4-6`
  - `google/antigravity-claude-opus-4-6-thinking`
- **Auto-Redirect Depresiasi Model**: Menangani perubahan backend Google secara otomatis (misal: pengalihan otomatis `gemini-3-pro` yang telah didepresiasi menjadi `gemini-3.1-pro`).
- **Skrip Sinkronisasi Satu Perintah**: Memudahkan pembaharuan kredensial kapan saja.

---

## 🤖 Model yang Didukung

| Model ID di OpenCode | Nama Tampilan | Varian / Thinking Level | Keterangan |
| :--- | :--- | :--- | :--- |
| `google/antigravity-gemini-3.1-pro` | Gemini 3.1 Pro (Antigravity) | `low`, `high` | Model default, penalaran logika mendalam |
| `google/antigravity-gemini-3.8-flash` | Gemini 3.8 Flash (Antigravity) | `minimal`, `low`, `medium`, `high` | Sangat cepat dengan reasoning fleksibel |
| `google/antigravity-gemini-3-flash` | Gemini 3 Flash (Antigravity) | `minimal`, `low`, `medium`, `high` | Model flash standar Antigravity |
| `google/antigravity-claude-sonnet-4-6` | Claude Sonnet 4.6 (Antigravity) | *-* | Model coding canggih Anthropic |
| `google/antigravity-claude-opus-4-6-thinking` | Claude Opus 4.6 Thinking | `low`, `max` | Extended thinking Claude |

---

## 🔍 Latar Belakang & Analisis Masalah

Sebelum integrasi ini dibuat, terdapat beberapa kendala ketika mencoba menghubungkan OpenCode dengan Antigravity:

1. **Format Penyimpanan Kredensial Berbeda**:
   - `agy` menyimpan token OAuth di: `~/.gemini/antigravity-cli/antigravity-oauth-token`
   - OpenCode menyimpan kredensial di: `~/.local/share/opencode/auth.json`
   - Plugin `opencode-antigravity-auth` membaca akun dari: `~/.config/opencode/antigravity-accounts.json`
   *Solusi*: Dibuat script `sync-tokens.py` untuk mengalirkan data token `agy` secara otomatis ke format OpenCode.

2. **Depresiasi Backend Google (`gemini-3-pro`)**:
   - Google telah menghentikan `gemini-3-pro` di backend Antigravity dengan pesan error: *"Gemini 3 Pro is no longer available. Please switch to Gemini 3.1 Pro"*.
   - Plugin default masih mencoba meminta `gemini-3-pro`, menyebabkan infinite loop error saat dijalankan.
   *Solusi*: Dilakukan patch pada `model-resolver.js` untuk mengarahkan permintaan `gemini-3-pro` ke `gemini-3.1-pro`.

3. **Penamaan `Gemini 3.8 Flash`**:
   - Di `agy`, slot Flash terbaru dinamai *Gemini 3.8 Flash*, sementara model backend dasarnya adalah `gemini-3-flash` dengan parameter thinking.
   *Solusi*: Model `antigravity-gemini-3.8-flash` didaftarkan ke `opencode.json` dan dipetakan di resolver.

4. **Endpoint Fallback Poisoning & Quota Exhaustion Lock (Penyebab 'No Response' / Hang)**:
   - Plugin bawaan menyertakan 3 endpoint fallback: `daily` sandbox, `autopush` sandbox, dan `prod` (`cloudcode-pa.googleapis.com`).
   - Token Antigravity milik akun pengguna hanya memiliki otorisasi kuota pada endpoint Sandbox Daily. Endpoint `autopush` mengembalikan `403 Forbidden` dan endpoint `prod` mengembalikan `429 Quota Exhausted`.
   - Ketika plugin mengalami retry atau jeda, ia mencoba fallback ke `prod` yang memicu status `QUOTA_EXHAUSTED` palsu. Akibatnya akun terkunci (*backoff cooldown*) hingga 300 detik (5 menit), membuat OpenCode seolah-olah "no response" atau hanging lama.
   *Solusi*: `patch-model-resolver.py` membatasi fallback HANYA ke Sandbox Daily (`https://daily-cloudcode-pa.sandbox.googleapis.com`), memprioritaskan endpoint daily untuk project discovery, dan menyediakan `antigravity.json` dengan fail-fast timeouts (15 detik) serta disk debug logging.


---

## 📦 Persyaratan Sistem

- **Linux / WSL (Ubuntu/Debian/Arch/dll)** atau **macOS**
- **Python 3.8+** (bawaan sistem)
- **OpenCode** sudah terpasang (`which opencode`)
- **Antigravity CLI (`agy`)** sudah terpasang dan dalam status login (`which agy`)

---

## ⚡ Panduan Cepat (One-Click Setup)

1. Clone repositori ini atau download foldernya:
   ```bash
   git clone https://github.com/<username>/opencode-antigravity-setup.git
   cd opencode-antigravity-setup
   ```

2. Jalankan skrip setup otomatis:
   ```bash
   ./setup.sh
   ```

3. Selesai! Anda bisa langsung menjalankan OpenCode:
   ```bash
   opencode run "Halo, siapakah kamu?"
   ```

---

## 🛠 Panduan Manual (Langkah demi Langkah)

Jika Anda ingin melakukan setup secara manual langkah demi langkah:

### Langkah 1: Instalasi Plugin
Jalankan perintah berikut di terminal:
```bash
opencode plugin -g opencode-antigravity-auth@latest
```

### Langkah 2: Konfigurasi opencode.json
Buat atau perbarui file `~/.config/opencode/opencode.json`:
```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "google/antigravity-gemini-3.1-pro",
  "plugin": [
    "opencode-antigravity-auth@latest"
  ],
  "provider": {
    "google": {
      "models": {
        "antigravity-gemini-3.1-pro": {
          "name": "Gemini 3.1 Pro (Antigravity)",
          "limit": { "context": 1048576, "output": 65535 },
          "modalities": { "input": ["text", "image", "pdf"], "output": ["text"] },
          "variants": {
            "low": { "thinkingLevel": "low" },
            "high": { "thinkingLevel": "high" }
          }
        },
        "antigravity-gemini-3.8-flash": {
          "name": "Gemini 3.8 Flash (Antigravity)",
          "limit": { "context": 1048576, "output": 65536 },
          "modalities": { "input": ["text", "image", "pdf"], "output": ["text"] },
          "variants": {
            "minimal": { "thinkingLevel": "minimal" },
            "low": { "thinkingLevel": "low" },
            "medium": { "thinkingLevel": "medium" },
            "high": { "thinkingLevel": "high" }
          }
        },
        "antigravity-gemini-3-flash": {
          "name": "Gemini 3 Flash (Antigravity)",
          "limit": { "context": 1048576, "output": 65536 },
          "modalities": { "input": ["text", "image", "pdf"], "output": ["text"] },
          "variants": {
            "minimal": { "thinkingLevel": "minimal" },
            "low": { "thinkingLevel": "low" },
            "medium": { "thinkingLevel": "medium" },
            "high": { "thinkingLevel": "high" }
          }
        },
        "antigravity-claude-sonnet-4-6": {
          "name": "Claude Sonnet 4.6 (Antigravity)",
          "limit": { "context": 200000, "output": 64000 },
          "modalities": { "input": ["text", "image", "pdf"], "output": ["text"] }
        },
        "antigravity-claude-opus-4-6-thinking": {
          "name": "Claude Opus 4.6 Thinking (Antigravity)",
          "limit": { "context": 200000, "output": 64000 },
          "modalities": { "input": ["text", "image", "pdf"], "output": ["text"] },
          "variants": {
            "low": { "thinkingConfig": { "thinkingBudget": 8192 } },
            "max": { "thinkingConfig": { "thinkingBudget": 32768 } }
          }
        }
      }
    }
  }
}
```

### Langkah 3: Sinkronisasi Token dari agy
Jalankan script Python:
```bash
python3 scripts/sync-tokens.py
```
Skrip ini akan:
- Membaca `~/.gemini/antigravity-cli/antigravity-oauth-token`.
- Mengisi `~/.local/share/opencode/auth.json` dengan kredensial Google OAuth yang valid.
- Mengisi `~/.config/opencode/antigravity-accounts.json` dengan account metadata.

### Langkah 4: Penerapan Patch Kompatibilitas Model
Jalankan script patch:
```bash
python3 scripts/patch-model-resolver.py
```
Skrip ini memodifikasi file `model-resolver.js` di dalam cache plugin agar permintaan model `gemini-3-pro` dialihkan ke `gemini-3.1-pro` dan `gemini-3.8-flash` dipetakan ke engine flash backend.

---

## 💻 Cara Penggunaan

### 1. Menjalankan TUI Interaktif OpenCode
```bash
opencode
```
Di dalam TUI, Anda dapat mengetikkan perintah `/models` untuk beralih antar model Antigravity kapan saja.

### 2. Menjalankan Single Prompt di Terminal
```bash
# Menggunakan default model (Gemini 3.1 Pro)
opencode run "Jelaskan konsep Dependency Injection dalam 2 kalimat."

# Menggunakan Gemini 3.8 Flash
opencode run --model=google/antigravity-gemini-3.8-flash "Buat regex untuk validasi email"

# Menggunakan Gemini 3.8 Flash dengan Thinking Level High (Reasoning Mendalam)
opencode run --model=google/antigravity-gemini-3.8-flash --variant=high "Optimasi fungsi recursive Fibonacci"

# Menggunakan Claude Sonnet 4.6
opencode run --model=google/antigravity-claude-sonnet-4-6 "Tuliskan boilerplate REST API Go"

# Menggunakan Claude Opus 4.6 Thinking
opencode run --model=google/antigravity-claude-opus-4-6-thinking "Analisis arsitektur sistem microservice berikut"
```

---

## 🔧 Pemeliharaan & Troubleshooting

### Token Kedaluwarsa / Perlu Refresh
Jika token OAuth kedaluwarsa atau Anda baru saja melakukan re-login di Antigravity CLI (`agy`), cukup jalankan kembali:
```bash
python3 scripts/sync-tokens.py
```
*(Atau jika sudah menambahkan `sync-agy-opencode` ke `$PATH`, cukup ketik `sync-agy-opencode` di terminal mana saja).*

### Memeriksa Kredensial di OpenCode
Cek apakah kredensial Google terdeteksi di OpenCode:
```bash
opencode providers list
```
Output yang benar akan menampilkan:
```
┌ Credentials ~/.local/share/opencode/auth.json
│
● Google oauth
│
└ 1 credentials
```

### Memeriksa Daftar Model yang Terdaftar
```bash
opencode models google
```

---

## 📁 Struktur Repositori

```text
opencode-antigravity-setup/
├── README.md                     # Dokumentasi & panduan lengkap ini
├── setup.sh                      # Skrip instalasi & konfigurasi otomatis satu perintah
├── LICENSE                       # Lisensi MIT
├── .gitignore                    # Mengabaikan file token & log sensitif
├── config/
│   ├── opencode.json             # Model profile definitions untuk ~/.config/opencode/opencode.json
│   └── antigravity.json          # Tuning stabilitas & timeout untuk ~/.config/opencode/antigravity.json
└── scripts/
    ├── sync-tokens.py            # Skrip sinkronisasi & refresh token OAuth agy -> OpenCode
    └── patch-model-resolver.py   # Skrip patch model resolver & stabilitas endpoint plugin
```

---

## 📄 Lisensi & Disclaimer

Proyek ini dirilis di bawah lisensi [MIT](LICENSE).

**Disclaimer:**
- Ini adalah proyek utilitas independen dan tidak berafiliasi secara resmi dengan Google atau OpenCode.
- Antigravity, Gemini, dan Google adalah merek dagang dari Google LLC.
