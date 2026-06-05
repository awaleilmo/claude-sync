# Claude Sync v2 — Phase 5C: Package Status & Tracking

PENTING

Lanjutkan dari Phase 5B.

Semua fitur sebelumnya harus tetap berfungsi.

Kerjakan HANYA Phase 5C.

Setelah selesai STOP.

Jangan lanjut ke Phase 5D.

Jangan membuat encryption.

Jangan membuat password.

Jangan membuat AES.

Jangan membuat migration.

Jangan mengubah export.

Jangan mengubah import.

Jangan mengubah restore flow.

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

Menambahkan informasi package ke status command.

Phase ini hanya berhubungan dengan:

* status command
* doctor command (jika tersedia)
* progress tracking
* plan tracking

Jangan menyentuh logic export/import.

---

# Status Command

Tambahkan informasi berikut:

```text
Package Format
Package Available
Package Size
```

Contoh:

```text
Package Format: Claudepack
Package Available: Yes
Package Size: 2.3 MB
```

Jika package tidak ada:

```text
Package Format: Folder
Package Available: No
Package Size: N/A
```

---

# Package Detection

Jika:

```text
.claude-sync/project.claudepack
```

ada:

anggap format:

```text
Claudepack
```

Jika tidak ada:

anggap format:

```text
Folder
```

Tidak perlu membaca isi package.

Tidak perlu extract package.

---

# Doctor Command

Lakukan hanya jika doctor command sudah tersedia.

Jika command doctor tidak ada:

JANGAN membuat doctor command baru.

Jika doctor command sudah ada:

Tambahkan:

```text
✓ Package Valid
```

atau

```text
✗ Package Corrupted
```

Validasi cukup:

* file ZIP dapat dibuka
* struktur package valid

Tidak perlu melakukan restore.

Tidak perlu extract seluruh package.

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

JANGAN menuliskan hasil testing.

Testing dilakukan oleh user.

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
Phase 6 = Pending
```

---

# Batas Scope

Boleh diubah:

* status command
* doctor command (jika sudah ada)
* progress.md
* plan.md

Jangan mengubah:

* exporter
* importer
* crypto
* project identity
* path mapping
* package format

Jika menemukan bug lain:

Catat di progress.md.

Jangan diperbaiki pada phase ini.

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

## Test 1 — Claudepack Available

Pastikan:

```text
.claude-sync/project.claudepack
```

ada.

Jalankan:

```bash
claude-sync status
```

Pastikan tampil:

```text
Package Format: Claudepack
Package Available: Yes
Package Size: ...
```

---

## Test 2 — No Package

Rename sementara:

```text
project.claudepack
```

menjadi:

```text
project.claudepack.bak
```

Jalankan:

```bash
claude-sync status
```

Pastikan tampil:

```text
Package Format: Folder
Package Available: No
```

---

## Test 3 — Doctor Validation

(Jika doctor command tersedia)

Jalankan:

```bash
claude-sync doctor
```

Pastikan package valid terdeteksi.

---

## Test 4 — Corrupt Package

Buat package rusak:

```bash
echo test > .claude-sync/project.claudepack
```

Jalankan:

```bash
claude-sync doctor
```

Pastikan:

```text
Package Corrupted
```

terdeteksi.

---

Setelah implementasi selesai:

STOP.

Tunggu instruksi user:

* lanjut ke Phase 6A
* perbaiki bug
* ulang implementasi
