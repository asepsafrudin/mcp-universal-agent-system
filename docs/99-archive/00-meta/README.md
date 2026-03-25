# 00-meta — Cara Menggunakan Dokumentasi

## Struktur Numerik Prefix

Dokumentasi menggunakan numerik prefix (`00-`, `01-`, dst) untuk:

1. **Urutan Logis**: Membaca dari awal hingga akhir memberikan pemahaman bertahap
2. **Fleksibilitas**: Dua digit (`00-99`) memungkinkan penambahan folder di tengah tanpa rename
3. **Kategori Jelas**: Setiap range memiliki makna:
   - `00-09`: Meta dan getting started
   - `10-89`: Konten utama
   - `90-99`: Archive dan reference

## Cara Membaca

### Untuk Newcomer
```
01-getting-started/ → 02-architecture/ → 03-development/
```

### Untuk Operator
```
01-getting-started/ → 04-operations/ → 06-database/
```

### Untuk Integrator
```
01-getting-started/ → 02-architecture/ → 05-integrations/
```

## Format File

### Nama File
- Gunakan `kebab-case.md` untuk multi-kata
- Hindari spasi dan underscore
- Contoh: `task-system-refactoring.md` ✅ | `task_system_refactoring.md` ❌

### Struktur Dokumen Standar

```markdown
# Judul Dokumen

> One-line summary

---

## Overview

Deskripsi singkat apa dokumen ini tentang.

## Section 1

### Subsection

Content...

## Referensi

- [Link ke dokumen terkait](../other-folder/file.md)

---

*Last Updated: YYYY-MM-DD*
```

## Contributing

1. Letakkan di folder yang paling sesuai
2. Update README.md folder jika menambahkan file penting
3. Update README.md utama jika menambahkan folder baru
4. Gunakan relative links untuk cross-reference

## Cross-Reference

Gunakan relative paths:
```markdown
[Lihat juga](../02-architecture/system-overview.md)
[Database docs](../06-database/README.md)
```
