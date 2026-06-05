# ARCHITECTURE.md — Claude Sync

> **Generated:** 2026-06-05
> **Version:** 0.1.0

---

## 1. Executive Summary

**claude-sync** adalah tools CLI berbasis Python untuk sinkronisasi data sesi Claude Code antar device melalui Git. Project ini memungkinkan user untuk:

- **Meng-export** seluruh data sesi Claude Code (sessions, tasks, plans, session-env, settings, memory) dari satu device ke format terstruktur di dalam folder `.claude-sync/`.
- **Meng-import** data yang tersinkronisasi kembali ke instalasi Claude Code di device lain.
- **Mendorong dan menarik** perubahan via Git (push/pull) sebagai mekanisme sync.
- **Melacak riwayat perubahan** file-file Claude Code menggunakan Git reflog dan log.
- **Memeriksa** isi dan struktur data `.claude-sync/`.
- **Memeriksa status** project, manifest, dan lokasi instalasi Claude.

Project ini dirancang untuk mengatasi masalah perpindahan data sesi Claude Code yang tidak portable secara native, dengan cara mem-backup, meng-export, dan meng-import secara terstruktur.

---

## 2. Project Structure

```
claude-sync/
├── pyproject.toml                 # Project metadata, dependencies, entry point
├── README.md                      # Dokumentasi user
├── ARCHITECTURE.md                # Dokumentasi arsitektur (file ini)
├── .gitignore                     # Git ignore rules
├── src/
│   └── claude_sync/
│       ├── __init__.py            # Version: 0.1.0
│       ├── cli.py                 # CLI entry point (Typer app, registrasi subcommands)
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── init.py            # `claude-sync init` — inisialisasi project
│       │   ├── status.py          # `claude-sync status` — cek status project & Claude
│       │   ├── inspect.py         # `claude-sync inspect` — periksa isi .claude-sync/
│       │   ├── export.py          # `claude-sync export` — copy data dari Claude Code
│       │   ├── import_cmd.py      # `claude-sync import` — restore data ke Claude Code
│       │   ├── push.py            # `claude-sync push` — git push ke remote
│       │   ├── pull.py            # `claude-sync pull` — git pull dari remote
│       │   └── trace.py           # `claude-sync trace` — lacak riwayat perubahan
│       └── utils/
│           ├── __init__.py
│           ├── config.py          # Configuration manager, manifest读写, path helpers
│           ├── claude_locator.py   # Penemuan lokasi .claude/ di filesystem
│           ├── exporter.py        # Logic export: copy tree, hitung file, report
│           ├── importer.py        # Logic import: restore, backup, collision handling
│           ├── inspector.py       # Tree inspection: hitung file per subdir
│           ├── git_sync.py        # Git integration: push/pull/commit via subprocess
│           └── trace.py           # Git reflog & log parsing untuk tracking
├── tests/
│   ├── test_init_command.py
│   ├── test_status_command.py
│   ├── test_inspect_command.py
│   ├── test_export_command.py
│   ├── test_exporter.py
│   ├── test_import_command.py
│   ├── test_importer.py
│   ├── test_push_pull_commands.py
│   ├── test_config.py
│   ├── test_claude_locator.py
│   ├── test_git_sync.py
│   ├── test_inspector.py
│   └── test_trace.py
├── .claude-sync/                  # Sync directory (generated per project)
│   ├── manifest.json              # Manifest metadata project
│   ├── data/                      # Exported Claude Code data
│   │   ├── sessions/
│   │   ├── tasks/
│   │   ├── plans/
│   │   ├── session-env/
│   │   ├── settings/
│   │   └── memory/
│   └── settings.json              # Project-level settings
├── .claude/                       # Claude Code local data (source)
│   └── settings.local.json
└── .claude-sync-trace.json        # Trace log (generated)
```

### Tanggung Jawab Setiap Folder

| Folder | Tanggung Jawab |
|--------|---------------|
| `src/claude_sync/` | Inti library: CLI, commands, utilities |
| `src/claude_sync/commands/` | Implementasi setiap subcommand CLI |
| `src/claude_sync/utils/` | Fungsi reusable: config, locator, exporter, importer, inspector, git, trace |
| `tests/` | 79 test cases, semua menggunakan `pytest` + `tmp_path` fixtures |
| `.claude-sync/` | Output directory per project (dihasilkan oleh `init`) |
| `.claude/` | Source data dari Claude Code (diread oleh export/import) |

