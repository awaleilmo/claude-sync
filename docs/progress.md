# Progress - Phase 4: Automatic Path Mapping

## Tanggal
2026-06-05

## Perubahan yang Dilakukan

### Tujuan Phase 4

Menyelesaikan masalah path Linux ↔ Windows. Nama folder project
Claude Code dihitung dari absolute path. Saat berpindah device,
absolute path berbeda (mis. `/home/awal/workspace/claude-sync` vs
`D:/Project/claude-sync`) sehingga nama folder hasil transformasi
juga berbeda (mis. `-home-awal-workspace-claude-sync` vs
`d--Project-claude-sync`). Claude Code hanya mengenali session
berdasarkan nama folder hasil transformasi, sehingga cross-device
restore sebelumnya tidak selalu dapat dipakai.

Phase 4 menambahkan:

1. Pencatatan nama folder Claude di mesin sumber saat `export`.
2. Perbandingan dengan nama folder Claude di mesin penerima saat `import`.
3. Restore selalu menggunakan nama folder hasil transformasi dari
   path mesin saat ini (sudah dilakukan di Phase 3 — diverifikasi
   ulang tetap berlaku).
4. Tampilan Source vs Current Claude Folder pada `status`.
5. Pemeriksaan `status --check-mapping` yang exit 0 saat cocok,
   exit 1 saat berbeda.
6. Validasi warning (bukan abort) jika nama folder tidak cocok.

### File yang Diubah

1. `src/claude_sync/utils/config.py`
   - Naikkan `MANIFEST_VERSION` dari 1 ke 2. Field baru
     `source_project_path` dan `source_claude_project_folder`
     hanya akan tercatat pada manifest versi 2 ke atas.

2. `src/claude_sync/commands/export.py`
   - Setelah export berhasil, tulis dua field baru ke manifest:
     - `source_project_path` — path absolut mesin sumber
     - `source_claude_project_folder` — nama folder Claude hasil
       transformasi dari path mesin sumber
   - Tambah import `get_manifest_path`, `read_manifest`,
     `write_manifest` dari `utils.config`.

3. `src/claude_sync/commands/status.py`
   - Tambah opsi `--check-mapping` untuk menjalankan mapping check
     dan keluar dengan kode 0/1.
   - Tambah fungsi `_run_mapping_check()` yang menampilkan
     Source vs Current folder dan verdict `✓ Mapping Valid` /
     `⚠ Source and Current Mapping Differ`.
   - Pada output `status` reguler, tampilkan dua baris baru:
     `Current Claude Folder` dan `Source Claude Folder`. Jika
     `source_claude_project_folder` belum tercatat, tampilkan
     "not recorded (run 'claude-sync export')".
   - Tambah import `get_manifest_path`, `read_manifest` dari
     `utils.config`.

4. `src/claude_sync/commands/import_cmd.py`
   - Tambah validasi warning (bukan abort) saat `import`:
     - Bandingkan `project_name` dari `project.json` dengan nama
       folder hasil transformasi dari path mesin saat ini. Jika
       berbeda, tampilkan
       `⚠ Mapping Mismatch: project.json says "X", current folder is "Y"`
       lalu lanjutkan import.
     - Bandingkan `source_claude_project_folder` dari manifest
       dengan nama folder hasil transformasi dari path mesin saat
       ini. Jika berbeda, tampilkan
       `⚠ Source folder "X" differs from current folder "Y"`
       lalu lanjutkan import.
   - Tambahkan `read_manifest` ke import dari `utils.config`.
   - Module docstring diperbarui untuk mendokumentasikan Phase 4.

5. `tests/test_import_command.py`
   - Tambah 3 test cases Phase 4:
     - `test_import_warns_on_project_name_mismatch_but_continues`
     - `test_import_warns_on_source_manifest_mismatch_but_continues`
     - `test_import_silent_when_mapping_matches`

### File yang Tidak Diubah

- `src/claude_sync/utils/project_path.py` — sudah berisi
  `project_to_claude_folder()` dan `locate_claude_project()`
  yang merupakan inti dari path mapping. Tidak perlu diubah.
- `src/claude_sync/utils/project_identity.py` — `ProjectMetadata`
  sudah memiliki field yang cukup; manifest menyimpan field
  mapping tambahan secara terpisah.

## Alasan Perubahan

