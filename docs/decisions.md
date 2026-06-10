# Decision Log

## 2026-06-05

**Decision:**
Project menggunakan Typer sebagai framework CLI utama dengan `no_args_is_help=True` dan `add_completion=False`.

**Alternatives:**
- Click (framework底层 Typer pakai)
- Argparse (stdlib, tapi kurang ergonomis)
- Typer + Rich untuk styling output

**Reason:**
Typer memberikan decorator-based registration yang clean, type-hint validation otomatis dari Python, dan integrasi bagus dengan Rich untuk styling terminal output.

**Impact:**
Seluruh 8 subcommand didaftarkan sebagai Typer commands. CLI entry point di `cli.py` menggunakan single `Typer` instance shared oleh semua subcommand.

**Status:**
Accepted

---

## 2026-06-05

**Decision:**
Project identity menggunakan UUID4 yang digenerate sekali saat `init` dan tidak pernah berubah.

**Alternatives:**
- Hash dari project path
- Timestamp-based ID
- User-defined name sebagai ID

**Reason:**
UUID4 memberikan identifier yang unik secara global, stable (tidak berubah saat project dipindahkan), dan tidak bergantung pada path yang bisa berbeda antar device. ID yang stabil diperlukan untuk project-based sync di Phase 2+.

**Impact:**
`project.json` dibuat di `.claude-sync/` dengan field `project_id`. `init` tidak overwrite jika file sudah ada (kecuali `--force` digunakan).

**Status:**
Accepted

---

## 2026-06-05

**Decision:**
Project metadata menggunakan dataclass `ProjectMetadata` (bukan raw dict).

**Alternatives:**
- Plain dict
- Pydantic model
- Simple namespace

**Reason:**
Dataclass memberikan type safety, IDE auto-completion, dan immutable (frozen=True) yang sesuai dengan sifat metadata yang seharusnya tidak berubah setelah dibuat. Lebih ringan dari Pydantic untuk use case ini.

**Impact:**
Semua akses ke project metadata melalui dataclass methods (`to_dict()`, `from_dict()`). Serialisasi ke JSON tetap didukung.

**Status:**
Accepted

---

## 2026-06-05

**Decision:**
Schema version project didefinisikan di dua level: `MANIFEST_VERSION` (1) di `manifest.json` dan `PROJECT_METADATA_VERSION` (2) di `project.json`.

**Alternatives:**
- Satu versi schema untuk semua file
- Tiap file punya versi internal masing-masing tanpa konsistensi cross-file

**Reason:**
`manifest.json` mewakili schema tingkat project-level (folder structure, metadata dasar), sementara `project.json` mewakili schema tingkat project identity. Memisahkan versi memungkinkan migration per-subsistem secara independen. Version 2 menandakan schema baru yang mencakup project identity.

**Impact:**
Future migration tool (Phase 7) dapat menggunakan versi ini untuk mendeteksi old schema dan melakukan migrasi otomatis.

**Status:**
Accepted

---

## 2026-06-05

**Decision:**
Claude Code path dideteksi secara otomatis berdasarkan platform (`platform.system()`) dengan fallback resolver.

**Alternatives:**
- Hardcoded path `~/.claude/` untuk semua platform
- User-defined path via config file
- Multi-path search dengan ranking

**Reason:**
Auto-detection berdasarkan platform memberikan UX yang lebih baik (no-config-required) karena path `.claude/` sudah konsisten di Linux, macOS, dan Windows. Resolver yang pluggable memungkinkan tests untuk override tanpa perlu subclassing.

**Impact:**
Module `claude_locator.py` menjadi single source of truth untuk path resolution. Deteksi WSL dilakukan via `/proc/version` parsing.

**Status:**
Accepted

---

## 2026-06-05

**Decision:**
Export data menggunakan dua strategi: legacy `ClaudeExporter` (mirrors entire `.claude/` subtree) dan `ProjectExporter` (Phase 2, exports per-project folder only).

**Alternatives:**
- Hanya legacy exporter
- Hanya project-based exporter
- Hybrid yang bisa switch berdasarkan config

**Reason:**
Legacy exporter dipertahankan untuk backward-compatibility dengan `import_cmd.py` yang masih membaca dari layout `data/`. `ProjectExporter` dirancang untuk Phase 2+ yang membutuhkan granularitas per-project.

