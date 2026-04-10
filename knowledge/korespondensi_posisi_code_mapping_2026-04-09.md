# Korespondensi POSISI Code Mapping

Dokumen ini mencatat mapping kode unit yang dipakai untuk membaca kolom `POSISI`
di workflow korespondensi PUU.

## Provenance

- Script sumber: `korespondensi-server/src/services/posisi_mapping.py`
- Endpoint pemakaian: `GET /api/internal/{unique_id}/timeline`
- Endpoint bridge: `GET /api/knowledge/posisi/unique`
- Tanggal dokumentasi: `2026-04-09`

## Tujuan

- Membuat teks `POSISI` lebih mudah dibaca saat tampil di UI timeline
- Menjaga data mentah tetap tersedia untuk verifikasi
- Menyediakan referensi cepat untuk developer berikutnya

## Mapping Kode

- `PUU` = Substansi Perundang-Undangan
- `SES` / `SET` = Sekretariat / Sekretaris
- `PRC` = Bagian Perencanaan
- `BU` / `UM` = Bagian Umum
- `TU` = Tata Usaha
- `KEU` = Bagian Keuangan
- `PEIPD` = Direktorat PEIPD
- `SUPD` = Direktorat SUPD
- `SD` = Subdit Wilayah
- `BANGDA` = Ditjen Bina Pembangunan Daerah

## Helper Aktif

Helper yang dipakai workflow saat ini berada di:

- `korespondensi-server/src/services/posisi_mapping.py`

Fungsi penting:

- `parse_posisi_timeline(...)`
- `format_short_date_id(...)`
- `format_posisi_event(...)`
- `build_posisi_timeline_view(...)`

## Contoh

Input:

`SES 16/3 KOREKSI 16/3 SES 6/4 PUU, BU 6/4`

Output timeline yang dibaca pengguna:

- `SES 16 Maret - Koreksi`
- `SES 6 April - Update`
- `PUU 6 April - Posisi diterima`
- `BU 6 April - Posisi diterima`

Teks asli tetap disimpan sebagai referensi:

`Asli: SES 16/3 KOREKSI 16/3 SES 6/4 PUU, BU 6/4`

## Catatan

- Dokumen ini adalah referensi tambahan, bukan sumber kebenaran utama.
- Kalau mapping berubah, update helper di `src/services/posisi_mapping.py` terlebih dahulu.
- Jika perlu jejak eksekusi yang lebih lengkap, catat juga command/endpoint yang
  dipakai saat knowledge ini dihasilkan.