- Cross-device restore mengharuskan restore menggunakan nama
  folder hasil transformasi path mesin saat ini, bukan nama
  folder dari mesin sumber.
- Manifest adalah tempat yang tepat untuk menyimpan identitas
  mesin sumber karena ia adalah metadata persisten yang
  didorong ke Git.
- `status --check-mapping` menyediakan cara terprogram untuk
  verifikasi cepat tanpa menjalankan `import`, yang akan
  melakukan restore.

## Testing

- Semua 92 test pass (89 existing + 3 baru Phase 4).
- Test Phase 3 (project-based import) tetap lulus.
- Test Phase 4 baru memverifikasi:
  - Warning tetap dicetak saat `project_name` di `project.json`
    tidak cocok dengan folder hasil transformasi, dan import
    tetap berjalan sampai selesai.
  - Warning tetap dicetak saat `source_claude_project_folder` di
    manifest tidak cocok dengan folder saat ini.
  - Tidak ada warning saat `project_name` dan `source_*` cocok.

## Status

- [x] `MANIFEST_VERSION` dinaikkan ke 2
- [x] Export menulis `source_project_path` dan
      `source_claude_project_folder` ke manifest
- [x] Status menampilkan `Source Claude Folder` dan
      `Current Claude Folder`
- [x] `status --check-mapping` memberikan verdict dan exit code
- [x] Import menampilkan warning saat mapping tidak cocok
      tanpa membatalkan restore
- [x] Semua 92 test pass
- [x] Dokumentasi progress dan plan diperbarui

## STOP — Phase 5A selesai

Phase 5B (Compression), Phase 6 (Encryption), dan Phase 7
(Migration) bukan bagian dari pekerjaan ini dan sengaja tidak
dimulai.

---

# Progress - Phase 5A: Claudepack Export

## Tanggal
2026-06-06

## Perubahan yang Dilakukan

### Tujuan Phase 5A

Mengubah format export dari folder menjadi package ZIP tunggal
(`project.claudepack`). File ZIP adalah standar zip tanpa enkripsi
dan tanpa password. Isi ZIP hanya `project/` dan `manifest.json`.
`project.json` TIDAK termasuk dalam ZIP.

### File yang Diubah

1. `src/claude_sync/utils/exporter.py`
   - Tambah field `claudepack_path: Path | None = None` ke
     `ProjectExportReport`.
   - Tambah fungsi `build_claudepack(project_root, source_folder,
     manifest_path)`:
     - Buat `tempfile.TemporaryDirectory()` untuk staging.
     - Salin source export folder sebagai `project/` di staging.
     - Salin `manifest.json` ke staging.
     - Buat ZIP dengan `zipfile.ZIP_DEFLATED`.
     - Hapus staging dir (context manager).
     - Kembalikan Path ke `.claudepack`.
   - Tambah fungsi `_copy_tree(src, dst)` sebagai helper copy
     rekursif ringan.
   - Panggil `build_claudepack()` di akhir `ProjectExporter.export()`.
   - Tambah `import os` di import section.

2. `src/claude_sync/commands/export.py`
   - Setelah export summary, tampilkan path `project.claudepack`
     jika `report.claudepack_path` tidak None.

### File yang Tidak Diubah
- `commands/import_cmd.py`, `utils/importer.py` — tidak ada
  logic import dari claudepack (larangan Phase 5A).
- `commands/status.py`, `push.py`, `pull.py`, `trace.py` —
  tidak disentuh.
- `utils/config.py`, `utils/project_path.py` — tidak diubah.
- Semua file `tests/` — mode IMPLEMENTATION ONLY.

## Alasan Perubahan
- Phase 5A membuat export lebih portabel dengan format ZIP.
- Folder export lama tetap ada (backward compatibility).
- Tidak ada dependency baru, hanya `zipfile` dari standard library.

## Status
- [x] `build_claudepack()` helper di `exporter.py`
- [x] Field `claudepack_path` di `ProjectExportReport`
- [x] Panggil `build_claudepack()` di akhir `ProjectExporter.export()`
- [x] Output console menampilkan lokasi claudepack
- [x] Folder export lama tetap ada
- [x] Dokumentasi progress dan plan diperbarui

## STOP — Phase 5A selesai

Phase 5B (Compression), Phase 6 (Encryption), dan Phase 7
(Migration) bukan bagian dari pekerjaan ini dan sengaja tidak
dimulai.

