# Claude Sync v2 - Phase 2

PENTING

Lanjutkan dari Phase 1.

Semua fitur Phase 1 harus tetap berfungsi.

Jangan menghapus fitur lama.

Jangan mengimplementasikan import.

Jangan mengimplementasikan compression.

Jangan mengimplementasikan encryption.

Jangan mengimplementasikan migration.

Kerjakan HANYA Phase 2.

Setelah selesai STOP.

---

## Tujuan

Mengubah export dari:

Global Claude Export

menjadi:

Project-Based Export

---

## Konteks

Saat ini export masih membaca seluruh data Claude.

Padahal hasil testing menunjukkan bahwa session Claude terikat ke folder project tertentu.

Contoh:

~/.claude/projects/-home-awal-workspace-claude-sync

Desain baru:

Export hanya project yang sedang aktif.

---

## Project Identity

Gunakan:

.claude-sync/project.json

yang dibuat pada Phase 1.

Jangan membuat identitas baru.

---

## Tugas

Buat resolver baru.

Contoh:

ProjectResolver

Tujuan:

Menentukan folder project Claude yang terkait dengan current project.

---

## Current Project Path

Contoh:

Linux

/home/awal/workspace/claude-sync

Windows

D:/Project/claude-sync

---

## Claude Project Folder

Claude menggunakan format folder:

-home-awal-workspace-claude-sync

atau

d--Project-claude-sync

Buat utility khusus yang menghasilkan format tersebut.

Jangan hardcode.

Buat fungsi reusable.

---

## Export Behaviour Baru

Saat:

claude-sync export

jangan lagi menyalin:

~/.claude/projects/*

Tetapi hanya:

~/.claude/projects/<current-project>

---

## Data Export

Untuk Phase 2 export cukup:

projects/<current-project>

Jangan export:

history.jsonl
memory
settings.json
tasks
sessions

kita akan evaluasi nanti.

Fokus dulu membuktikan project-only export.

---

## Struktur Baru

.claude-sync/

├── project.json
├── manifest.json
└── export/
└── project/

---

## Manifest

Tambahkan metadata:

{
"project_id": "...",
"project_name": "...",
"source_project_path": "...",
"claude_project_folder": "..."
}

---

## Status Command

Tambahkan:

Detected Claude Project Folder

Contoh:

-home-awal-workspace-claude-sync

---

## Progress Tracking

Update progress.md

Tambahkan:

* perubahan yang dilakukan
* alasan perubahan
* hasil testing

---

## Plan Tracking

Update plan.md

Tandai:

Phase 1 = Completed

Phase 2 = Completed

Phase 3 = Pending

---

## Output Yang Wajib Ditampilkan

1. File baru
2. File yang diubah
3. Ringkasan arsitektur baru
4. Cara testing

---

## Testing Manual (User Wajib Melakukan)

1.

Masuk ke project:

claude-sync

2.

Jalankan:

claude-sync export

3.

Pastikan:

.claude-sync/export/project/

terisi.

4.

Pastikan hanya ada satu project Claude yang diexport.

5.

Pastikan project lain tidak ikut.

6.

Jalankan:

claude-sync status

7.

Pastikan:

Detected Claude Project Folder

ditampilkan.

---

Setelah selesai:

STOP.

Jangan membuat import.

Jangan membuat compression.

Jangan membuat encryption.

Jangan membuat auto path mapping.
