# Claude Sync v2 — Phase 7C: Inspect Project

PENTING

Lanjutkan dari Phase 7B.

Semua fitur sebelumnya harus tetap berfungsi.

Kerjakan HANYA Phase 7C.

Setelah selesai STOP.

Jangan lanjut ke Phase 7D.

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
claude-sync inspect-project
```

untuk melihat metadata project yang sedang aktif.

Phase ini hanya membuat kemampuan inspect.

Belum ada registration status.

Belum ada doctor integration.

---

# Behaviour

Saat dijalankan dari root project:

```bash
claude-sync inspect-project
```

Tool harus membaca metadata yang sudah tersedia.

Jangan membuat metadata baru.

Jangan melakukan scanning seluruh Claude folder.

---

# Informasi Yang Ditampilkan

Minimal tampilkan:

```text
Project Name
Project ID
Current Path
Claude Folder
```

---

# Jika Tersedia

Tampilkan juga:

```text
Export Package
Encryption Status
```

Jika informasi tersebut memang sudah tersedia dari phase sebelumnya.

Jika tidak tersedia:

Tampilkan:

```text
N/A
```

Jangan membuat metadata tambahan hanya untuk memenuhi tampilan.

---

# Contoh Output

```text
Project Name: claude-sync

Project ID:
550e8400-e29b-41d4-a716-446655440000

Current Path:
/home/user/workspace/claude-sync

Claude Folder:
-home-user-workspace-claude-sync

Export Package:
project.claudepack

Encryption Status:
Enabled
```

---

# Package Detection

Jika:

```text
.claude-sync/project.claudepack
```

ada:

Tampilkan nama package.

Jika tidak ada:

```text
N/A
```

---

# Encryption Status

Jika metadata menunjukkan package terenkripsi:

```text
Enabled
```

Jika package legacy:

```text
Disabled
```

Jika tidak diketahui:

```text
N/A
```

---

# Error Handling

Jika:

```text
.claude-sync/project.json
```

tidak ditemukan:

Tampilkan error yang jelas.

Jangan crash.

Jika metadata rusak:

Tampilkan error yang jelas.

Jangan crash.

---

# Batas Scope

Boleh diubah:

* inspect-project command baru
* cli registration
* helper inspect jika diperlukan
* progress.md

Jangan mengubah:

* discover
* register
* status command
* doctor command
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

Jalankan:

```bash
claude-sync inspect-project
```

Pastikan metadata project tampil.

---

## Test 2

Pastikan:

```text
Project Name
Project ID
Current Path
Claude Folder
```

muncul.

---

## Test 3

Jika package tersedia:

Pastikan:

```text
Export Package
```

menampilkan:

```text
project.claudepack
```

---

## Test 4

Jika package terenkripsi:

Pastikan:

```text
Encryption Status: Enabled
```

muncul.

---

## Test 5

Rename sementara:

```text
.claude-sync/project.json
```

menjadi:

```text
project.json.bak
```

Jalankan:

```bash
claude-sync inspect-project
```

Pastikan muncul error yang jelas.

Tidak crash.

---

Setelah implementasi selesai:

STOP.

Tunggu instruksi user:

* lanjut ke Phase 7D
* perbaiki bug
* ulang implementasi