---

# Progress - Phase 5B: Claudepack Import

## Tanggal
2026-06-06

## Perubahan yang Dilakukan

### Tujuan Phase 5B

Menambahkan dukungan import dari `project.claudepack` dengan
prioritas di atas format folder lama.

### File yang Diubah

1. `src/claude_sync/utils/importer.py`
   - Tambah property `claudepack_path` di `ProjectImporter`.
   - Tambah method `has_claudepack()` — validasi ZIP via `testzip()`.
   - Tambah method `extract_claudepack()` — extract ke `.claude-sync/.extracted/`,
     raise `ValueError` jika corrupt.
   - Tambah method `_find_claudepack_source()` — prioritas claudepack > folder.
   - Update `import_data()` — gunakan `actual_source = source / "project"`
     saat `source_type == "claudepack"` agar hanya isi `project/`
     yang di-restore, bukan seluruh extracted dir.

2. `src/claude_sync/commands/import_cmd.py`
   - Cek `project.claudepack` sebelum folder export.
   - Validasi ZIP sebelum restore dimulai.
   - Fallback ke `.claude-sync/export/` jika claudepack tidak ada.
   - Tampilkan label source type di output.

### File yang Tidak Diubah
- `utils/exporter.py`, `commands/export.py` — tidak disentuh.
- `commands/status.py` — tidak disentuh.

## Status
- [x] Import dari `project.claudepack` berfungsi
- [x] Prioritas claudepack > folder export
- [x] Fallback ke format lama jika claudepack tidak ada
- [x] Validasi corrupt ZIP dengan error yang jelas
- [x] Restore hanya dari `project/` subdirectory (bukan root extracted)
- [x] 9/9 test importer pass
- [x] Dokumentasi progress diperbarui

## STOP — Phase 5B selesai

Phase 5C (Status/Doctor), Phase 6 (Encryption), dan Phase 7
(Migration) bukan bagian dari pekerjaan ini.

---

# Progress - Phase 5C: Package Status & Tracking

## Tanggal
2026-06-06

## Perubahan yang Dilakukan

### Tujuan Phase 5C

Menambahkan informasi package ke `status` command.

### File yang Diubah

1. `src/claude_sync/commands/status.py`
   - Tambah section "Package Format" setelah Source Claude Folder.
   - Cek keberadaan `project.claudepack` di `.claude-sync/`.
   - Jika ada: tampilkan `Claudepack`, `Yes`, dan ukuran file.
   - Jika tidak ada: tampilkan `Folder`, `No`, `N/A`.
   - Format ukuran: MB jika >= 1MB, KB jika < 1MB.

### File yang Tidak Diubah
- `commands/export.py`, `utils/exporter.py` — tidak disentuh.
- `commands/import_cmd.py`, `utils/importer.py` — tidak disentuh.
- Doctor command — tidak ada (belum ada di codebase).
- `utils/config.py`, `utils/project_path.py` — tidak diubah.

## Alasan Perubahan
- User perlu tahu format package yang tersedia sebelum export/import.
- Package size membantu estimasi transfer time dan storage.

## Status
- [x] Package format info di `status` command
- [x] Tampilkan Claudepack/Folder berdasarkan keberadaan `project.claudepack`
- [x] Tampilkan Package Available (Yes/No)
- [x] Tampilkan Package Size dengan format manusia-membaca
- [x] Dokumentasi progress dan plan diperbarui

## STOP — Phase 5C selesai

Phase 6 (Encryption), Phase 7 (Migration) bukan bagian dari pekerjaan ini.

---

# Progress - Phase 6A: Crypto Foundation

## Tanggal
2026-06-06

## Perubahan yang Dilakukan

### Tujuan Phase 6A

Membuat fondasi encryption yang akan digunakan pada phase berikutnya.
Phase ini BELUM mengaktifkan encryption pada export/import.

### File Baru

1. `src/claude_sync/utils/crypto.py`
   - `derive_key(password, salt)` — PBKDF2HMAC + SHA256, 32-byte key, 480k iter
   - `encrypt_bytes(data, password)` — AES-256-GCM, payload: MAGIC+VERSION+SALT+NONCE+CIPHERTEXT
   - `decrypt_bytes(payload, password)` — parse payload, validate magic/version, decrypt
   - Konstanta: MAGIC=`CSYN`, VERSION=1, SALT=16 byte, NONCE=12 byte, KDF=480k iter

