# Claude Sync v2 — Phase 6B: Encrypt Export

PENTING

Lanjutkan dari Phase 6A.

Semua fitur sebelumnya harus tetap berfungsi.

Kerjakan HANYA Phase 6B.

Setelah selesai STOP.

Jangan lanjut ke Phase 6C.

Jangan mengubah import.

Jangan mengubah status command.

Jangan mengubah doctor command.

Jangan mengubah package format.

Jangan mengubah crypto foundation yang sudah dibuat.

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

Mengaktifkan encryption saat export.

Phase ini hanya mengubah export flow.

Import BELUM mendukung package terenkripsi.

Itu akan dikerjakan pada Phase 6C.

---

# Behaviour Baru

Saat:

```bash
claude-sync export
```

dijalankan:

Flow baru:

```text
Export Project
↓
Build ZIP Package
↓
Minta Password
↓
Encrypt Package
↓
Simpan project.claudepack
↓
Hapus File Sementara
```

---

# Password Prompt

Saat export:

Tampilkan:

```text
Enter Encryption Password:
```

Gunakan input yang tidak menampilkan password di layar.

Jangan menyimpan password ke file.

Jangan menyimpan password ke manifest.

Jangan menyimpan password ke project.json.

---

# Claudepack Baru

Sebelum Phase 6:

```text
project.claudepack
=
ZIP biasa
```

Sesudah Phase 6B:

```text
project.claudepack
=
Encrypted ZIP Payload
```

File tidak boleh bisa dibuka langsung menggunakan ZIP reader.

---

# Crypto

Gunakan utility yang dibuat pada Phase 6A:

```python
encrypt_bytes()
```

Jangan membuat implementasi crypto baru.

Jangan menduplikasi logic encryption.

---

# Manifest

Tambahkan metadata:

```json
{
  "package_version": 2,
  "encrypted": true,
  "algorithm": "AES-256-GCM"
}
```

Jangan menyimpan:

* password
* password hash
* derived key
* salt export session

---

# Error Handling

Jika:

* password kosong
* encrypt gagal
* file tidak bisa ditulis

Abort export.

Tampilkan error yang jelas.

Jangan menghasilkan package setengah jadi.

---

# Temporary Files

Jika menggunakan temporary ZIP:

Pastikan dibersihkan setelah encryption selesai.

Jika terjadi error:

Pastikan temporary file ikut dibersihkan.

---

# Batas Scope

Boleh diubah:

* export command
* exporter
* manifest handling
* progress.md

Jangan mengubah:

* importer
* status command
* doctor command
* path mapping
* project identity
* crypto.py (kecuali bug blocker)

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

## Test 1

Jalankan:

```bash
claude-sync export
```

Masukkan:

```text
test123
```

Pastikan:

```text
.claude-sync/project.claudepack
```

terbentuk.

---

## Test 2

Rename:

```text
project.claudepack
```

menjadi:

```text
project.zip
```

Coba buka.

Pastikan gagal dibuka sebagai ZIP.

---

## Test 3

Periksa:

```text
manifest.json
```

Pastikan:

```json
{
  "encrypted": true,
  "algorithm": "AES-256-GCM"
}
```

tersimpan.

---

## Test 4

Jalankan export kedua.

Gunakan password berbeda.

Pastikan ukuran package tetap masuk akal dan file berhasil dibuat.

---

Setelah implementasi selesai:

STOP.

Tunggu instruksi user:

* lanjut ke Phase 6C
* perbaiki bug
* ulang implementasi
