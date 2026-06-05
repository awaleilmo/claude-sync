# Claude Sync v2 — Phase 7D: Registration Status

PENTING

Lanjutkan dari Phase 7C.

Semua fitur sebelumnya harus tetap berfungsi.

Kerjakan HANYA Phase 7D.

Setelah selesai STOP.

Jangan lanjut ke Phase 7E.

Jangan mengubah doctor command.

Jangan mengubah export/import.

Jangan mengubah discover.

Jangan mengubah register.

Jangan mengubah inspect-project.

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

Menambahkan informasi registrasi ke:

```bash
claude-sync status
```

Phase ini hanya mengubah status reporting.

Tidak mengubah behaviour command lain.

---

# Status Baru

Tambahkan:

```text
Registration Status
```

---

# Registered

Jika:

```text
.claude-sync/project.json
```

ada dan valid

Tampilkan:

```text
✓ Registered
```

---

# Not Registered

Jika:

```text
.claude-sync/project.json
```

tidak ada

Tampilkan:

```text
⚠ Not Registered
```

---

# Contoh Output

## Registered

```text
Project Name: claude-sync
Project ID: 550e8400-e29b-41d4-a716-446655440000

Registration Status:
✓ Registered
```

---

## Not Registered

```text
Registration Status:
⚠ Not Registered
```

---

# Metadata Validation

Validasi minimal:

```json
{
  "project_id": "...",
  "project_name": "..."
}
```

Jika metadata rusak:

perlakukan sebagai:

```text
⚠ Not Registered
```

Jangan crash.

---

# Performance

Status command tidak boleh:

* scan ~/.claude/projects
* menjalankan discover
* membaca package besar
* meminta password

Status harus tetap ringan.

---

# Batas Scope

Boleh diubah:

* status command
* helper status jika diperlukan
* progress.md
* plan.md

Jangan mengubah:

* discover
* register
* inspect-project
* doctor command
* exporter
* importer
* crypto

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
Phase 7D = Completed
Phase 7E = Pending
```

Jangan mengubah roadmap lain.

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
claude-sync status
```

Pastikan tampil:

```text
✓ Registered
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
claude-sync status
```

Pastikan tampil:

```text
⚠ Not Registered
```

---

## Test 3 — Corrupted Metadata

Rusak isi:

```text
project.json
```

Jalankan:

```bash
claude-sync status
```

Pastikan:

```text
⚠ Not Registered
```

muncul.

Tidak crash.

---

Setelah implementasi selesai:

STOP.

Tunggu instruksi user:

* lanjut ke Phase 7E
* perbaiki bug
* ulang implementasi
