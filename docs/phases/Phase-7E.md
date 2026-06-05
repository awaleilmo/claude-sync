# Claude Sync v2 — Phase 7E: Registration Doctor

PENTING

Lanjutkan dari Phase 7D.

Semua fitur sebelumnya harus tetap berfungsi.

Kerjakan HANYA Phase 7E.

Setelah selesai STOP.

Jangan lanjut ke Phase 8.

Jangan mengubah export/import.

Jangan mengubah discover.

Jangan mengubah register.

Jangan mengubah inspect-project.

Jangan mengubah status command.

---

# MODE SAAT INI

IMPLEMENTATION ONLY

Dilarang:

* Menjalankan pytest
* Menjalankan unit test
* Menjalankan integration test
* Menjalankan manual test
* Menjalankan benchmark
* Menjalankan coverage
* Menjalankan debugging iteratif
* Menjalankan tool untuk memverifikasi implementasi

User akan melakukan testing sendiri.

Jika implementasi selesai:

STOP.

Tunggu hasil testing dari user.

---

# Tujuan

Menambahkan pemeriksaan registrasi project ke:

```bash
claude-sync doctor
```

Phase ini hanya mengubah doctor reporting.

Tidak mengubah behaviour command lain.

---

# Doctor Checks Baru

Tambahkan:

```text
Project Registered
Project Not Registered
Project Metadata Valid
Project Metadata Invalid
```

---

# Contoh Output

## Project Registered

```text
✓ Project Registered
✓ Project Metadata Valid
```

---

## Project Not Registered

```text
✗ Project Not Registered
```

---

## Metadata Rusak

```text
✗ Project Metadata Invalid
```

---

# Validation Rules

## Project Registered

Jika:

```text
.claude-sync/project.json
```

ada dan valid.

Tampilkan:

```text
✓ Project Registered
```

---

## Project Not Registered

Jika:

```text
.claude-sync/project.json
```

tidak ada.

Tampilkan:

```text
✗ Project Not Registered
```

---

## Project Metadata Valid

Validasi minimal:

```json
{
  "project_id": "...",
  "project_name": "..."
}
```

Jika field wajib tersedia:

```text
✓ Project Metadata Valid
```

---

## Project Metadata Invalid

Jika:

* JSON rusak
* field wajib hilang
* format tidak valid

Tampilkan:

```text
✗ Project Metadata Invalid
```

---

# Jika Doctor Command Belum Ada

JANGAN membuat doctor command baru.

Kerjakan phase ini hanya jika doctor command memang sudah tersedia.

Jika doctor command tidak ada:

Tuliskan pada output bahwa phase ini tidak memerlukan perubahan kode.

STOP.

---

# Performance

Doctor command tidak boleh:

* menjalankan discover
* scan seluruh ~/.claude/projects
* membaca package besar
* meminta password
* melakukan export/import

Doctor hanya memeriksa metadata project saat ini.

---

# Batas Scope

Boleh diubah:

* doctor command
* helper doctor jika diperlukan
* progress.md
* plan.md

Jangan mengubah:

* discover
* register
* inspect-project
* status command
* exporter
* importer
* crypto
* path mapping

Jika menemukan bug lain:

Catat di progress.md.

Jangan diperbaiki pada phase ini.

---

# Progress Tracking

Update:

```text
progress.md
```

Tambahkan:

* perubahan yang dilakukan
* file yang diubah
* alasan perubahan

Jangan menuliskan hasil testing.

---

# Plan Tracking

Update:

```text
plan.md
```

Tandai:

```text
Phase 1 = Completed
Phase 2 = Completed
Phase 3 = Completed
Phase 4 = Completed
Phase 5 = Completed
Phase 6 = Completed
Phase 7 = Completed
```

Hapus:

```text
Phase 7 = Pending
```

Jangan menambahkan roadmap baru.

Jangan membuat Phase 8.

Jangan membuat Git Hooks.

Jangan membuat Release Preparation.

---

# Batas Akhir Roadmap

Phase 7 adalah phase terakhir.

Setelah Phase 7 selesai:

Claude Sync dianggap mencapai:

```text
Version 1.0
```

Tidak ada phase lanjutan pada roadmap ini.

---

# Output Yang Wajib Ditampilkan

1. File baru
2. File yang diubah
3. Ringkasan perubahan
4. Checklist testing manual

Jangan menjalankan test.

Jangan menampilkan hasil test.

---

# Testing Manual (User Wajib Melakukan)

## Test 1 — Registered Project

Pastikan:

```text
.claude-sync/project.json
```

ada.

Jalankan:

```bash
claude-sync doctor
```

Pastikan tampil:

```text
✓ Project Registered
✓ Project Metadata Valid
```

---

## Test 2 — Not Registered

Rename sementara:

```text
project.json
```

menjadi:

```text
project.json.bak
```

Jalankan:

```bash
claude-sync doctor
```

Pastikan tampil:

```text
✗ Project Not Registered
```

---

## Test 3 — Corrupted Metadata

Rusak isi:

```text
project.json
```

Jalankan:

```bash
claude-sync doctor
```

Pastikan tampil:

```text
✗ Project Metadata Invalid
```

Tidak crash.

---

## Test 4 — Existing Doctor Checks

Pastikan seluruh pemeriksaan doctor sebelumnya masih muncul.

Tidak boleh ada regression.

---

Setelah implementasi selesai:

STOP.

Tunggu instruksi user:

* perbaiki bug
* revisi roadmap
* release v1.0
