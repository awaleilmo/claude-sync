# Claude Sync v2 — Phase 7A: Discover Existing Claude Projects

PENTING

Lanjutkan dari Phase 6F.

Semua fitur sebelumnya harus tetap berfungsi.

Kerjakan HANYA Phase 7A.

Setelah selesai STOP.

Jangan lanjut ke Phase 7B.

Jangan membuat register command.

Jangan membuat inspect-project command.

Jangan mengubah status command.

Jangan mengubah doctor command.

Jangan mengubah export/import.

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

Menambahkan command:

```bash
claude-sync discover
```

untuk melihat project Claude yang sudah ada.

Phase ini hanya membuat kemampuan discover.

Belum ada register.

Belum ada inspect.

---

# Behaviour

Scan:

```text
~/.claude/projects/
```

Cari seluruh folder project Claude.

Contoh:

```text
-home-awal-workspace-nims-core
-home-awal-workspace-weblink
-home-awal-workspace-ws-interior
```

---

# Output

Tampilkan tabel:

```text
Claude Folder
Project Name
Status
```

Contoh:

```text
Claude Folder                      Project Name     Status
----------------------------------------------------------------
-home-awal-workspace-nims-core     nims-core        Unknown
-home-awal-workspace-weblink       weblink          Unknown
-home-awal-workspace-ws-interior   ws-interior      Unknown
```

---

# Project Name

Gunakan best effort extraction.

Jika tidak bisa ditentukan:

```text
Unknown
```

Jangan membuat reverse path mapping yang kompleks.

Jangan mencoba menebak path asli.

---

# Status

Untuk Phase 7A:

Selalu tampilkan:

```text
Unknown
```

Status registration akan dikerjakan pada Phase 7D.

---

# Error Handling

Jika:

```text
~/.claude/projects
```

tidak ada:

Tampilkan pesan yang jelas.

Jangan crash.

---

# Batas Scope

Boleh diubah:

* discover command baru
* cli registration
* helper discover jika diperlukan
* progress.md

Jangan mengubah:

* register
* inspect-project
* status command
* doctor command
* exporter
* importer
* crypto
* project identity

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

* command baru
* file yang diubah
* alasan perubahan

Jangan menuliskan hasil testing.

---

# Output Yang Wajib Ditampilkan

1. File baru
2. File yang diubah
3. Command baru
4. Ringkasan perubahan
5. Checklist testing manual

Jangan menjalankan test.

Jangan menampilkan hasil test.

---

# Testing Manual (User Wajib Melakukan)

## Test 1

Pastikan terdapat beberapa project Claude.

Contoh:

```text
~/.claude/projects/
├── project-a
├── project-b
├── project-c
```

---

## Test 2

Jalankan:

```bash
claude-sync discover
```

Pastikan seluruh project muncul.

---

## Test 3

Rename sementara:

```text
~/.claude/projects
```

Jalankan:

```bash
claude-sync discover
```

Pastikan muncul error yang jelas.

Tidak crash.

---

Setelah implementasi selesai:

STOP.

Tunggu instruksi user:

* lanjut ke Phase 7B
* perbaiki bug
* ulang implementasi
