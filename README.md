# Personal Input Tracker & Logger

A transparent, permission-based desktop assistant that records keyboard and mouse activity, stores it locally in JSON, and forwards batches to a configurable webhook/server for dashboards and auditing.

> ⚠️ **Etika & Privasi** — Gunakan aplikasi ini hanya pada perangkat dan akun milik sendiri atau dengan izin tertulis dari pemiliknya. Jangan gunakan untuk memata-matai, mencuri data, atau tindakan melawan hukum. Aplikasi tidak berjalan secara stealth; GUI selalu terlihat dan terdapat peringatan etika saat awal dijalankan.

## Fitur Utama

- Perekaman real-time keyboard & mouse via `pynput` (karakter, tombol khusus, klik, scroll)
- Metadata lengkap: timestamp UTC, judul jendela aktif, posisi kursor, delta scroll
- Filter jendela sensitif berdasar kata kunci (default: password/login/auth/credential)
- Logging modular: JSONL lokal + pengiriman batch ke webhook HTTP
- Antrian dan retry otomatis; penyimpanan sementara saat server tidak tersedia
- GUI modern berbasis `tkinter` + opsi tray (pystray) dengan kontrol Mulai/Jeda, statistik kirim, serta tombol buka folder log
- Mode debug untuk melihat event di terminal
- Opsi screenshot berkala (mss/pyautogui) yang turut dikirim ke server
- Konfigurasi tersentral di `config.json`
- Server FastAPI sederhana + dashboard HTML + SQLite storage + Basic Auth opsional
- Instruksi packaging PyInstaller untuk distribusi Windows/macOS/Linux

## Kebutuhan Sistem

- Python 3.10+
- Dependencies di `requirements.txt`
- Desktop environment (pynput & pyautogui membutuhkan akses GUI, bukan headless)

## Instalasi

```fish
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Konfigurasi

Pada run pertama, `config.json` otomatis dibuat dari default `config.DEFAULT_CONFIG`. Contoh isi:

```json
{
  "webhook_url": "http://127.0.0.1:8000/api/input",
  "send_interval_seconds": 5,
  "batch_size": 25,
  "log_dir": "logs",
  "enable_screenshots": false,
  "screenshot_interval_seconds": 120,
  "debug_mode": false,
  "tray_enabled": true,
  "pending_cache_file": "pending_events.jsonl",
  "screenshot_format": "png",
  "sensitive_title_keywords": ["password", "login", "auth", "credential"],
  "ethics_acknowledged": false
}
```

Ubah sesuai kebutuhan. Pastikan folder `log_dir` dapat ditulis.

## Menjalankan Aplikasi Desktop

```fish
source .venv/bin/activate
python main.py
```

Kontrol utama:

- **Mulai/Jeda**: memulai atau menghentikan perekaman & pengiriman
- **Buka Log**: membuka folder log lokal
- **Keluar**: menutup aplikasi (dan menghentikan listener)

### Mode Debug

Aktifkan `"debug_mode": true` di `config.json` untuk mencetak event ke terminal.

### Screenshot Opsional

Set `"enable_screenshots": true` untuk memicu capture berkala. Pastikan minimal salah satu backend tersedia:

- [`mss`](https://github.com/BoboTiG/python-mss) (default, multi-platform)
- [`pyautogui`](https://pyautogui.readthedocs.io/)

## Server FastAPI

Server menerima webhook, menyimpan ke SQLite, dan menyediakan dashboard HTML sederhana.

```fish
source .venv/bin/activate
uvicorn server:APP --reload --host 0.0.0.0 --port 8000
```

### Lingkungan Opsional

- `TRACKER_DASH_USER` & `TRACKER_DASH_PASS`: mengaktifkan Basic Auth di dashboard (`/`)
- `DB_PATH`: ubah lokasi SQLite (default `tracker.db`)

### Endpoint

- `POST /api/input` — terima payload `{ "events": [...] }`
- `GET /api/events?limit=50` — JSON event terbaru
- `GET /` — dashboard HTML (auto-refresh)

## Packaging ke Executable

1. Pastikan virtual environment sudah terpasang dependency GUI (tkinter sudah termasuk di Python standar).
2. Jalankan PyInstaller (contoh Windows, ganti `--onefile`/`--windowed` sesuai kebutuhan):

```fish
source .venv/bin/activate
pyinstaller --onefile --windowed --name InputTracker main.py
```

3. Sertakan `config.json`, `requirements.txt`, dan README ketika mendistribusikan.
4. Untuk macOS `.app` atau Linux AppImage, gunakan opsi PyInstaller yang relevan (`--target-architecture`, dll).

## Struktur Proyek

```
main.py               # Entry point
config.py             # Loader/saver konfigurasi
logger.py             # Listener keyboard & mouse
sender.py             # Pengiriman HTTP + retry/pending cache
screenshot.py         # Opsional capture screenshot
storage.py            # JSONL logger lokal
utils.py              # Helper timestamp, window title, chunker
gui.py                # Antarmuka tkinter + tray
server.py             # FastAPI receiver + dashboard
templates/            # Dashboard HTML
```

## Logging & Troubleshooting

- Log aplikasi disalurkan ke stdout; aktifkan `debug_mode` untuk detail event
- File event lokal: `<log_dir>/events.jsonl`
- Pending queue: `<log_dir>/pending_events.jsonl`
- Gunakan `python -m compileall .` untuk deteksi error sintaks cepat

## Pengembangan Lanjutan

- Tambahkan autentikasi token pada webhook
- Integrasi storage lain (PostgreSQL, cloud queue)
- Ekstensi plugin (misalnya analitik kelas aktivitas)

## Lisensi

Proyek ini ditujukan untuk pembelajaran/monitoring pribadi. Pastikan mematuhi hukum dan regulasi privasi setempat.