**Impact:**
Constant `EXPORT_SUBDIRS` dan `EXPORT_FILES` di `exporter.py` dire-export untuk backward compatibility. Layout baru menggunakan `export/project/<folder>/` di dalam `.claude-sync/`.

**Status:**
Accepted

---

## 2026-06-05

**Decision:**
Project path-to-folder mapping mengikuti konvensi internal Claude Code: ganti separator dengan `-`, lowercase drive letter, ganti `:` dengan `--`.

**Alternatives:**
- UUID-based folder naming
- User-defined folder name
- Hash-based naming (SHA256)

**Reason:**
Mengikuti konvensi Claude Code menjamin kompatibilitas langsung — folder yang dihasilkan `ProjectExporter` akan cocok dengan folder yang diharapkan Claude Code. Tidak ada kebutuhan enkripsi atau hashing karena nama folder bukan untuk keamanan.

**Impact:**
Function `project_to_claude_folder()` di `project_path.py` menjadi fungsi kunci untuk mapping. Contoh: `/home/user/project` → `-home-user-project`. Inverse mapping (Claude → local) belum diimplementasi (akan ada di Phase 4).

**Status:**
Accepted

---

## 2026-06-05

**Decision:**
Tidak membuat `doctor` command di Phase 1.

**Alternatives:**
- Langsung implement doctor command
- Skip dan add di Phase terpisah

**Reason:**
Doctor command (health check, diagnostic, auto-fix) lebih cocok untuk phase lanjutan setelah foundation (project identity) solid. Prioritas Phase 1 adalah identitas project yang stable.

**Impact:**
Saat ini tidak ada built-in diagnostic command. User harus mengandalkan `status` command untuk memeriksa kondisi project.

**Status:**
Deferred

---

## 2026-06-05

**Decision:**
Data di `.claude-sync/data/` disimpan tanpa enkripsi (plaintext via `shutil.copy2()`).

**Alternatives:**
- Enkripsi end-to-end (AES) di Phase 1
- Enkripsi di phase kemudian
- User-configurable encryption toggle

**Reason:**
Enkripsi adalah fitur keamanan lanjutan yang memerlukan password/key management. ARCHITECTURE.md mencatat ini sebagai known issue kritis yang dijadwalkan untuk Phase 6. Phase 1 berfokus pada foundation.

**Impact:**
Siapa pun yang punya akses ke Git repo bisa membaca semua isi `.claude-sync/data/`. User perlu rely pada enkripsi Git repo (Git-encrypted, LFS, atau repo private) sebagai mitigation.

**Status:**
Accepted (Deferred Implementation — Phase 6)

---

## 2026-06-05

**Decision:**
Tidak ada session validation saat export (session yang sudah tidak valid tetap di-export).

**Alternatives:**
- Validasi session status (active/inactive/expired)
- Filter berdasarkan timestamp
- User-configurable filtering rules

**Reason:**
Session validation memerlukan definisi "valid" yang mungkin berbeda antar kasus penggunaan. Phase 1 berfokus pada copy data apa adanya. Filtering bisa ditambahkan di Phase 2+ jika diperlukan.

**Impact:**
Ukuran export bisa lebih besar dari yang diperlukan jika banyak session tidak valid. Tidak ada risiko kehilangan data karena filtering yang terlalu agresif.

**Status:**
Accepted (Deferred Implementation)

---

## 2026-06-05

**Decision:**
Git sync menggunakan subprocess untuk memanggil Git CLI (`git push`, `git pull`) bukan library Python seperti GitPython.

**Alternatives:**
- GitPython library
- Dulwich (pure Python Git)
- Subprocess ke Git CLI

**Reason:**
Subprocess ke Git CLI lebih reliable karena memanfaatkan Git native behavior, termasuk credential handling, SSH config, dan remote URL resolution. Library Python seringkali tidak mengikuti semua nuansa Git CLI.

**Impact:**
`git_sync.py` menjalankan Git sebagai external process. User perlu sudah mengkonfigurasi Git (remote, credentials) secara terpisah.

**Status:**
Accepted

---

## 2026-06-05

**Decision:**
Version aplikasi diatur di `__init__.py` sebagai `__version__ = "0.1.0"` dan ditampilkan via `--version` flag.