---

## 3. CLI Flow

### `claude-sync init`

- **Entrypoint:** `src/claude_sync/cli.py` → `app.command("init")` → `src/claude_sync/commands/init.py`
- **Class/Fungsi:** `InitCommand.init()` (satu command class)
- **Util yang dipanggil:** `load_project_root()`, `find_claude_path()`, `ensure_dir()`, `write_json()`, `print_success/warning/error`
- **Flow:**
  1. Cek apakah project sudah terinisialisasi (`Path(".claude-sync")`)
  2. Cari instalasi Claude Code via `ClaudeLocator`
  3. Buat folder `.claude-sync/`
  4. Tulis `manifest.json` dengan metadata project (path Claude, versi, timestamp)
  5. Tulis `.gitignore` ke dalam `.claude-sync/`
  6. Print success message

### `claude-sync status`

- **Entrypoint:** `cli.py` → `src/claude_sync/commands/status.py`
- **Class/Fungsi:** `StatusCommand.status()`
- **Util:** `load_project_root()`, `ClaudeLocator.find_claude_path()`, `print_info/success/warning/error`
- **Flow:**
  1. Validasi project terinisialisasi (`.claude-sync/` + `manifest.json` harus ada)
  2. Cari instalasi Claude Code
  3. Tampilkan status: inisialisasi (yes/no), manifest (ada/hilang), path Claude (found/not found)
  4. Exit 0 jika semua OK, non-zero jika ada masalah

### `claude-sync inspect`

- **Entrypoint:** `cli.py` → `src/claude_sync/commands/inspect.py`
- **Class/Fungsi:** `InspectCommand.inspect()`
- **Util:** `load_project_root()`, `ClaudeLocator`, `load_settings()`, `Inspector`, `print_table()`, `print_tree()`
- **Flow:**
  1. Validasi project terinisialisasi
  2. Baca `settings.json` untuk mengetahui mode inspect (source, destination, atau both)
  3. Jika mode source: tampilkan struktur `.claude/`
  4. Jika mode destination: tampilkan struktur `.claude-sync/data/`
  5. Output dalam bentuk table + tree view menggunakan `rich`

### `claude-sync export`

- **Entrypoint:** `cli.py` → `src/claude_sync/commands/export.py`
- **Class/Fungsi:** `ExportCommand.export()`
- **Util:** `load_project_root()`, `ClaudeLocator`, `ExportReport`, `Exporter.export_data()`, `print_success/warning`
- **Flow:**
  1. Validasi project terinisialisasi
  2. Dapatkan path Claude Code (dari flag atau locator)
  3. Baca `settings.json` untuk konfigurasi export (source path, exclude patterns, subdir filter)
  4. Panggil `Exporter.export_data()` — copy tree dari `.claude/` ke `.claude-sync/data/`
  5. Tampilkan `ExportReport` (total file, subdir detail, excluded items)

### `claude-sync import`

- **Entrypoint:** `cli.py` → `src/claude_sync/commands/import_cmd.py`
- **Class/Fungsi:** `ImportCommand.import_cmd()`
- **Util:** `load_project_root()`, `ClaudeLocator`, `ImportReport`, `Importer.import_data()`, `print_success/warning/error`
- **Flow:**
  1. Validasi project terinisialisasi
  2. Dapatkan path Claude Code (dari flag atau locator)
  3. Baca `settings.json` untuk konfigurasi import (destination path, backup prefix, collision handling)
  4. Cek apakah destination ada — jika ya, buat backup sesuai setting
  5. Panggil `Importer.import_data()` — copy dari `.claude-sync/data/` ke `.claude/`
  6. Tampilkan `ImportReport` (total file, backup info, collision count)

### `claude-sync push`

