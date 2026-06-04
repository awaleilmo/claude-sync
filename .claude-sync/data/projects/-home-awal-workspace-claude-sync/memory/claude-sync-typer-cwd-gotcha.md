---
name: claude-sync-typer-cwd-gotcha
description: Typer default Path.cwd() di-eval saat module load; gunakan None + helper untuk default yang dievaluasi saat call-time (penting untuk monkeypatch.chdir di tests)
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b1a65801-9581-4070-b3d2-e494eb5b3997
---

Di Typer, default argumen dievaluasi **sekali saat modul dimuat**, bukan saat command dipanggil. Ini menyebabkan:
- `Path.cwd()` sebagai default → mengunci cwd ke nilai saat startup
- `monkeypatch.chdir(tmp_path)` di pytest tidak akan mengubah nilai default
- Test gagal karena CLI masih menulis ke cwd awal

**Solusi:** Gunakan `Path | None = None` sebagai default + helper:
```python
def _resolve_root(project_root: Path | None) -> Path:
    return project_root if project_root is not None else Path.cwd()
```
Helper ini dipanggil di body command, sehingga `Path.cwd()` dievaluasi saat call-time dan merespons `chdir`.

**Why:** Bug ini muncul di semua command `claude-sync` (init, status, import, export). Test awal gagal karena `tmp_path` digunakan untuk assert tapi CLI menulis ke cwd awal.

**How to apply:** Pola ini digunakan di `src/claude_sync/commands/{init,status,import,export}.py`. Untuk Typer commands yang butuh path relatif terhadap cwd, selalu gunakan pola None + helper.

Related: [[claude-sync-tahap-progress]]
