# Knowledge Notes

Folder ini dipakai untuk catatan hasil investigasi, perbaikan, dan mapping
yang ingin mudah dicari ulang oleh developer maupun agent.

## Format yang Disarankan

Sebaiknya setiap file knowledge menyertakan:

- Judul yang jelas
- Tanggal dokumentasi
- Provenance / sumber asal
  - nama script
  - path file
  - endpoint atau command yang dipakai
- Ringkasan masalah atau mapping
- Langkah perbaikan atau hasil akhir
- Catatan operasional penting

## Template

Gunakan file template berikut saat membuat knowledge baru:

- [knowledge_template.md](knowledge_template.md)

## Kamus POSISI

- [korespondensi_posisi_terms_dictionary_2026-04-09.md](korespondensi_posisi_terms_dictionary_2026-04-09.md)
- [korespondensi_posisi_terms_dictionary_2026-04-09.json](korespondensi_posisi_terms_dictionary_2026-04-09.json)
- [korespondensi_posisi_dictionary_minimal_2026-04-09.json](korespondensi_posisi_dictionary_minimal_2026-04-09.json)

## Contoh Provenance

```md
## Provenance
- Script sumber: `korespondensi-server/src/services/posisi_mapping.py`
- Endpoint pemakaian: `GET /api/knowledge/posisi/unique`
- Tanggal dokumentasi: `2026-04-09`
```

## Prinsip

- Knowledge adalah catatan bantu, bukan source of truth utama.
- Kalau ada helper, endpoint, atau script yang berubah, update source code
  terlebih dahulu, lalu sinkronkan knowledge.
- Jika catatan dibuat dari workflow tertentu, sebutkan command/endpoint itu
  agar jejaknya mudah dilacak ulang.
