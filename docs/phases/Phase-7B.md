# Claude Sync v2 — Phase 7B: Register Existing Project

PENTING

Lanjutkan dari Phase 7A.

Semua fitur sebelumnya harus tetap berfungsi.

Kerjakan HANYA Phase 7B.

Setelah selesai STOP.

Jangan lanjut ke Phase 7C.

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
claude-sync register
```

untuk mendaftarkan project yang sudah ada.

Phase ini hanya membuat kemampuan register.

Belum ada inspect-project.

Belum ada registration status.

---

# Behaviour

Saat dijalankan dari root project:

```bash
claude-sync register
```

Tool harus:

1. membaca current working directory
2. menentukan Claude folder mapping
3. memeriksa apakah project sudah terdaftar
4. membuat metadata project jika belum ada

---

# Registration Target

Gunakan:

```text
.claude-sync/project.json
```

sebagai sumber identitas project.

Jika belum ada:

buat menggunakan mekanisme yang sama seperti:

```bash
claude-sync init
```

---

# Jika Project Sudah Terdaftar

Contoh:

```text
.claude-sync/project.json
```

sudah ada.

Maka:

Tampilkan warning.

Jangan overwrite.

Jangan generate UUID baru.

Jangan mengubah metadata yang sudah ada.

---

# Jika Project Belum Terdaftar

Buat:

```text
.claude-sync/project.json
```

dengan struktur yang sudah digunakan sejak Phase 1.

Gunakan generator UUID yang sudah ada.

Jangan membuat format baru.

---

# Claude Folder Mapping

Gunakan utility yang sudah ada.

Jangan membuat implementasi mapping baru.

Jangan membuat reverse mapping.

---

# Metadata Tambahan

Boleh menambahkan:

```json
{
  "registered_at": "<timestamp>"
}
```

jika memang diperlukan.

Jika tidak diperlukan oleh desain saat ini:

abaikan.

Jangan memaksa perubahan schema besar.

---

# Error Handling

Jika dijalankan di folder yang tidak valid:

Tampilkan error yang jelas.

Jangan crash.

Jika metadata tidak bisa ditulis:

Abort.

Tampilkan pesan yang jelas.

---

# Batas Scope

Boleh diubah:

* register command baru
* cli registration
* helper register jika diperlukan
* progress.md

Jangan mengubah:

* discover command
* inspect-project
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

## Test 1 — Fresh Registration

Masuk ke project yang belum memiliki:

```text
.claude-sync/project.json
```

Jalankan:

```bash
claude-sync register
```

Pastikan:

```text
.claude-sync/project.json
```

dibuat.

---

## Test 2 — UUID Stability

Catat:

```text
project_id
```

Jalankan lagi:

```bash
claude-sync register
```

Pastikan UUID tidak berubah.

---

## Test 3 — Existing Registration

Pastikan:

```text
.claude-sync/project.json
```

sudah ada.

Jalankan:

```bash
claude-sync register
```

Pastikan muncul warning.

Tidak ada overwrite.

---

## Test 4 — Invalid Project

Jalankan di folder yang bukan project valid.

Pastikan muncul error yang jelas.

Tidak crash.

---

Setelah implementasi selesai:

STOP.

Tunggu instruksi user:

* lanjut ke Phase 7C
* perbaiki bug
* ulang implementasi
