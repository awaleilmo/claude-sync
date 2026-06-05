# Claude Sync v2 - Phase 4

PENTING

Lanjutkan dari Phase 3.

Semua fitur sebelumnya harus tetap berfungsi.

Kerjakan HANYA Phase 4.

Setelah selesai STOP.

Jangan lanjut ke Phase 5.

Jangan membuat compression.

Jangan membuat encryption.

Jangan membuat migration tool.

---

## Tujuan

Menyelesaikan masalah path Linux ↔ Windows.

Saat ini:

Export:

/home/awal/workspace/claude-sync

↓

-home-awal-workspace-claude-sync

Import:

D:/Project/claude-sync

↓

d--Project-claude-sync

Claude Code menggunakan nama folder project berdasarkan path.

Karena itu restore saat ini tidak selalu dapat digunakan lintas device.

---

## Konteks Hasil Testing

Hasil testing menunjukkan:

Jika folder:

-home-awal-workspace-claude-sync

direname menjadi:

d--Project-claude-sync

maka Claude Code dapat menemukan kembali session.

Artinya:

Masalah utama adalah nama folder project.

---

## Tujuan Phase Ini

Saat import:

Jangan restore menggunakan nama folder lama.

Restore menggunakan nama folder yang sesuai dengan current machine.

---

## Utility Baru

Buat utility baru:

ClaudeProjectMapper

Tujuan:

Melakukan transformasi nama folder Claude berdasarkan current project path.

---

## Behaviour

Current Path:

D:/Project/claude-sync

↓

Generate:

d--Project-claude-sync

---

Current Path:

/home/awal/workspace/claude-sync

↓

Generate:

-home-awal-workspace-claude-sync

---

Jangan hardcode Linux.

Jangan hardcode Windows.

Gunakan path yang sedang aktif.

---

## Manifest

Tambahkan metadata baru:

{
"project_id": "...",
"project_name": "...",
"source_project_path": "...",
"source_claude_project_folder": "..."
}

Catat informasi saat export.

---

## Import Behaviour Baru

Saat import:

1. baca manifest
2. baca current path
3. generate current claude folder name
4. restore menggunakan current folder name

Contoh:

Export:

-home-awal-workspace-claude-sync

Import:

D:/Project/claude-sync

↓

Restore:

d--Project-claude-sync

---

## Existing Folder Handling

Jika target folder sudah ada:

backup folder tersebut

restore ke folder yang sama

---

## Validation

Tambahkan validasi:

Jika project_name dalam project.json
tidak cocok dengan current folder name

Tampilkan warning.

Jangan abort.

User tetap boleh lanjut.

---

## Status Command

Tambahkan:

Source Claude Folder

Current Claude Folder

Contoh:

Source:
-home-awal-workspace-claude-sync

Current:
d--Project-claude-sync

---

## Doctor Command

Jika doctor tersedia:

Tambahkan:

Mapping Check

Output:

✓ Mapping Valid

atau

⚠ Source and Current Mapping Differ

---

## Progress Tracking

Update progress.md

Tambahkan:

* perubahan yang dilakukan
* file yang diubah
* hasil testing
* temuan baru

---

## Plan Tracking

Update plan.md

Tandai:

Phase 1 = Completed

Phase 2 = Completed

Phase 3 = Completed

Phase 4 = Completed

Phase 5 = Pending

---

## Output Yang Wajib Ditampilkan

1. File baru
2. File yang diubah
3. Ringkasan perubahan
4. Cara testing

---

## Testing Manual (User Wajib Melakukan)

### Test 1

Laptop

Project:

/home/awal/workspace/claude-sync

Jalankan:

claude-sync export

Periksa manifest.

Pastikan terdapat:

source_project_path

source_claude_project_folder

---

### Test 2

Push ke Git.

---

### Test 3

PC

Project:

D:/Project/claude-sync

Jalankan:

claude-sync import

---

### Test 4

Periksa:

~/.claude/projects/

Pastikan folder yang dibuat:

d--Project-claude-sync

bukan:

-home-awal-workspace-claude-sync

---

### Test 5

Buka VS Code.

Buka Claude Code.

Pastikan session dapat ditemukan.

---

### Test 6

Jalankan:

claude-sync status

Pastikan:

Source Claude Folder
Current Claude Folder

ditampilkan.

---

Setelah selesai:

STOP.

Jangan membuat compression.

Jangan membuat encryption.

Jangan membuat package format baru.

Jangan membuat password.

Jangan lanjut ke Phase 5.
