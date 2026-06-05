# Claude Sync v2 — Phase 6C: Decrypt Import

PENTING

Lanjutkan dari Phase 6B.

Semua fitur sebelumnya harus tetap berfungsi.

Kerjakan HANYA Phase 6C.

Setelah selesai STOP.

Jangan lanjut ke Phase 6D.

Jangan mengubah export.

Jangan mengubah status command.

Jangan mengubah doctor command.

Jangan mengubah format package.

Jangan mengubah crypto foundation.

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

Import dapat membaca:

```text
Encrypted project.claudepack
```

yang dibuat oleh Phase 6B.

Phase ini hanya mengubah import flow.

Tidak menyentuh export.

---

# Behaviour Baru

Saat:

```bash
claude-sync import
```

dijalankan:

Flow baru:

```text
Read project.claudepack
↓
Minta Password
↓
Decrypt Package
↓
Extract Temporary Directory
↓
Restore Project
↓
Cleanup Temporary Files
```

---

# Password Prompt

Saat import:

Tampilkan:

```text
Enter Encryption Password:
```

Gunakan input tersembunyi.

Jangan menyimpan password.

Jangan menyimpan hash password.

Jangan menyimpan key.

---

# Crypto

Gunakan utility dari:

```python
crypto.py
```

Gunakan:

```python
decrypt_bytes()
```

Jangan membuat implementasi crypto baru.

Jangan menduplikasi logic decrypt.

---

# Restore Flow

Setelah decrypt berhasil:

```text
Encrypted Payload
↓
ZIP Bytes
↓
Extract Temp Folder
↓
Restore
```

Gunakan restore flow yang sudah ada.

Jangan membuat restore engine baru.

---

# Package Structure

Setelah extract:

```text
temp/
├── project/
└── manifest.json
```

Restore HARUS menggunakan:

```text
temp/project/
```

Bukan:

```text
temp/
```

Jangan membuat:

```text
target/project/
```

nested folder.

---

# Wrong Password

Jika password salah:

Abort.

Tampilkan pesan error yang jelas.

Jangan melakukan restore.

Jangan membuat backup.

Jangan melakukan restore sebagian.

---

# Corrupted Package

Jika package rusak:

Abort.

Tampilkan pesan error yang jelas.

Jangan melakukan restore.

Jangan membuat backup.

Jangan melakukan restore sebagian.

---

# Temporary Files

Jika decrypt berhasil:

hapus seluruh temporary files setelah restore.

Jika decrypt gagal:

hapus seluruh temporary files.

Tidak boleh meninggalkan file sementara.

---

# Batas Scope

Boleh diubah:

* import command
* importer
* helper yang diperlukan untuk decrypt package
* progress.md

Jangan mengubah:

* exporter
* status command
* doctor command
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

## Test 1 — Happy Path

Jalankan:

```bash
claude-sync import
```

Masukkan password yang benar.

Pastikan:

* decrypt berhasil
* restore berhasil
* session dapat ditemukan kembali

---

## Test 2 — Wrong Password

Jalankan:

```bash
claude-sync import
```

Masukkan password salah.

Pastikan:

* muncul error yang jelas
* restore tidak berjalan

---

## Test 3 — Corrupted Package

Rusak sebagian isi:

```text
project.claudepack
```

Jalankan:

```bash
claude-sync import
```

Pastikan:

* muncul error
* restore tidak berjalan

---

## Test 4 — Nested Folder Validation

Setelah restore:

Pastikan target TIDAK menjadi:

```text
target/project/
```

Pastikan isi project langsung berada pada target restore.

---

## Test 5 — Temporary Cleanup

Setelah import selesai atau gagal:

Pastikan tidak ada temporary directory yang tertinggal.

---

Setelah implementasi selesai:

STOP.

Tunggu instruksi user:

* lanjut ke Phase 6D
* perbaiki bug
* ulang implementasi
