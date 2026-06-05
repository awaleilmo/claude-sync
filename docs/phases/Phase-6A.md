# Claude Sync v2 — Phase 6A: Crypto Foundation

PENTING

Lanjutkan dari Phase 5C.

Semua fitur sebelumnya harus tetap berfungsi.

Kerjakan HANYA Phase 6A.

Setelah selesai STOP.

Jangan lanjut ke Phase 6B.

Jangan mengubah export.

Jangan mengubah import.

Jangan mengubah status command.

Jangan mengubah doctor command.

Jangan mengubah manifest.

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

Membuat fondasi encryption yang akan digunakan pada phase berikutnya.

Phase ini BELUM mengaktifkan encryption pada export/import.

Phase ini hanya membuat utility crypto yang reusable.

---

# Dependency

Tambahkan dependency:

```text
cryptography
```

Gunakan library resmi:

```python
cryptography
```

Jangan menggunakan:

* pyzipper
* custom crypto
* openssl subprocess
* library crypto lain

---

# Standar Crypto

Tetapkan keputusan berikut:

Algorithm:
AES-256-GCM

KDF:
PBKDF2HMAC

Hash:
SHA256

Salt:
16 byte random

Nonce:
12 byte random

Jangan membuat opsi konfigurasi lain.

Jangan menambahkan pilihan Scrypt.

---

# File Baru

Buat:

```text
src/claude_sync/utils/crypto.py
```

---

# Fungsi Yang Wajib Ada

## derive_key()

Input:

```python
password: str
salt: bytes
```

Output:

```python
bytes
```

Gunakan:

PBKDF2HMAC + SHA256

---

## encrypt_bytes()

Input:

```python
data: bytes
password: str
```

Output:

```python
bytes
```

Flow:

1. Generate salt random
2. Generate nonce random
3. Derive key
4. Encrypt menggunakan AES-GCM
5. Return payload gabungan

Payload format:

```text
MAGIC
VERSION
SALT
NONCE
CIPHERTEXT
```

---

## decrypt_bytes()

Input:

```python
payload: bytes
password: str
```

Output:

```python
bytes
```

Flow:

1. Parse payload
2. Ambil salt
3. Ambil nonce
4. Derive key
5. Decrypt
6. Return plaintext

---

# Error Handling

Jika:

* password salah
* payload rusak
* payload tidak valid

Maka:

Raise exception yang jelas.

Jangan return None.

Jangan swallow error.

---

# Batas Scope

Boleh diubah:

* pyproject.toml
* crypto.py
* progress.md

Jangan mengubah:

* exporter
* importer
* manifest
* status command
* doctor command
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

* file baru
* dependency baru
* perubahan yang dilakukan
* alasan perubahan

Jangan menuliskan hasil testing.

---

# Output Yang Wajib Ditampilkan

1. File baru
2. File yang diubah
3. Dependency baru
4. Ringkasan perubahan
5. Checklist testing manual

Jangan menjalankan test.

Jangan menampilkan hasil test.

---

# Testing Manual (User Wajib Melakukan)

## Test 1

Buka Python REPL.

Import:

```python
from claude_sync.utils.crypto import encrypt_bytes, decrypt_bytes
```

---

## Test 2

Encrypt:

```python
data = b"hello world"
payload = encrypt_bytes(data, "test123")
```

Pastikan payload terbentuk.

---

## Test 3

Decrypt:

```python
result = decrypt_bytes(payload, "test123")
```

Pastikan:

```python
b"hello world"
```

dikembalikan.

---

## Test 4

Decrypt dengan password salah:

```python
decrypt_bytes(payload, "wrong-password")
```

Pastikan exception muncul.

---

## Test 5

Corrupt payload:

Ubah beberapa byte.

Pastikan exception muncul.

---

Setelah implementasi selesai:

STOP.

Tunggu instruksi user:

* lanjut ke Phase 6B
* perbaiki bug
* ulang implementasi
