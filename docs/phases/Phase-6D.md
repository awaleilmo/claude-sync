# Claude Sync v2 — Phase 6D: Legacy Package Compatibility

PENTING

Lanjutkan dari Phase 6C.

Semua fitur sebelumnya harus tetap berfungsi.

Kerjakan HANYA Phase 6D.

Setelah selesai STOP.

Jangan lanjut ke Phase 6E.

Jangan mengubah export.

Jangan mengubah crypto foundation.

Jangan mengubah status command.

Jangan mengubah doctor command.

Jangan mengubah package format.

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

Menjaga kompatibilitas dengan package lama.

Saat ini terdapat dua kemungkinan package:

## Phase 5 Package

```text
ZIP biasa
Tidak terenkripsi
```

## Phase 6 Package

```text
Encrypted ZIP
AES-256-GCM
```

Import harus dapat membaca keduanya.

---

# Behaviour Baru

Saat:

```bash
claude-sync import
```

dijalankan:

Importer harus mendeteksi tipe package.

---

# Encrypted Package

Jika package adalah format baru:

```text
AES-256-GCM
```

Flow:

```text
Read Package
↓
Request Password
↓
Decrypt
↓
Extract
↓
Restore
```

Gunakan flow dari Phase 6C.

---

# Legacy Package

Jika package adalah ZIP biasa:

Flow:

```text
Read Package
↓
Show Warning
↓
Extract
↓
Restore
```

Tidak perlu password.

---

# Warning

Saat package lama terdeteksi:

Tampilkan:

```text
Warning: Unencrypted Package Detected
```

Import tetap dilanjutkan.

Jangan abort.

---

# Detection

Gunakan metadata yang sudah tersedia.

Atau gunakan header package yang dibuat pada Phase 6A.

Jangan melakukan heuristik yang rumit.

Jangan scan seluruh file.

Jangan membuat format migrasi.

---

# Migration

JANGAN:

* mengubah package lama
* mengkonversi package lama
* membuat auto migration
* menulis ulang package lama

Import saja apa adanya.

---

# Error Handling

Jika package:

* bukan ZIP valid
* bukan encrypted package valid

Abort.

Tampilkan pesan yang jelas.

Jangan melakukan restore sebagian.

---

# Restore Flow

Baik package lama maupun baru harus menggunakan restore flow yang sama setelah package berhasil dibuka.

Jangan membuat dua restore engine berbeda.

---

# Batas Scope

Boleh diubah:

* importer
* import command
* helper yang diperlukan untuk package detection
* progress.md

Jangan mengubah:

* exporter
* crypto.py
* status command
* doctor command
* manifest schema
* path mapping
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

* perubahan yang dilakukan
* file yang diubah
* alasan perubahan

Jangan menuliskan hasil testing.

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

## Test 1 — Legacy Package

Gunakan package dari Phase 5.

Jalankan:

```bash
claude-sync import
```

Pastikan:

```text
Warning: Unencrypted Package Detected
```

muncul.

Import tetap berhasil.

---

## Test 2 — Encrypted Package

Gunakan package dari Phase 6B.

Jalankan:

```bash
claude-sync import
```

Masukkan password yang benar.

Pastikan import berhasil.

---

## Test 3 — Wrong Password

Gunakan package terenkripsi.

Masukkan password salah.

Pastikan import gagal.

---

## Test 4 — Invalid Package

Gunakan file acak:

```text
project.claudepack
```

yang bukan ZIP dan bukan encrypted package.

Pastikan import abort.

---

## Test 5 — Compatibility Check

Pastikan:

* package lama masih bisa dipakai
* package baru masih bisa dipakai

tanpa perubahan manual.

---

Setelah implementasi selesai:

STOP.

Tunggu instruksi user:

* lanjut ke Phase 6E
* perbaiki bug
* ulang implementasi
