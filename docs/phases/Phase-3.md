# Claude Sync v2 - Phase 3

PENTING

Lanjutkan dari Phase 2.

Semua fitur sebelumnya harus tetap berfungsi.

Jangan menghapus fitur lama.

Kerjakan HANYA Phase 3.

Setelah selesai STOP.

Jangan lanjut ke Phase 4.

Jangan membuat compression.

Jangan membuat encryption.

Jangan membuat migration tool.

---

## Tujuan

Mengubah import dari:

Global Claude Restore

menjadi:

Project-Based Restore

---

## Konteks

Saat ini export sudah berbasis project.

Namun import masih memiliki risiko:

* overwrite project lain
* backup seluruh ~/.claude
* restore seluruh ~/.claude

Desain baru:

Import hanya project yang sedang aktif.

---

## Source Data

Gunakan hasil export dari:

.claude-sync/export/project/

Jangan menggunakan source lain.

---

## Current Project

Gunakan:

.claude-sync/project.json

sebagai identitas utama.

---

## Claude Project Folder

Gunakan resolver yang dibuat pada Phase 2.

Contoh:

Linux

/home/awal/workspace/claude-sync

↓

-home-awal-workspace-claude-sync

Windows

D:/Project/claude-sync

↓

d--Project-claude-sync

---

## Import Behaviour Baru

Saat:

claude-sync import

jangan lagi:

backup ~/.claude

jangan lagi:

restore ~/.claude

---

## Behaviour Yang Diinginkan

Import hanya:

~/.claude/projects/<current-project>

---

## Backup Behaviour Baru

Backup hanya folder target.

Contoh:

Jika target:

~/.claude/projects/d--Project-claude-sync

maka backup hanya:

~/.claude/projects/d--Project-claude-sync

menjadi:

~/.claude/backups/
d--Project-claude-sync-YYYYMMDD-HHMMSS

Jangan backup seluruh ~/.claude.

---

## Restore Behaviour

Restore hanya:

.claude-sync/export/project/

↓

~/.claude/projects/<current-project>

---

## Existing Target

Jika target project sudah ada:

1. backup target project
2. hapus target project
3. restore project baru

Jangan menyentuh project lain.

---

## Safety Validation

Sebelum restore:

Validasi:

* project.json exists
* export folder exists
* Claude path exists

Jika gagal:

abort.

Jangan melakukan restore sebagian.

---

## Status Command

Tambahkan informasi:

Export Available:
YES / NO

Current Claude Mapping: <folder-name>

---

## Progress Tracking

Update progress.md

Tambahkan:

* perubahan yang dilakukan
* file yang diubah
* hasil testing

---

## Plan Tracking

Update plan.md

Tandai:

Phase 1 = Completed

Phase 2 = Completed

Phase 3 = Completed

Phase 4 = Pending

---

## Output Yang Wajib Ditampilkan

1. File baru
2. File yang diubah
3. Ringkasan perubahan
4. Cara testing

---

## Testing Manual (User Wajib Melakukan)

### Test 1

Pastikan terdapat project lain pada Claude.

Contoh:

~/.claude/projects/

├── project-a
├── project-b
├── project-c

---

### Test 2

Masuk ke:

claude-sync

---

### Test 3

Jalankan:

claude-sync import

---

### Test 4

Pastikan hanya project:

claude-sync

yang berubah.

---

### Test 5

Pastikan:

project-a
project-b
project-c

tetap ada.

---

### Test 6

Buka Claude Code.

Pastikan session project masih dapat dibuka.

---

### Test 7

Pastikan backup hanya dibuat untuk:

target project

dan bukan seluruh ~/.claude.

---

Setelah selesai:

STOP.

Jangan membuat auto path mapping.

Jangan membuat compression.

Jangan membuat encryption.

Jangan membuat migrasi project.

Jangan lanjut ke Phase 4.