**Alternatives:**
- Read from pyproject.toml at runtime
- Hardcoded constant di module terpisah
- Use setuptools_scm (version from git tags)

**Reason:**
Version di `__init__.py` memberikan single source of truth yang mudah di-update dan kompatibel dengan Typer's `--version` callback pattern. Simpel untuk project dengan size seperti ini.

**Impact:**
Version bumping perlu dilakukan manual saat release. pyproject.toml juga perlu di-update secara sinkron.

**Status:**
Accepted

---

## 2026-06-05

**Decision:**
Sync directory menggunakan nama `.claude-sync/` (hidden folder) di root project.

**Alternatives:**
- `.claude_sync/` (underscore)
- `claude-sync/` (visible folder)
- `.config/claude-sync/` (XDG-style)

**Reason:**
Convention hidden folder (`.` prefix) menjaga directory tidak clutter workspace. Nama `claude-sync` jelas merepresentasikan fungsi directory tanpa ambigu.

**Impact:**
Seluruh metadata project (manifest, project.json, settings) dan exported data berada di dalam folder ini. `.gitignore` perlu di-update untuk memastikan file yang tepat di-track.

**Status:**
Accepted

---

## 2026-06-05

**Decision:**
`init` command bersifat idempotent — aman untuk di-run berulang tanpa merusak data existing.

**Alternatives:**
- Fail jika sudah initialized
- Overwrite semua file setiap run
- Partial update (skip existing, create new)

**Reason:**
Idempotency memudahkan testing dan penggunaan di CI/CD pipeline. Existing `manifest.json` dan `project.json` dipertahankan kecuali `--force` diberikan.

**Impact:**
Run `init` kedua atau ketiga tidak mengubah data. Output CLI menunjukkan status (Created / already exists / Re-created).

**Status:**
Accepted

---

## 2026-06-09

**Decision:**
`project.claudepack` berisi AES-256-GCM encrypted ZIP payload, bukan ZIP biasa.
Password diminta secara interaktif saat export dan tidak pernah disimpan.

**Alternatives:**
- Public-key encryption (RSA/ECC)
- Plain ZIP tanpa enkripsi (sebelum Phase 6A)
- ZIP dengan password bawaan (rentan terhadap known-plaintext)

**Reason:**
Menggunakan `encrypt_bytes()` dari Phase 6A yang sudah menyediakan AEAD
(authenticated encryption) via AES-256-GCM. PBKDF2 dengan 480k iterasi
memberikan key derivation yang kuat. Password tidak disimpan agar tidak
bocor lewat file atau Git history.

**Impact:**
- `project.claudepack` tidak bisa dibuka dengan ZIP reader.
- Manifest mencatat `package_version: 2`, `encrypted: true`, `algorithm: "AES-256-GCM"`.
- Import dari claudepack akan membutuhkan password yang sama (Phase 6C).

**Status:**
Accepted

---

## 2026-06-09

**Decision:**
Phase 6C: Import flow menggunakan `decrypt_bytes()` dari `crypto.py` untuk
mendecrypt `project.claudepack` yang dienkripsi oleh Phase 6B. Password diminta
secara interaktif dan tidak pernah disimpan. Temporary extracted directory
dibersihkan setelah restore.

**Alternatives:**
- Public-key decryption (RSA/ECC) — tidak digunakan karena export juga symmetric
- Manual decryption implementation — duplikasi logic
- Cache password in memory — risiko memory dump

**Reason:**
- `decrypt_bytes()` dari Phase 6A sudah menyediakan authenticated decryption
  yang memvalidasi integritas package.
- PBKDF2 dengan 480k iterasi memberikan key derivation yang konsisten dengan
  export.
- AES-256-GCM AEAD menolak wrong password sebagai corrupt package (bukan
  memberikan pesan error yang berbeda yang bisa bocor informasi).
- Password diminta ulang setiap kali import untuk menghindari caching.
- Temporary directory dibersihkan untuk mencegah bocornya data sensitif
  di filesystem.

**Impact:**
- Import dari encrypted `.claudepack` sekarang berfungsi penuh.
- User harus mengingat password yang digunakan saat export.
- Wrong password menghasilkan error "Failed to decrypt" yang tidak
  membocorkan informasi apakah package atau password yang salah.
- Cleanup otomatis mencegah file temporary tertinggal.

**Status:**
Accepted