- **Entrypoint:** `cli.py` → `src/claude_sync/commands/push.py`
- **Class/Fungsi:** `PushCommand.push()`
- **Util:** `load_project_root()`, `GitSync.push()`, `run_git_command()`, `print_info/success`
- **Flow:**
  1. Validasi project terinisialisasi
  2. Cek apakah folder adalah Git repository
  3. Cek apakah remote configured
  4. Jalankan `git add .claude-sync/ && git commit -m ... && git push`
  5. Tampilkan hasil commit hash dan status

### `claude-sync pull`

- **Entrypoint:** `cli.py` → `src/claude_sync/commands/pull.py`
- **Class/Fungsi:** `PullCommand.pull()`
- **Util:** `load_project_root()`, `GitSync.pull()`, `run_git_command()`, `print_info/warning`
- **Flow:**
  1. Validasi project terinisialisasi
  2. Cek apakah folder adalah Git repository
  3. Cek apakah remote configured
  4. Jalankan `git pull` untuk `.claude-sync/`
  5. Tampilkan hasil

### `claude-sync trace`

- **Entrypoint:** `cli.py` → `src/claude_sync/commands/trace.py`
- **Class/Fungsi:** `TraceCommand.trace()`
- **Util:** `load_project_root()`, `TraceTracker`, `run_git_command()`, `print_info/success/error`
- **Flow:**
  1. Validasi project terinisialisasi
  2. Baca `settings.json` untuk konfigurasi trace
  3. Jika target source (`.claude/`): baca Git log dari Git repository parent
  4. Jika target destination (`.claude-sync/`): baca Git log dari current repo
  5. Parse reflog untuk melihat perubahan file
  6. Tulis hasil ke `.claude-sync-trace.json` dan tampilkan summary

---

## 4. Dependency Graph

```
cli.py (entry point)
│
├── commands/init.py
│   ├── utils/config.py (load_project_root, ensure_dir, write_json)
│   ├── utils/claude_locator.py (ClaudeLocator.find_claude_path)
│   └── utils/git_sync.py (run_git_command)
│
├── commands/status.py
│   ├── utils/config.py (load_project_root)
│   └── utils/claude_locator.py (ClaudeLocator.find_claude_path)
│
├── commands/inspect.py
│   ├── utils/config.py (load_project_root, load_settings)
│   ├── utils/claude_locator.py (ClaudeLocator)
│   ├── utils/inspector.py (Inspector)
│   └── cli.py (print_table, print_tree) [internal helpers]
│
├── commands/export.py
│   ├── utils/config.py (load_project_root, load_settings)
│   ├── utils/claude_locator.py (ClaudeLocator)
│   ├── utils/exporter.py (ExportReport, Exporter)
│   └── cli.py (print_table, print_tree)
│
├── commands/import_cmd.py
│   ├── utils/config.py (load_project_root, load_settings)
│   ├── utils/claude_locator.py (ClaudeLocator)
│   ├── utils/importer.py (ImportReport, Importer)
│   └── cli.py (print_table, print_tree)
│
├── commands/push.py
│   ├── utils/config.py (load_project_root)
│   └── utils/git_sync.py (GitSync, run_git_command)
│
├── commands/pull.py
│   ├── utils/config.py (load_project_root)
│   └── utils/git_sync.py (GitSync, run_git_command)
│
└── commands/trace.py
    ├── utils/config.py (load_project_root, load_settings)
    ├── utils/trace.py (TraceTracker)
    └── utils/git_sync.py (run_git_command)
```

---

## 5. Export Architecture

### File yang Terlibat

| File | Peran |
|------|-------|
| `commands/export.py` | Command handler: parsing args, orchestrasi |
| `utils/exporter.py` | Core logic: tree copy, file counting, report generation |
| `utils/config.py` | Path resolution, settings loading |
| `utils/claude_locator.py` | Menemukan path `.claude/` |

### Class yang Terlibat

- **`ExportReport`** (`dataclass`): Menyimpan hasil export
  - `total_files: int` — total file yang di-export
  - `subdir_counts: dict[str, int]` — file count per subdir
  - `source_path: str` — path sumber (Claude Code)
  - `destination_path: str` — path tujuan (`.claude-sync/data/`)
  - `excluded_items: list[str]` — file/dir yang di-exclude
  - `settings: dict` — konfigurasi export yang digunakan

