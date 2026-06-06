# claude-sync Roadmap

## Phase 1: Project Identity
- [x] Buat `project.json` saat `claude-sync init`
- [x] UUID4 stable identifier (tidak berubah)
- [x] Dataclass `ProjectMetadata`
- [x] Status command menampilkan Project Name, ID, Version
- [x] `init` tidak overwrite `project.json` jika sudah ada
- [x] Tidak membuat doctor command (belum ada)

## Phase 2: Project-Based Export
- [x] Buat `ProjectResolver` utility (sudah ada di `project_path.py`)
- [x] `ProjectExporter` hanya export project folder yang aktif
- [x] Export layout baru: `.claude-sync/export/project/<folder>/`
- [x] Manifest menyertakan `project_id` dan `source_project_path`
- [x] Status command menampilkan Detected Claude Project Folder
- [x] Semua 79 test pass

## Phase 3: Project-Based Import
- [x] Import session data ke project target
- [x] Validasi project match (project.json, export, claude path)
- [x] Backup hanya target project folder
- [x] Restore dari `.claude-sync/export/project/` ke `~/.claude/projects/<current>/`
- [x] Tidak menyentuh project lain
- [x] Status command menampilkan Export Available dan Current Claude Mapping
- [x] Semua 89 test pass

## Phase 4: Automatic Path Mapping
- [x] Catat `source_project_path` dan `source_claude_project_folder` ke manifest saat export
- [x] `MANIFEST_VERSION` dinaikkan ke 2
- [x] Import restore selalu menggunakan folder hasil transformasi path mesin saat ini
- [x] Status menampilkan `Source Claude Folder` dan `Current Claude Folder`
- [x] `status --check-mapping` untuk verifikasi cepat (exit 0/1)
- [x] Validasi warning (bukan abort) saat `project_name` atau `source_claude_project_folder` tidak cocok
- [x] Semua 92 test pass

## Phase 5: Compression Package
- [x] Kompresi export package
- [x] Optimasi ukuran transfer

## Phase 6: AES Encryption
- [ ] Encryption untuk data sensitif
- [ ] Password-based key derivation

## Phase 7: Migration Tool
- [ ] Migrasi dari schema lama ke schema baru
- [ ] Auto-detect old projects
- [ ] Backup sebelum migrasi
