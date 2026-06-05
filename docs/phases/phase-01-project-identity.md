# Claude Sync v2 - Phase 1

PENTING

Mode saat ini adalah REFACTOR TERKONTROL.

Jangan langsung mengimplementasikan seluruh roadmap.

Kerjakan HANYA Phase 1.

Setelah selesai STOP.

Jangan lanjut ke Phase 2.

Jangan membuat fitur encryption.

Jangan membuat fitur compression.

Jangan membuat auto mapping.

Jangan membuat migrasi otomatis.

Jangan membuat commit.

---

## Konteks

Hasil testing menunjukkan:

1. Export dan import saat ini sebenarnya bekerja.

2. Session Claude berhasil dipindahkan antar device.

3. Masalah utama adalah project Claude Code terikat pada absolute path.

Contoh:

Linux:

/home/awal/workspace/claude-sync

menjadi:

-home-awal-workspace-claude-sync

Windows:

D:/Project/claude-sync

menjadi:

d--Project-claude-sync

Karena nama folder project berbeda, Claude Code tidak menemukan session.

4. Desain lama berbasis global ~/.claude akan ditinggalkan.

5. Desain baru menggunakan Project-Based Sync.

---

## Tugas

Buat fondasi baru tanpa merusak fitur yang sudah ada.

---

## Wajib Buat

### project.json

Saat:

claude-sync init

buat:

.claude-sync/project.json

format:

{
"project_id": "<uuid4>",
"project_name": "<folder-name>",
"version": 2
}

UUID harus dibuat sekali.

Tidak boleh berubah.

Jika file sudah ada:

jangan overwrite.

---

## Data Model Baru

Buat model terpisah untuk project metadata.

Jangan menggunakan dict mentah.

Gunakan dataclass.

Contoh:

ProjectMetadata

* project_id
* project_name
* version

---

## Status Command

Tambahkan informasi:

Project Name
Project ID
Version

Jika project.json ditemukan.

---

## Doctor Command

Jika command doctor sudah ada:

tambahkan validasi:

* project.json exists
* uuid valid

Jika doctor belum ada:

JANGAN buat sekarang.

---

## Progress Tracking

Buat file:

progress.md

di root project.

Isi:

* perubahan yang dilakukan
* file yang diubah
* alasan perubahan

---

## Plan Tracking

Buat file:

plan.md

Isi:

Roadmap baru:

Phase 1
Project Identity

Phase 2
Project-Based Export

Phase 3
Project-Based Import

Phase 4
Automatic Path Mapping

Phase 5
Compression Package

Phase 6
AES Encryption

Phase 7
Migration Tool

---

## Output Yang Wajib Ditampilkan

1. File yang dibuat
2. File yang diubah
3. Cara testing manual

---

## Testing Manual (User Wajib Melakukan)

1. Buat folder kosong: 
test-project

2. Jalankan:
claude-sync init

3. Pastikan muncul:
.claude-sync/project.json

4. Jalankan:
claude-sync status

5. Pastikan UUID tampil.

6. Jalankan ulang:
claude-sync init

7. Pastikan UUID tidak berubah.

---

Setelah semua langkah selesai:

STOP.

Jangan lanjut ke project-based export.

Jangan lanjut ke import.

Jangan lanjut ke compression.

Jangan lanjut ke encryption.