- **`Exporter`** (class): Engine export
  - `export_data(source, destination, settings)` — fungsi utama

### Fungsi yang Terlibat

- `ExportCommand.export()`: Command handler
  - Validasi project initialized
  - Resolve Claude path
  - Load settings
  - Panggil `Exporter.export_data()`
  - Tampilkan report

- `Exporter.export_data(source, destination, settings)`:
  - Baca `export_settings` dari config
  - Dapatkan `source_path` dan `destination_path`
  - Baca `excluded_patterns` dari config
  - Hapus isi `destination` jika ada (replace, bukan merge)
  - Buat subdirectory yang terdefinisi dalam `settings.tracked_subdirs`
  - Untuk setiap tracked subdir:
    - Jika ada di source: copy semua file ke destination
    - Jika tidak ada: skip (tidak error)
  - Hitung total file yang di-copy
  - Kembalikan `ExportReport`

### Data yang Dihasilkan

```
<project>/.claude-sync/
├── manifest.json          # Metadata project
├── settings.json          # Konfigurasi export/import
├── .gitignore             # Git ignore untuk .claude-sync/
└── data/                  # Hasil export
    ├── sessions/          # File dari .claude/sessions/
    ├── tasks/             # File dari .claude/tasks/
    ├── plans/             # File dari .claude/plans/
    ├── session-env/       # File dari .claude/session-env/
    ├── settings/          # File dari .claude/settings/
    └── memory/            # File dari .claude/memory/
```

### Diagram Alur Export

```
[User: claude-sync export]
        │
        ▼
[ExportCommand.export()]
        │
        ├── Validasi: project initialized?
        │         └── No → exit non-zero
        │
        ├── Resolve Claude path
        │         └── --flag atau ClaudeLocator
        │
        ├── Load settings.json
        │         └── Baca export settings
        │
        ▼
[Exporter.export_data()]
        │
        ├── Hapus destination (replace mode)
        │
        ├── Buat tracked subdirs
        │
        ├── Copy files per subdir
        │       │
        │       ├── sessions/  → .claude-sync/data/sessions/
        │       ���── tasks/     → .claude-sync/data/tasks/
        │       ├── plans/     → .claude-sync/data/plans/
        │       ├── session-env/ → .claude-sync/data/session-env/
        │       ├── settings/  → .claude-sync/data/settings/
        │       └── memory/    → .claude-sync/data/memory/
        │
        └── Generate ExportReport
              │
              ▼
[ExportReport: total_files, subdir_counts, excluded_items]
```

---

## 6. Import Architecture

### File yang Terlibat

| File | Peran |
|------|-------|
| `commands/import_cmd.py` | Command handler: parsing args, orchestrasi |
| `utils/importer.py` | Core logic: restore, backup, collision handling |
| `utils/config.py` | Path resolution, settings loading |
| `utils/claude_locator.py` | Menemukan path `.claude/` |

### Class yang Terlibat

- **`ImportReport`** (`dataclass`): Menyimpan hasil import
  - `total_files: int` — total file yang di-import
  - `subdir_counts: dict[str, int]` — file count per subdir
  - `backup_path: str | None` — lokasi backup jika ada
  - `collision_count: int` — jumlah file yang bentrok
  - `source_path: str` — path sumber (`.claude-sync/data/`)
  - `destination_path: str` — path tujuan (`.claude/`)
  - `collision_files: list[str]` — nama file yang bentrok
  - `settings: dict` — konfigurasi import yang digunakan

- **`Importer`** (class): Engine import
  - `import_data(source, destination, settings)` — fungsi utama

### Fungsi yang Terlibat

- `ImportCommand.import_cmd()`: Command handler
  - Validasi project initialized
  - Resolve Claude path
  - Load settings
  - Cek destination (jika ada → backup)
  - Panggil `Importer.import_data()`
  - Tampilkan report

- `Importer.import_data(source, destination, settings)`:
  - Baca `import_settings` dari config
  - Dapatkan `source_path` dan `destination_path`
  - Baca `collision_handling` dari config (backup/overwrite/interactive)
  - Jika destination ada: buat backup (timestamped suffix)
  - Untuk setiap tracked subdir di source:
    - Jika subdir ada di source: copy ke destination
    - Jika file bentrok: handle sesuai collision policy
  - Kembalikan `ImportReport`

