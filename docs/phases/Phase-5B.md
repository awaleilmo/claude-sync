# Claude Sync v2 — Phase 5B: Claudepack Import

PENTING

Lanjutkan dari Phase 5A.

Semua fitur sebelumnya harus tetap berfungsi.

Kerjakan HANYA Phase 5B.

Setelah selesai STOP.

Jangan lanjut ke Phase 5C.

Jangan membuat encryption.

Jangan membuat password.

Jangan membuat AES.

Jangan membuat migration.

Jangan mengubah status command.

Jangan mengubah doctor command.

Jangan mengubah format package.

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

Menambahkan dukungan import dari:

```text
.claude-sync/project.claudepack
```

Import lama harus tetap berfungsi.

---

# Prioritas Import

Saat:

```bash
claude-sync import
```

dijalankan:

Urutan prioritas:

1. project.claudepack
2. .claude-sync/export/

Jika package tersedia:

gunakan package.

Jika package tidak tersedia:

fallback ke format lama.

---

# Struktur Package

Package berisi:

```text
project/
manifest.json
```

Saat diextract ke temporary directory:

contoh:

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

Jangan membuat nested folder:

```text
target/project/
```

Target yang diinginkan adalah isi dari:

```text
project/
```

langsung direstore ke project tujuan.

---

# Behaviour Baru

Jika:

```text
project.claudepack
```

ada:

1. Buat temporary directory
2. Extract package
3. Validasi struktur package
4. Restore project
5. Hapus temporary directory

Jika:

```text
project.claudepack
```

tidak ada:

gunakan flow lama:

```text
.claude-sync/export/
```

---

# Validasi Package

Jika ZIP:

* corrupt
* tidak bisa dibuka
* tidak memiliki folder project/

maka:

Abort.

Tampilkan error yang jelas.

JANGAN melakukan restore sebagian.

JANGAN membuat backup baru jika restore belum dimulai.

---

# Backward Compatibility

Format lama:

```text
.claude-sync/export/
```

tetap harus berfungsi.

Jangan memaksa migrasi.

Jangan menghapus support format lama.

---

# Batas Scope

Boleh diubah:

* import command
* importer
* helper yang langsung diperlukan untuk membaca package

Jangan mengubah:

* exporter
* status command
* doctor command
* encryption
* project identity
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

* perubahan yang dilakukan
* file yang diubah
* alasan perubahan

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

Pastikan:

* package diextract
* restore berhasil
* session dapat ditemukan kembali

---

## Test 2 — Package Priority

Pastikan:

```text
.claude-sync/project.claudepack
```

dan

```text
.claude-sync/export/
```

keduanya ada.

Jalankan:

```bash
claude-sync import
```

Pastikan package digunakan terlebih dahulu.

---

## Test 3 — Corrupt Package

Buat package rusak:

```bash
echo test > .claude-sync/project.claudepack
```

Jalankan:

```bash
claude-sync import
```

Pastikan:

* muncul error yang jelas
* restore tidak berjalan

---

## Test 4 — Missing Package

Hapus:

```text
.claude-sync/project.claudepack
```

Jalankan:

```bash
claude-sync import
```

Pastikan fallback ke:

```text
.claude-sync/export/
```

---

## Test 5 — Nested Folder Validation

Setelah restore:

Pastikan target TIDAK menjadi:

```text
target/project/
```

Pastikan isi:

```text
project/
```

langsung berada di target project.

---

Setelah implementasi selesai:

STOP.

Tunggu instruksi user:

* lanjut ke Phase 5C
* perbaiki bug
* ulang implementasi
