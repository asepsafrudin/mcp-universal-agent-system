# Korespondensi POSISI Terms Dictionary

Tanggal: 2026-04-09

## Provenance

- Script sumber: `korespondensi-server/src/services/posisi_bridge.py`
- Endpoint validasi: `GET /api/knowledge/posisi/terms`
- Endpoint sumber konteks: `GET /api/knowledge/posisi/unique`
- Tanggal dokumentasi: `2026-04-09`

## Tujuan

- Menyusun kamus awal dari token unik yang muncul pada kolom `POSISI`
- Memisahkan token menjadi kategori agar mudah diberi definisi manual
- Menjadi referensi kerja untuk developer dan agent IDE lain

## Kategori

### 1. Unit / Entitas Organisasi

- `SES`
- `SET`
- `PRC`
- `BU`
- `UM`
- `TU`
- `KEU`
- `PUU`
- `PEIPD`
- `SUPD`
- `SD`
- `BANGDA`
- `DIRJEN`
- `DITJEN`

### 2. Aksi / Status

- `KOREKSI`
- `TTD`
- `SELESAI`
- `DJ`
- `DISPOSISI`
- `UPDATE`
- `POSITION_CHECK`
- `DITERIMA`
- `PROSES`
- `DONE`

### 3. Penanda Tanggal

Token tanggal yang muncul sebagai bagian dari `POSISI`, misalnya:

- `13/3`
- `16/3`
- `24/2`
- `9/1`
- `11/3`
- `17/3`

### 4. Catatan / Keterangan Tambahan

- `ND`
- `PAK BARJO`
- `SISTEM`
- `SIMND`
- `SRIKANDI`
- `POOLING`

## Contoh Mapping Awal

> Ini masih kamus kerja awal. Definisi final sebaiknya diverifikasi manual
> terhadap konteks surat dan sheet sumber.

| Token | Kategori | Arti Awal |
|------|----------|-----------|
| SES | Unit | Sekretariat / Sekretaris |
| PRC | Unit | Perencanaan |
| BU | Unit | Bagian Umum |
| PUU | Unit | Substansi Perundang-Undangan |
| KEU | Unit | Keuangan |
| SUPD | Unit | Sekretariat/Unit SUPD |
| KOREKSI | Aksi | Koreksi / revisi data |
| TTD | Aksi | Tanda tangan / finalisasi |
| SELESAI | Status | Selesai / ditutup |
| DJ | Aksi | Dipakai sebagai penanda disposisi/lanjutan |

## Statistik Awal

Hasil endpoint `terms` menunjukkan token dominan seperti:

- `SES`
- `KOREKSI`
- `TTD`
- `SELESAI`
- `BU`
- `PRC`
- `SUPD`

## Catatan

- Token diekstrak secara heuristik dari string raw `POSISI`.
- Beberapa token perlu interpretasi manual karena bisa bermakna berbeda
  tergantung sheet dan konteks surat.
- Kamus ini adalah referensi awal dan bisa diperluas dari hasil endpoint yang sama.