### Proses Backup

1. Jika destination `.claude/` sudah ada dan `backup=True`:
   - Buat backup folder dengan timestamp suffix: `.claude-backup-YYYYMMDD_HHMMSS/`
   - Copy seluruh isi `.claude/` ke backup folder
   - Backup path disimpan di `ImportReport.backup_path`

2. Jika `backup=False`:
   - Langsung overwrite tanpa backup

### Diagram Alur Import

```
[User: claude-sync import]
        │
        ▼
[ImportCommand.import_cmd()]
        │
        ├── Validasi: project initialized?
        │         └── No → exit non-zero
        │
        ├── Resolve Claude path
        │
        ├── Load settings.json
        │
        ├── Cek destination (.claude/)
        │         │
        │         ├── Ada + backup=True → Backup!
        │         │   └── .claude-backup-YYYYMMDD_HHMMSS/
        │         │
        │         └── Tidak ada → Langsung
        │
        ▼
[Importer.import_data()]
        │
        ├── Copy files per subdir
        │       │
        │       ├── .claude-sync/data/sessions/ → .claude/sessions/
        │       ├── .claude-sync/data/tasks/    → .claude/tasks/
        │       ├── .claude-sync/data/plans/    → .claude/plans/
        │       ├── .claude-sync/data/session-env/ → .claude/session-env/
        │       ├── .claude-sync/data/settings/ → .claude/settings/
        │       └── .claude-sync/data/memory/   → .claude/memory/
        │
        ├── Handle collision (jika ada)
        │       ├── backup → backup file lama
        │       ├── overwrite → timpa
        │       └── increment → .claude/file.txt.bak1, .bak2, ...
        │
        └── Generate ImportReport
```

---

## 7. Git Integration

### File yang Terlibat

| File | Peran |
|------|-------|
| `utils/git_sync.py` | Semua logic Git: push, pull, commit, remote detection |
| `commands/push.py` | Command handler push |
| `commands/pull.py` | Command handler pull |

### Push Flow

```
[User: claude-sync push]
        │
        ▼
[PushCommand.push()]
        │
        ├── Validasi: project initialized?
        │
        ├── Cek: Git repo?
        │         └── No → warn "bukan Git repo"
        │
        ├── Cek: remote configured?
        │         └── No → warn "no remote"
        │
        ▼
[GitSync.push()]
        │
        ├── git add .claude-sync/
        ├── git commit -m "claude-sync: sync"
        ├── git push
        │
        ▼
[Hasil: commit hash, status]
```

### Pull Flow

```
[User: claude-sync pull]
        │
        ▼
[PullCommand.pull()]
        │
        ├── Validasi: project initialized?
        │
        ├── Cek: Git repo?
        │
        ├── Cek: remote configured?
        │         └── No → warn "no remote"
        │
        ▼
[GitSync.pull()]
        │
        ├── git pull
        │
        ▼
[Hasil: pull output]
```

### Remote Detection

- Menggunakan `git remote -v` untuk cek apakah ada remote configured
- Jika tidak ada: warn user bahwa push/pull tidak akan berhasil tanpa remote
- Tidak melakukan otomatis add remote — user harus setup sendiri

### Commit Strategy

- Auto-commit semua perubahan di `.claude-sync/` saat push
- Commit message: `"claude-sync: sync"`
- Tidak ada interaksi user — fully automatic

---

## 8. Configuration System

### config.json / Manifest (manifest.json)

**Lokasi:** `.claude-sync/manifest.json`

**Schema:**
```json
{
  "claude_path": "/home/user/.claude",
  "version": 1,
  "created_at": "2026-06-05T12:00:00",
  "updated_at": "2026-06-05T12:00:00"
}
```

- **`claude_path`**: Path absolut ke instalasi Claude Code (`~/.claude` atau setara)
- **`version`**: Schema version (saat ini `1`)
- **`created_at`**: Timestamp saat project diinisialisasi
- **`updated_at`**: Timestamp terakhir di-update

