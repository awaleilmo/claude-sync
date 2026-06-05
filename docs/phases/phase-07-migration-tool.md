# Claude Sync v2 - Phase 7

PENTING

Lanjutkan dari Phase 6.

Semua fitur sebelumnya harus tetap berfungsi.

Kerjakan HANYA Phase 7.

Setelah selesai STOP.

Jangan lanjut ke Phase 8.

Jangan membuat cloud sync.

Jangan membuat remote server.

Jangan membuat SaaS.

Jangan membuat account system.

---

## Tujuan

Mempermudah adopsi Claude Sync pada project yang sudah ada.

Saat ini:

claude-sync init

harus dijalankan secara manual pada setiap project.

Hal ini tidak praktis jika user sudah memiliki banyak project Claude.

---

## Tujuan Phase Ini

Membuat kemampuan:

* discover
* register
* inspect

untuk project Claude yang sudah ada.

---

## Command Baru

claude-sync discover

---

## Behaviour

Scan:

~/.claude/projects

Cari seluruh project Claude yang tersedia.

Contoh:

-home-awal-workspace-nims-core

-home-awal-workspace-weblink

-home-awal-workspace-ws-interior

---

## Output

Tampilkan tabel:

Claude Folder
Project Name (best effort)
Status

Contoh:

nims-core
Not Registered

weblink
Registered

ws-interior
Not Registered

---

## Registration Command

Command baru:

claude-sync register

---

## Behaviour

Saat dijalankan dari root project:

claude-sync register

Tool:

1. membaca current path
2. generate claude folder mapping
3. membuat project.json jika belum ada
4. menyimpan metadata yang diperlukan

Jika project sudah ter-register:

tampilkan warning.

Jangan overwrite.

---

## Inspect Command

Command baru:

claude-sync inspect-project

---

## Behaviour

Tampilkan:

Project Name
Project ID
Current Path
Claude Folder
Export Package
Encryption Status

---

## Manifest Enhancement

Tambahkan metadata:

registered_at

last_export

last_import

Jika tersedia.

---

## Status Command

Tambahkan:

Registration Status

Contoh:

✓ Registered

atau

⚠ Not Registered

---

## Doctor Command

Jika tersedia:

Tambahkan pemeriksaan:

✓ Project Registered

atau

✗ Project Not Registered

---

## Progress Tracking

Update progress.md

Tambahkan:

* perubahan yang dilakukan
* file yang diubah
* hasil testing
* command baru

---

## Plan Tracking

Update plan.md

Tandai:

Phase 1 = Completed

Phase 2 = Completed

Phase 3 = Completed

Phase 4 = Completed

Phase 5 = Completed

Phase 6 = Completed

Phase 7 = Completed

Phase 8 = Pending

Tambahkan roadmap baru:

Phase 8
Usability Improvements

Phase 9
Git Hooks

Phase 10
Release Preparation

---

## Output Yang Wajib Ditampilkan

1. File baru
2. File yang diubah
3. Command baru
4. Cara testing

---

## Testing Manual (User Wajib Melakukan)

### Test 1

Pastikan terdapat beberapa project Claude.

Contoh:

nims-core
weblink
ws-interior

---

### Test 2

Jalankan:

claude-sync discover

Pastikan project ditemukan.

---

### Test 3

Masuk ke project yang belum terdaftar.

---

### Test 4

Jalankan:

claude-sync register

Pastikan:

project.json

dibuat.

---

### Test 5

Jalankan:

claude-sync inspect-project

Pastikan metadata tampil.

---

### Test 6

Jalankan:

claude-sync status

Pastikan status registrasi tampil.

---

Setelah selesai:

STOP.

Jangan membuat cloud sync.

Jangan membuat remote storage.

Jangan membuat Git hooks.

Jangan lanjut ke Phase 8.