### File yang Diubah

1. `pyproject.toml`
   - Tambah `cryptography>=42.0.0` ke dependencies

### File yang Tidak Diubah
- `commands/export.py`, `utils/exporter.py` — tidak disentuh.
- `commands/import_cmd.py`, `utils/importer.py` — tidak disentuh.
- `commands/status.py` — tidak disentuh.
- `utils/config.py` — tidak disentuh.

## Alasan Perubahan
- Phase 6+ membutuhkan fondasi crypto yang konsisten.
- AES-256-GCM menyediakan confidentiality + integrity (authenticated encryption).
- PBKDF2HMAC dengan 480k iter sesuai rekomendasi NIST untuk key derivation.

## Status
- [x] `crypto.py` utility dengan derive_key, encrypt_bytes, decrypt_bytes
- [x] Payload format: MAGIC + VERSION + SALT + NONCE + CIPHERTEXT
- [x] `cryptography>=42.0.0` ditambahkan ke dependencies
- [x] Dokumentasi progress dan plan diperbarui

---

# Progress - Phase 6B: Encrypt Export

## Tanggal
2026-06-09

## Perubahan yang Dilakukan

### Tujuan Phase 6B

Mengaktifkan encryption pada export flow. Setelah Phase 6B,
`project.claudepack` berisi AES-256-GCM encrypted ZIP payload,
bukan ZIP biasa. Password diminta secara interaktif saat export.

### File yang Diubah

1. **`src/claude_sync/utils/exporter.py`**
   - Tambah `from claude_sync.utils.crypto import encrypt_bytes` di import.
   - Tambah parameter `password: str | None = None` ke `ProjectExporter.__init__`.
   - Simpan `self.password` untuk digunakan saat build claudepack.
   - Pass `password=self.password` ke `build_claudepack()`.
   - Tambah parameter `password: str | None = None` ke `build_claudepack()`.
   - Ubah implementasi: ZIP dibuild di temp file, lalu jika `password`
     disediakan: baca ZIP bytes, encrypt dengan `encrypt_bytes()`,
     tulis encrypted payload ke `project.claudepack`.
   - Jika password tidak disediakan: fallback ke plain ZIP (legacy).
   - Temp directory auto-cleanup via context manager.

2. **`src/claude_sync/commands/export.py`**
   - Tambah `import getpass` di import section.
   - Tambah password prompt menggunakan `getpass.getpass()` sebelum
     membuat `ProjectExporter`.
   - Validasi password tidak kosong — abort jika kosong.
   - Pass `password=password` ke `ProjectExporter`.
   - Tambah metadata encryption ke manifest setelah export sukses:
     - `package_version: 2`
     - `encrypted: True`
     - `algorithm: "AES-256-GCM"`

3. **`tests/test_export_command.py`**
   - Tambah `input="test123\n"` ke semua panggilan `runner.invoke(app, ["export"])`
     untuk menyediakan password via CliRunner stdin.

### File yang Tidak Diubah
- `src/claude_sync/utils/crypto.py` — tetap sebagai fondasi crypto (tidak diubah).
- `src/claude_sync/utils/importer.py` — import belum mendukung encrypted package.
- `src/claude_sync/commands/import_cmd.py` — import belum mendukung encrypted package.
- `src/claude_sync/commands/status.py` — tidak disentuh.
- `src/claude_sync/utils/config.py` — tidak disentuh.

## Alasan Perubahan
- Phase 6A menyediakan fondasi crypto (`encrypt_bytes`); Phase 6B
  mengaktifkannya pada export flow.
- Password diminta secara interaktif untuk keamanan — tidak pernah
  disimpan ke file, manifest, atau project.json.
- AES-256-GCM menyediakan authenticated encryption yang mencegah
  package dibuka sebagai ZIP biasa.

## Status
- [x] Password prompt saat `claude-sync export`
- [x] Validasi password tidak kosong
- [x] Password tidak disimpan ke file/manifest/project.json
- [x] ZIP dibuild di temp directory, dienkripsi, temporary dibersihkan
- [x] `project.claudepack` berisi encrypted payload (AES-256-GCM)
- [x] Manifest mencatat `package_version: 2`, `encrypted: true`,
      `algorithm: "AES-256-GCM"`
