# claude-sync

A CLI tool to synchronize Claude Code sessions across devices using Git.

> **Status:** Tahap 6 selesai. `init`, `status`, `inspect`, `export`,
> `import` (dengan auto-backup), `push` (export → commit → push), dan
> `pull` (fetch → pull → import) sudah diimplementasikan dan teruji.
> Lihat [Autentikasi Git](#autentikasi-git-token-based) untuk setup token.

## Tujuan

`claude-sync` memungkinkan Anda menyinkronkan session Claude Code antar device dengan menggunakan Git sebagai media sinkronisasi. Project ini dibangun secara bertahap (tahap per tahap) untuk menjaga kestabilan setiap fitur.

## Requirements

- Python 3.12 atau lebih baru
- `pip` atau `uv` untuk instalasi

## Instalasi

Clone repository ini lalu install dalam mode editable:

```bash
cd claude-sync
python -m venv .venv
source .venv/bin/activate  # Linux/WSL
# .venv\Scripts\activate   # Windows PowerShell
pip install -e .
```

Atau jika menggunakan `uv`:

```bash
uv pip install -e .
```

## Cara Menjalankan

Setelah terinstal, command `claude-sync` akan tersedia di terminal:

```bash
claude-sync --help
```

Perintah yang tersedia di Tahap 6:

### `claude-sync init`

Membuat folder `.claude-sync` di current directory dan file `manifest.json` di dalamnya.

```bash
cd my-project
claude-sync init
```

Output:
```
✓ Created .claude-sync folder
✓ Created manifest.json
```

### `claude-sync status`

Mengecek apakah project sudah terinisialisasi dan **apakah Claude Code
terdeteksi di mesin ini**. Menampilkan hasilnya menggunakan Rich.

```bash
claude-sync status
```

Output (jika sudah diinisialisasi dan Claude ditemukan):
```
✓ Project initialized (.claude-sync/ present)
✓ Manifest found (manifest.json)

✓ Claude Path: /home/user/.claude
  Detected environment: WSL

Everything looks good.
```

Output (jika belum diinisialisasi):
```
✗ Project not initialized
  Missing: .claude-sync
  Run claude-sync init to initialize.

! Claude Path: Not Found
  Install Claude Code so its data can be synced.
```

### `claude-sync inspect`

Membaca struktur folder Claude Code (read-only) dan menampilkan statistik
jumlah entry di subfolder yang dilacak menggunakan Rich table.

```bash
claude-sync inspect
```

Output contoh:
```
Claude Path: /home/user/.claude

                  Claude Code Directory Structure
┏━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Subdirectory ┃ Status  ┃ Entries ┃ Path                         ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ sessions     │ present │      48 │ /home/user/.claude/sessions  │
│ projects     │ present │      12 │ /home/user/.claude/projects  │
│ tasks        │ present │       7 │ /home/user/.claude/tasks     │
│ plans        │ present │      10 │ /home/user/.claude/plans     │
│ session-env  │ present │      32 │ /home/user/.claude/session-env │
└──────────────┴─────────┴─────────┴──────────────────────────────┘

Summary: 5/5 tracked subdirs present, 109 total entries.
```

Opsi tambahan:
- `--claude-path PATH` — inspeksi path tertentu, lewati auto-detect
- `--no-locate` — jangan cari otomatis; gabungkan dengan `--claude-path`

### `claude-sync export`

Menyalin data Claude Code (`sessions`, `tasks`, `plans`, `session-env`)
dari `~/.claude` ke `./.claude-sync/data/`. Tujuan di-wipe lalu ditulis
ulang setiap kali, jadi file yang dihapus di source tidak akan
"tertinggal" di export.

```bash
claude-sync export
```

Output contoh:
```
Exporting from: /home/user/.claude
Exporting to:   /home/user/project/.claude-sync/data

                  Export Summary
┏━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Subdir      ┃ Files ┃          Status          ┃
┡━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ sessions    │    48 │          copied          │
│ tasks       │     7 │          copied          │
│ plans       │    10 │          copied          │
│ session-env │    32 │          copied          │
└─────────────┴───────┴──────────────────────────┘

✓ Exported 97 files into data/
```

Opsi tambahan:
- `--claude-path PATH` — sumber override (lewati locator)

### `claude-sync import`

Restore isi `.claude-sync/data/` ke `~/.claude`. Sebelum menimpa,
otomatis membuat backup `~/.claude.backup-YYYYMMDD-HHMMSS` agar
data lama bisa di-restore kalau terjadi masalah.

```bash
claude-sync import
```

Output contoh:
```
Importing from: /home/user/project/.claude-sync/data
Importing to:   /home/user/.claude
Backup created at: /home/user/.claude.backup-20260603-134512

                 Import Summary
┏━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Subdir      ┃ Files ┃          Status          ┃
┡━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ sessions    │    48 │       restored           │
│ tasks       │     7 │       restored           │
│ plans       │    10 │       restored           │
│ session-env │    32 │       restored           │
└─────────────┴───────┴──────────────────────────┘

✓ Restored 97 files from data/
✓ Backup kept at /home/user/.claude.backup-20260603-134512
```

Opsi tambahan:
- `--claude-path PATH` — tujuan override (lewati locator)
- `--no-backup` — lewati auto-backup (tidak disarankan)

### `claude-sync push`

Menjalankan `export` lalu commit + push ke remote Git. Memerlukan
folder `.claude-sync/` sudah terinisialisasi dan merupakan repository
Git dengan minimal satu remote.

```bash
claude-sync push
```

Alur:
1. Jalankan `export` (sinkronkan `~/.claude` → `.claude-sync/data/`)
2. `git add` + `git commit` (hanya jika ada perubahan)
3. `git push` ke branch & remote yang sedang aktif

Output contoh:
```
✓ Exported 97 files into data/
✓ Committed 3 file(s) with message: claude-sync: export 97 files at 2026-06-03T13:45:12
✓ Pushed to origin/main
```

Opsi tambahan:
- `--message / -m TEXT` — custom commit message
- `--no-export` — lewati export, langsung commit + push
- `--claude-path PATH` — sumber export override

### Autentikasi Git (Token-based)

`push` dan `pull` memanggil `git` langsung, jadi **autentikasi mengikuti
konfigurasi Git yang sudah ada di mesin Anda**. Karena `claude-sync` tidak
membungkus prompt password, Anda harus memastikan Git sudah bisa
berkomunikasi dengan remote sebelum menjalankan `push`/`pull`.

Cara-cara yang umum dipakai:

1. **Token GitHub (`ghp_*`, `github_pat_*`, dll) — paling umum**
   Token bisa dipasang di URL remote, atau lebih aman lewat helper:

   ```bash
   # Opsi A: simpan kredensial via helper (disarankan)
   git config --global credential.helper store
   git push   # masukkan username + token satu kali, tersimpan untuk berikutnya
   ```

   ```bash
   # Opsi B: embed token di URL remote (kurang aman, jangan di repo publik)
   git remote set-url origin https://<TOKEN>@github.com/<user>/<repo>.git
   ```

   `claude-sync push`/`pull` akan otomatis memakai kredensial yang tersimpan
   — **Anda tidak perlu mengetik token lagi setiap kali push/pull**, kecuali
   helper tidak dikonfigurasi atau token expired.

2. **SSH key** — kalau URL remote sudah `git@github.com:...`, Git akan
   memakai `~/.ssh/id_*` secara otomatis.

3. **GitHub CLI (`gh auth login`)** — setelah login, `gh` menulis
   kredensial ke store Git sehingga `claude-sync` ikut memanfaatkannya.

> ⚠️ **Catatan keamanan:** token di `https://<TOKEN>@github.com/...`
> akan tersimpan di `.git/config` (plain text). Untuk mesin bersama atau
> laptop yang sering di-clone ulang, gunakan `credential.helper` atau SSH.

### `claude-sync pull`

Menjalankan `git pull` lalu `import`. Aman dijalankan dari mana saja
karena `git` yang memutuskan apakah working tree bersih.

```bash
claude-sync pull
```

Alur:
1. `git pull` dari remote (fetch + merge/rebase)
2. Jalankan `import` (sinkronkan `.claude-sync/data/` → `~/.claude`)

Output contoh:
```
✓ Pulled from origin/main (2 commit(s))
✓ Restored 12 files from data/
✓ Backup kept at /home/user/.claude.backup-20260603-134530
```

Opsi tambahan:
- `--no-import` — lewati import, hanya pull
- `--claude-path PATH` — tujuan import override

## Cara Testing

Jalankan test suite dengan:

```bash
pytest
```

## Struktur Project

```
claude-sync/
├── src/
│   └── claude_sync/
│       ├── __init__.py
│       ├── cli.py                  # Entry point CLI (Typer app)
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── init.py             # `claude-sync init`
│       │   ├── status.py           # `claude-sync status`
│       │   ├── inspect.py          # `claude-sync inspect` (Tahap 3)
│       │   ├── export.py           # `claude-sync export` (Tahap 4)
│       │   ├── import_cmd.py       # `claude-sync import` (Tahap 5)
│       │   ├── push.py             # `claude-sync push` (Tahap 6)
│       │   └── pull.py             # `claude-sync pull` (Tahap 6)
│       └── utils/
│           ├── __init__.py
│           ├── config.py           # Path & manifest helpers
│           ├── claude_locator.py   # `ClaudeLocator` (Tahap 2)
│           ├── inspector.py        # `ClaudeInspector` (Tahap 3)
│           ├── exporter.py         # `ClaudeExporter` (Tahap 4)
│           ├── importer.py         # `ClaudeImporter` (Tahap 5)
│           └── git_sync.py         # `GitSync` helpers (Tahap 6)
├── tests/
├── pyproject.toml
├── README.md
└── .gitignore
```

## Roadmap

- **Tahap 1** — Inisialisasi project CLI (`init`, `status`) ✅
- **Tahap 2** — Deteksi folder Claude Code (Linux/Windows/WSL) ✅
- **Tahap 3** — Analisis struktur session Claude (`inspect`) ✅
- **Tahap 4** — Export manual (`export`) ✅
- **Tahap 5** — Import manual (`import`) ✅
- **Tahap 6** — Integrasi Git (`push`, `pull`) ✅
