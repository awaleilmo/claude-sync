# Claude Sync v2 — Phase 6F: Encryption Doctor Validation

PENTING

Lanjutkan dari Phase 6E.

Semua fitur sebelumnya harus tetap berfungsi.

Kerjakan HANYA Phase 6F.

Setelah selesai STOP.

Jangan lanjut ke Phase 7.

Jangan mengubah export.

Jangan mengubah import.

Jangan mengubah crypto foundation.

Jangan mengubah status command.

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

Menambahkan validasi encryption ke:

```bash
claude-sync doctor
```

Phase ini hanya mengubah doctor reporting.

Tidak mengubah behaviour export/import.

---

# Doctor Checks Baru

Tambahkan pemeriksaan:

```text
Package Encrypted
Package Not Encrypted
Package Metadata Valid
Package Metadata Invalid
```

---

# Contoh Output

## Package Encrypted

```text
✓ Package Found
✓ Package Metadata Valid
✓ Package Encrypted
✓ AES-256-GCM
```

---

## Legacy Package

```text
✓ Package Found
✓ Package Metadata Valid
⚠ Package Not Encrypted
```

---

## Package Corrupted

```text
✓ Package Found
✗ Package Metadata Invalid
```

---

## Package Tidak Ada

```text
⚠ Package Not Found
```

---

# Validation Rules

## Package Found

Periksa:

```text
.claude-sync/project.claudepack
```

ada atau tidak.

---

## Package Metadata Valid

Periksa metadata yang tersedia.

Pastikan:

```text
package_version
encrypted
algorithm
```

konsisten.

---

## Package Encrypted

Jika metadata menunjukkan:

```json
{
  "encrypted": true,
  "algorithm": "AES-256-GCM"
}
```

maka tampilkan:

```text
✓ Package Encrypted
✓ AES-256-GCM
```

---

## Package Not Encrypted

Jika package legacy:

```json
{
  "encrypted": false
}
```

atau metadata lama tidak memiliki field encryption.

Tampilkan:

```text
⚠ Package Not Encrypted
```

---

# Performance

Doctor command tidak boleh:

* melakukan decrypt package
* melakukan import
* melakukan restore
* meminta password

Doctor hanya melakukan validasi metadata.

---

# Jika Doctor Command Belum Ada

JANGAN membuat doctor command baru.

Kerjakan phase ini hanya jika doctor command memang sudah tersedia.

---

# Batas Scope

Boleh diubah:

* doctor command
* helper doctor yang diperlukan
* progress.md
* plan.md

Jangan mengubah:

* exporter
* importer
* crypto.py
* status command
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

# Plan Tracking

Update:

```text
plan.md
```

Tandai:

```text
Phase 6 = Completed
Phase 7 = Pending
```

Jangan mengubah roadmap phase lain.

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

## Test 1 — Encrypted Package

Pastikan package terenkripsi tersedia.

Jalankan:

```bash
claude-sync doctor
```

Pastikan tampil:

```text
✓ Package Encrypted
✓ AES-256-GCM
```

---

## Test 2 — Legacy Package

Gunakan package dari Phase 5.

Jalankan:

```bash
claude-sync doctor
```

Pastikan tampil:

```text
⚠ Package Not Encrypted
```

---

## Test 3 — Corrupted Metadata

Rusak metadata package.

Jalankan:

```bash
claude-sync doctor
```

Pastikan tampil:

```text
✗ Package Metadata Invalid
```

---

## Test 4 — Missing Package

Rename:

```text
project.claudepack
```

menjadi:

```text
project.claudepack.bak
```

Jalankan:

```bash
claude-sync doctor
```

Pastikan tampil:

```text
⚠ Package Not Found
```

---

Setelah implementasi selesai:

STOP.

Tunggu instruksi user:

* lanjut ke Phase 7A
* perbaiki bug
* ulang implementasi
