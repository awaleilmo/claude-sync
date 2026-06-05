# Claude Sync v2 - Phase 6

PENTING

Lanjutkan dari Phase 5.

Semua fitur sebelumnya harus tetap berfungsi.

Kerjakan HANYA Phase 6.

Setelah selesai STOP.

Jangan lanjut ke Phase 7.

Jangan membuat cloud sync.

Jangan membuat server.

Jangan membuat account system.

Jangan membuat key storage.

---

## Tujuan

Menambahkan encryption pada:

project.claudepack

agar aman disimpan di:

* Git
* GitHub
* GitLab
* OneDrive
* Dropbox
* NAS

tanpa mengekspos session Claude yang mungkin mengandung:

* API Key
* GitHub Token
* Password
* Secret

---

## Prinsip Utama

Password TIDAK BOLEH disimpan.

Password TIDAK BOLEH ditulis ke file.

Password TIDAK BOLEH disimpan di project.json.

Password TIDAK BOLEH disimpan di manifest.json.

User wajib memasukkan password saat:

* export
* import

---

## Library

Gunakan:

cryptography

Jangan menggunakan:

* pyzipper
* zip password
* custom crypto

---

## Format Baru

Export menghasilkan:

.claude-sync/

├── project.json
├── manifest.json
└── project.claudepack

Tetap sama seperti Phase 5.

Namun sekarang isi file:

project.claudepack

sudah terenkripsi.

---

## Encryption Standard

Gunakan:

AES-256

Mode:

AES-GCM

Karena:

* authenticated encryption
* mendeteksi file corrupt
* mendeteksi password salah

---

## Key Derivation

Gunakan:

PBKDF2HMAC

atau

Scrypt

Pilih yang paling sesuai dengan cryptography.

---

## Salt

Salt wajib random.

Salt wajib berbeda setiap export.

Salt disimpan di package.

Salt bukan secret.

---

## Export Flow

Saat:

claude-sync export

Langkah:

1. export project
2. build package sementara
3. minta password

Enter Password:

4. derive key
5. encrypt package
6. simpan:

project.claudepack

7. hapus data sementara

---

## Import Flow

Saat:

claude-sync import

Langkah:

1. baca package
2. minta password

Enter Password:

3. derive key
4. decrypt
5. extract
6. restore

---

## Wrong Password

Jika password salah:

Tampilkan pesan jelas.

Abort.

Jangan melakukan restore sebagian.

---

## Corrupted Package

Jika package rusak:

Abort.

Jangan melakukan restore sebagian.

---

## Manifest

Tambahkan metadata:

{
"package_version": 2,
"encrypted": true,
"algorithm": "AES-256-GCM"
}

Jangan menyimpan:

* password
* hash password
* derived key

---

## Status Command

Tambahkan:

Package Encryption:
Enabled

Algorithm:
AES-256-GCM

---

## Doctor Command

Jika tersedia:

Tambahkan:

✓ Package Encrypted

atau

✗ Package Not Encrypted

---

## Backward Compatibility

Import harus tetap dapat membaca:

Phase 5 package

yang belum terenkripsi.

Tampilkan warning:

Unencrypted Package Detected

tetapi tetap izinkan import.

---

## Progress Tracking

Update progress.md

Tambahkan:

* perubahan yang dilakukan
* file yang diubah
* hasil testing
* dependency baru

---

## Plan Tracking

Update plan.md

Tandai:

Phase 1 = Completed

Phase 2 = Completed

Phase 3 = Completed

Phase 4 = Completed

Phase 5 = Completed

Phase 6 = Completed

Phase 7 = Pending

---

## Output Yang Wajib Ditampilkan

1. File baru
2. File yang diubah
3. Dependency baru
4. Cara testing

---

## Testing Manual (User Wajib Melakukan)

### Test 1

Jalankan:

claude-sync export

---

### Test 2

Masukkan password:

test123

---

### Test 3

Pastikan:

project.claudepack

berhasil dibuat.

---

### Test 4

Pastikan file tidak dapat dibuka sebagai ZIP biasa.

---

### Test 5

Jalankan:

claude-sync import

---

### Test 6

Masukkan password yang benar.

Pastikan restore berhasil.

---

### Test 7

Ulangi import.

Masukkan password yang salah.

Pastikan restore gagal.

---

### Test 8

Buka Claude Code.

Pastikan session masih dapat ditemukan.

---

### Test 9

Push ke GitHub.

Pastikan tidak lagi terkena:

GitHub Push Protection

akibat session Claude yang mengandung token.

---

Setelah selesai:

STOP.

Jangan membuat cloud sync.

Jangan membuat account.

Jangan membuat remote storage.

Jangan lanjut ke Phase 7.
