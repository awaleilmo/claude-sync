# claude-sync

A CLI tool to synchronize Claude Code sessions across devices using Git.

> **Status:** Tahap 4 — Export manual. `init`, `status`, `inspect`, dan
> `export` (copy `sessions`/`tasks`/`plans`/`session-env` ke
> `.claude-sync/data/`) sudah diimplementasikan. Import dan Git sync
> belum.

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

Perintah yang tersedia di Tahap 1:

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
│       │   └── export.py           # `claude-sync export` (Tahap 4)
│       └── utils/
│           ├── __init__.py
│           ├── config.py           # Path & manifest helpers
│           ├── claude_locator.py   # `ClaudeLocator` (Tahap 2)
│           ├── inspector.py        # `ClaudeInspector` (Tahap 3)
│           └── exporter.py         # `ClaudeExporter` (Tahap 4)
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
- **Tahap 5** — Import manual
- **Tahap 6** — Integrasi Git (`push`, `pull`)