- [x] Error handling: password kosong, encrypt gagal, file write gagal
      menyebabkan abort tanpa partial package
- [x] Dokumentasi progress dan plan diperbarui

## Phase 6C: Decrypt Import

### Tanggal
2026-06-09

### Perubahan yang Dilakukan

#### Tujuan Phase 6C
Mengaktifkan decryption pada import flow. Setelah Phase 6C, `project.claudepack`
yang dienkripsi oleh Phase 6B dapat diimpor kembali dengan password yang sama.

#### File yang Diubah

1. **`src/claude_sync/utils/crypto.py`**
   - Tidak diubah — `decrypt_bytes()` dari Phase 6A digunakan untuk decryption.

2. **`src/claude_sync/utils/importer.py`**
   - Import `decrypt_bytes` dari `crypto.py`.
   - Tambah parameter `password: str | None = None` ke `ProjectImporter.__init__`.
   - Simpan `self.password` untuk digunakan saat extract claudepack.
   - Tambah method `_is_encrypted_claudepack()` — cek apakah package dienkripsi
     (bukan plain ZIP).
   - Tambah method `_extract_plain_zip(extracted_dir, password)` — extract ZIP,
     optionally decrypting if encrypted.
   - Tambah parameter `password: str | None = None` ke `extract_claudepack()`.
   - Panggil `_extract_plain_zip()` yang handles decryption.
   - Tambah cleanup extracted directory setelah restore.
   - Update `_find_claudepack_source()` — pass `self.password` ke `extract_claudepack()`.

3. **`src/claude_sync/commands/import_cmd.py`**
   - Tambah `import getpass` di import section.
   - Tambah password prompt menggunakan `getpass.getpass()` sebelum membuat `ProjectImporter`.
   - Validasi password tidak kosong — abort jika kosong.
   - Pass `password=password` ke `ProjectImporter`.
   - Password hanya diminta jika `.claudepack` ada.

### File yang Tidak Diubah
- `src/claude_sync/utils/exporter.py`, `commands/export.py` — tidak disentuh.
- `src/claude_sync/commands/status.py`, `push.py`, `pull.py`, `trace.py` — tidak disentuh.
- `src/claude_sync/utils/config.py`, `utils/project_path.py` — tidak diubah.

### Alasan Perubahan
- Phase 6B mengenkripsi `project.claudepack` dengan AES-256-GCM.
- Phase 6C mengaktifkan decryption pada import flow.
- Password diminta secara interaktif untuk keamanan — tidak pernah disimpan ke file.
- AES-256-GCM authenticated decryption memvalidasi integritas package.

### Crypto Flow
```
Encrypted Payload (project.claudepack)
          ↓
    decrypt_bytes(password)
          ↓
    ZIP Bytes
          ↓
   Extract Zip
          ↓
   temp/project/
          ↓
    Restore to Claude
          ↓
   Cleanup temp
```

### Status Implementation
- [x] `decrypt_bytes()` dari `crypto.py` digunakan
- [x] Password prompt saat `claude-sync import` (jika .claudepack ada)
- [x] Validasi password tidak kosong
- [x] Password tidak disimpan ke file/manifest/project.json
- [x] Encrypted .claudepack didecrypt sebelum extract
- [x] Temporary directory dibersihkan setelah restore
- [x] Error handling: wrong password, corrupt package → abort dengan warning

### Testing Checklist
1. Import dari encrypted .claudepack dengan password yang benar:
   * Decrypt berhasil
   * Restore berhasil
   * Session dapat ditemukan kembali
2. Import dari encrypted .claudepack dengan password salah:
   * Muncul error yang jelas ("Wrong password or corrupted package")
   * Restore tidak berjalan
3. Import from corrupted encrypted .claudepack:
   * Muncul error
   * Restore tidak berjalan
4. Import dari legacy folder export (tanpa .claudepack):
   * Tidak ada password prompt
   * Import berjalan normal
5. Temporary cleanup:
   * Setelah import selesai atau gagal, `/.claude-sync/.extracted/` tidak ada

---

## STOP — Phase 6C selesai

Phase 6D, Phase 6E, Phase 6F bukan bagian dari pekerjaan ini dan sengaja tidak
dimulai.

Tunggu hasil testing dari user.

Jangan lanjut ke Phase 6D.