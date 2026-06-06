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