### Project Settings (settings.json)

**Lokasi:** `.claude-sync/settings.json`

Berisi konfigurasi untuk semua command:
- `track_subdirs`: Daftar subdir yang di-track
- `excluded_patterns`: Pattern file/dir yang di-exclude saat export
- `export_settings`: Konfigurasi export (source path, dst)
- `import_settings`: Konfigurasi import (destination path, backup prefix, collision handling)
- `trace_settings`: Konfigurasi trace (enabled/disabled, log file)

### Path Resolution

1. **Project Root**: Current working directory saat CLI dijalankan
2. **Claude Path**: 
   - Diprioritaskan dari flag `--claude-path`
   - Jika tidak ada: `ClaudeLocator.find_claude_path()` mencari di lokasi standar
   - Jika tidak ditemukan: command gagal dengan error
3. **Sync Directory**: `<project_root>/.claude-sync/`
4. **Data Directory**: `<project_root>/.claude-sync/data/`

### Project Root Detection

- Tidak ada otomatis detection — project root adalah CWD saat CLI dijalankan
- Setelah `init`, folder `.claude-sync/` menandakan bahwa CWD adalah project yang terinisialisasi
- Command berikutnya di CWD yang sama akan langsung terdeteksi sebagai project initialized

---

## 9. Data Model Inventory

| Model | Lokasi | Tipe | Fungsi |
|-------|--------|------|--------|
| `ExportReport` | `utils/exporter.py` | `@dataclass` | Menyimpan hasil operasi export |
| `ImportReport` | `utils/importer.py` | `@dataclass` | Menyimpan hasil operasi import |
| `SubdirStat` | `utils/inspector.py` | `@dataclass` | Statistik satu subdir (file count, size, dll) |
| `InspectorResult` | `utils/inspector.py` | `@dataclass` | Hasil inspect dari seluruh tree |
| `TraceTracker` | `utils/trace.py` | Class | Melacak perubahan file via Git |
| `TraceResult` | `utils/trace.py` | `@dataclass` | Hasil operasi trace |
| `GitSync` | `utils/git_sync.py` | Class | Operasi Git (push/pull/commit) |
| `ClaudeLocator` | `utils/claude_locator.py` | Class | Menemukan path `.claude/` di filesystem |
| `InitCommand` | `commands/init.py` | Class | Command handler init |
| `StatusCommand` | `commands/status.py` | Class | Command handler status |
| `InspectCommand` | `commands/inspect.py` | Class | Command handler inspect |
| `ExportCommand` | `commands/export.py` | Class | Command handler export |
| `ImportCommand` | `commands/import_cmd.py` | Class | Command handler import |
| `PushCommand` | `commands/push.py` | Class | Command handler push |
| `PullCommand` | `commands/pull.py` | Class | Command handler pull |
| `TraceCommand` | `commands/trace.py` | Class | Command handler trace |

### Manifest Schema

```json
{
  "claude_path": str,       // Lokasi .claude/
  "version": int,           // Schema version (1)
  "created_at": str,        // ISO format timestamp
  "updated_at": str         // ISO format timestamp
}
```

---

## 10. Platform Compatibility

### Linux

- **Status:** ✅ Fully supported
- Claude Code berjalan di `~/.claude/`
- Path separator `/` (native)
- Git command tersedia
- File permissions normal

### WSL (Windows Subsystem for Linux)

