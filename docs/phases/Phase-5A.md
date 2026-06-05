# Claude Sync v2 — Phase 5A: Claudepack Export

PENTING

Lanjutkan dari Phase 4.

Semua fitur sebelumnya harus tetap berfungsi.

Kerjakan HANYA Phase 5A.

Setelah selesai STOP.

Jangan lanjut ke Phase 5B.

Jangan membuat import dari claudepack.

Jangan membuat encryption.

Jangan membuat password.

Jangan membuat AES.

Jangan membuat migration.

Jangan mengubah status command.

Jangan mengubah doctor command.

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
* Menjalankan tool untuk validasi hasil implementasi

User akan melakukan testing sendiri.

Jika implementasi selesai:

STOP.

Tunggu hasil testing dari user.

---

# Tujuan

Mengubah format export dari folder menjadi package ZIP.

Format package baru:

project.claudepack

Ekstensi `.claudepack` hanyalah ZIP biasa.

Jangan tambahkan encryption.

Jangan tambahkan password.

Jangan tambahkan dependency baru.

Gunakan hanya:

Python Standard Library

```python
zipfile
```

---

# Behaviour Baru

Saat:

```bash
claude-sync export
```

dijalankan:

1. Jalankan export project seperti biasa
2. Buat temporary directory
3. Salin hasil export ke temporary directory
4. Buat ZIP package
5. Simpan sebagai:

```text
.claude-sync/project.claudepack
```

6. Hapus temporary directory

---

# Struktur Setelah Export

```text
.claude-sync/
├── project.json
├── manifest.json
└── project.claudepack
```

---

# Isi Package

Package harus berisi:

```text
project/
manifest.json
```

---

# Larangan

JANGAN memasukkan:

```text
project.json
```

ke dalam package.

JANGAN mengubah:

* import
* importer
* restore flow
* status command
* doctor command
* encryption logic

JANGAN melakukan refactor di luar kebutuhan export package.

---

# Backward Compatibility

Export folder lama boleh tetap ada sementara.

Jangan menghapus behaviour lama kecuali memang diperlukan oleh implementasi package baru.

Fokus phase ini hanya:

Membuat `project.claudepack`.

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

Jangan tampilkan hasil test.

Jangan menjalankan test.

---

# Testing Manual (User Wajib Melakukan)

## Test 1

Jalankan:

```bash
claude-sync export
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

Buka ZIP.

Pastikan isi:

```text
project/
manifest.json
```

---

## Test 3

Pastikan:

```text
project.json
```

tidak ada di dalam ZIP.

---

## Test 4

Bandingkan ukuran:

```text
.claude-sync/export/
```

dan

```text
project.claudepack
```

Pastikan package berhasil dibuat.

---

Setelah implementasi selesai:

STOP.

Tunggu instruksi user:

* lanjut ke Phase 5B
* perbaiki bug
* ulang implementasi
