# Claude Sync v2 - Phase 5

PENTING

Lanjutkan dari Phase 4.

Semua fitur sebelumnya harus tetap berfungsi.

Kerjakan HANYA Phase 5.

Setelah selesai STOP.

Jangan lanjut ke Phase 6.

Jangan membuat encryption.

Jangan membuat password.

Jangan membuat migrasi project.

---

## Tujuan

Mengubah format export dari:

Folder-Based Export

menjadi:

Package-Based Export

Namun BELUM menggunakan encryption.

---

## Konteks

Saat ini hasil export berbentuk folder:

.claude-sync/

├── project.json
├── manifest.json
└── export/
└── project/

Struktur ini akan diubah.

Tujuan:

* ukuran lebih kecil
* mudah dipindahkan
* lebih mudah masuk Git
* persiapan untuk encryption pada Phase 6

---

## Format Baru

Setelah export:

.claude-sync/

├── project.json
├── manifest.json
└── project.claudepack

---

## Claudepack

Untuk Phase 5:

project.claudepack

adalah:

ZIP biasa

BELUM encrypted.

BELUM password protected.

---

## Export Behaviour Baru

Saat:

claude-sync export

Langkah:

1. export project seperti biasa
2. buat temporary folder
3. copy seluruh hasil export ke temporary folder
4. compress menjadi:

project.claudepack

5. hapus temporary folder

---

## Package Contents

Isi package:

project/

manifest.json

Jangan menyimpan:

project.json

karena project.json adalah identitas lokal project.

---

## Compression Library

Gunakan:

zipfile

dari standard library Python.

Jangan menambah dependency baru.

---

## Import Behaviour Baru

Saat:

claude-sync import

Langkah:

1. validasi package ada
2. extract package ke temporary folder
3. jalankan restore seperti sebelumnya
4. hapus temporary folder

---

## Backward Compatibility

PENTING

Jika menemukan:

.claude-sync/export/

format lama

tetap support.

Jangan memaksa migrasi.

Prioritaskan:

project.claudepack

jika tersedia.

---

## Validation

Saat import:

Jika:

project.claudepack

rusak

abort dengan pesan yang jelas.

Jangan melakukan restore sebagian.

---

## Status Command

Tambahkan:

Package Format:
Folder / Claudepack

Package Size:
...

---

## Doctor Command

Jika doctor tersedia:

Tambahkan:

✓ Package Valid

atau

✗ Package Corrupted

---

## Progress Tracking

Update progress.md

Tambahkan:

* perubahan yang dilakukan
* file yang diubah
* hasil testing

---

## Plan Tracking

Update plan.md

Tandai:

Phase 1 = Completed

Phase 2 = Completed

Phase 3 = Completed

Phase 4 = Completed

Phase 5 = Completed

Phase 6 = Pending

---

## Output Yang Wajib Ditampilkan

1. File baru
2. File yang diubah
3. Ringkasan perubahan
4. Cara testing

---

## Testing Manual (User Wajib Melakukan)

### Test 1

Masuk ke project:

claude-sync

Jalankan:

claude-sync export

---

### Test 2

Periksa:

.claude-sync/

Pastikan terdapat:

project.claudepack

---

### Test 3

Periksa ukuran file.

Pastikan package lebih kecil dibanding folder export.

---

### Test 4

Hapus folder export sementara jika masih ada.

Pastikan package tetap dapat digunakan.

---

### Test 5

Jalankan:

claude-sync import

---

### Test 6

Pastikan restore berhasil dari:

project.claudepack

bukan dari folder export.

---

### Test 7

Buka Claude Code.

Pastikan session tetap dapat ditemukan.

---

Setelah selesai:

STOP.

Jangan membuat encryption.

Jangan membuat password.

Jangan membuat AES.

Jangan membuat key management.

Jangan lanjut ke Phase 6.