- **Status:** ⚠️ Partially supported
- Claude Code bisa ada di `~/.claude/` di WSL filesystem
- Tapi Claude Code sebenarnya berjalan di Windows, data bisa di `C:\Users\<user>\.claude\`
- Cross-filesystem path handling (`/mnt/c/...`) mungkin perlu mapping
- Git di WSL bisa berbeda dari Git di Windows host

### Windows

- **Status:** ❌ Limited support
- Path separator `\` vs `/` — bisa jadi masalah
- `~/.claude/` mungkin di `C:\Users\<user>\.claude\` atau `AppData\Roaming\...`
- Git command tersedia tapi syntax bisa berbeda
- No explicit Windows path normalization di codebase

### Bagian yang Sudah Portable

- Semua path menggunakan `pathlib.Path` (cross-platform)
- Git command via `subprocess` (tersedia di semua platform)
- JSON serialization (cross-platform)
- File copy menggunakan `shutil.copy2` (preserves metadata)

### Bagian yang Belum Portable

- Hardcoded assumption path `.claude/` — bisa berbeda di Windows
- `ClaudeLocator` mungkin tidak menemukan Claude Code di Windows
- No explicit path normalization untuk Windows backslashes
- Git command langsung (tidak pakai library seperti `gitpython`)

---

## 11. Technical Debt

| Issue | Lokasi | Severity | Deskripsi |
|-------|--------|----------|-----------|
| **Hardcoded tracked subdirs** | `utils/config.py`, `utils/exporter.py`, `utils/importer.py` | MEDIUM | Daftar subdir (`sessions`, `tasks`, `plans`, dll) di-hardcode di beberapa tempat, tidak terpusat |
| **No encryption** | Seluruh codebase | HIGH | Data Claude Code (termasuk sesi, memory, settings) di-copy dalam plaintext ke `.claude-sync/` — siapa pun yang punya akses repo bisa membaca semua data |
| **No path mapping** | `utils/exporter.py`, `utils/importer.py` | HIGH | Tidak ada mekanisme untuk memetakan path absolut dari satu device ke device lain. Jika Claude Code ada di path berbeda, import akan gagal atau ke path yang salah |
| **Git command via subprocess** | `utils/git_sync.py` | LOW | Menggunakan `subprocess.run("git ...")` — fragile jika git output berubah, tidak ada error handling yang robust |
| **No validation of settings.json** | `utils/config.py` | LOW | Tidak ada schema validation untuk `settings.json` — user bisa salah konfigurasi tanpa feedback |
| **Replace-only export** | `utils/exporter.py` | MEDIUM | Export selalu menghapus isi destination (`shutil.rmtree`) — tidak ada incremental export. Ini juga berarti jika export terputus, data hilang |
| **No concurrency/safety** | `utils/exporter.py`, `utils/importer.py` | MEDIUM | Tidak ada file locking — jika Claude Code sedang menulis file saat export/import, data bisa korup atau tidak konsisten |
| **Trace depends on Git** | `utils/trace.py` | MEDIUM | Trace hanya bekerja jika Claude Code data ada di Git repo — tidak ada fallback mechanism |
| **Single version string** | `__init__.py` | LOW | Version masih `0.1.0` — mungkin perlu bump untuk release |
| **Duplicate CLI helpers** | `commands/` files | LOW | Setiap command module mengimpor `print_success`, `print_error`, dll secara individual — bisa di-refactor ke shared CLI utility |

---

## 12. Current Sync Limitation

### Mengapa Session Claude Code Tidak Dapat Dipindahkan Sempurna Antar Device

**Bukti dari source code:**

1. **Tidak Ada Path Mapping (Critical)**
   - `utils/exporter.py` dan `utils/importer.py` hanya melakukan copy file mentah
   - Tidak ada logika untuk memetakan path absolut dari device A ke device B
   - Jika Claude Code di device A ada di `/home/userA/.claude/` dan di device B di `/home/userB/.claude/`, maka:
     - File yang berisi referensi path absolut akan rusak saat di-import ke device B
     - Settings, memory files, atau session metadata yang menyimpan path absolut tidak akan berfungsi

2. **Tidak Ada Encryption (Critical)**
   - `utils/exporter.py` menggunakan `shutil.copy2()` — plaintext copy
   - Seluruh data Claude Code (termasuk session tokens, AI conversations, memory files) disimpan tanpa enkripsi di `.claude-sync/data/`
   - Siapa pun yang punya akses ke Git repo bisa membaca semua isi

3. **Tidak Ada Session Validation**
   - Tidak ada pengecekan apakah session file valid atau belum expired
   - `utils/exporter.py` menyalin semua file tanpa filtering berdasarkan status
   - Session yang sudah tidak valid tetap di-export dan di-import

4. **Cross-Device Path Incompatibility**
   - File di `.claude/` bisa berisi path absolut ke file lokal device
   - Saat di-import ke device lain, path tersebut tidak akan valid
   - Tidak ada mekanisme "auto path mapping" atau "relative path conversion"

5. **No Package/Format Standard**
   - `.claude-sync/data/` adalah tree folder biasa — bukan format terstruktur seperti ZIP/Archive
   - Tidak ada manifest yang melacak versi file, checksum, atau dependencies
   - Sulit untuk memvalidasi integritas data saat import

6. **Dependency pada Git Repo yang Sama**
   - `utils/git_sync.py` menganggap seluruh project ada di Git repo yang sama
   - Tidak support push ke satu remote dan pull dari remote yang berbeda secara aman
   - Tidak ada mechanism untuk handle conflict saat sync dari 3+ device

---

## 13. Impact Analysis — Transition to Project-Based Session Sync

Jika project diubah menjadi **Project-Based Session Sync**, berikut file yang perlu diubah:

| File | Reason | Risk |
|------|--------|------|
| `utils/exporter.py` | Perlu enkripsi, per-project package format, path mapping | HIGH — core logic |
| `utils/importer.py` | Perlu decrypt, validate, path remapping | HIGH — core logic |
| `utils/config.py` | Perlu project-scoped config, version bump | MEDIUM — schema change |
| `utils/claude_locator.py` | Perlu support multi-path resolution per project | LOW —扩展 |
| `utils/git_sync.py` | Perlu selective commit, per-package sync | MEDIUM — Git logic |
| `utils/inspector.py` | Perlu report per-project session stats | LOW — reporting |
| `utils/trace.py` | Perlu per-project trace isolation | MEDIUM — trace logic |
| `commands/export.py` | Perlu argumen project identifier | LOW — UI change |
| `commands/import_cmd.py` | Perlu argumen project identifier | LOW — UI change |
| `commands/push.py` | Perlu selective push per project | MEDIUM — Git logic |
| `commands/pull.py` | Perlu selective pull per project | MEDIUM — Git logic |
| `commands/init.py` | Perlu project scope definition | MEDIUM — init logic |
| `commands/status.py` | Perlu project-aware status | LOW — reporting |
| `commands/inspect.py` | Perlu project-aware inspection | LOW — reporting |
| `commands/trace.py` | Perlu project-scoped trace | MEDIUM — trace logic |
| `pyproject.toml` | Update dependencies jika perlu enkripsi library | LOW — metadata |
| `tests/` | Semua test perlu update untuk project-based | MEDIUM — test coverage |

---

## 14. Refactor Recommendation

### Phase 1 — Foundation (Perbaikan Dasar)

**Tujuan:** Perbaiki technical debt kritis tanpa mengubah user-facing API

- [ ] Tambahkan schema validation untuk `settings.json`
- [ ] Sentralisasi daftar `tracked_subdirs` — satu sumber kebenaran
- [ ] Tambahkan file locking saat export/import untuk mencegah race condition
- [ ] Improve error handling di `git_sync.py`
- [ ] Bump manifest version ke 2

### Phase 2 — Project-Based Architecture

**Tujuan:** Ubah dari single-device sync menjadi project-based session sync

- [ ] Desain per-project session format (ZIP/package encrypted)
- [ ] Tambahkan project identifier di manifest
- [ ] Ubah `export` untuk menghasilkan per-project session package
- [ ] Ubah `import` untuk membaca session package dengan path mapping
- [ ] Tambahkan `project` command untuk manajemen multi-project

### Phase 3 — Cross-Platform Support

**Tujuan:** Dukungan penuh untuk Windows, WSL, macOS

- [ ] Implement auto path mapping (absolute → relative → absolute per device)
- [ ] Tambahkan platform detection dan path normalization
- [ ] Support multiple Claude Code installation paths per platform
- [ ] Test di semua platform

### Phase 4 — Advanced Features

**Tujuan:** Fitur lanjutan untuk production-ready

- [ ] Enkripsi end-to-end untuk session packages
- [ ] Incremental export (hanya file yang berubah)
- [ ] Conflict resolution yang lebih sophisticated
- [ ] Dashboard/report untuk session stats
- [ ] Auto-sync dengan configurable interval
