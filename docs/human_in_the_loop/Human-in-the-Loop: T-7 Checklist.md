Bagus — ini pertanyaan yang tepat ditanyakan sebelum T-7 dimulai.

---

## Human-in-the-Loop: T-7 Checklist

### HARUS DILAKUKAN ✅

**Sebelum setiap step, baca checkpoint-nya dulu.** Jangan lanjut ke step berikutnya sebelum checkpoint step sebelumnya benar-benar pass — bukan "kira-kira pass."

**Set environment variables production secara manual dan verifikasi:**
```bash
export JWT_SECRET=$(openssl rand -hex 32)
export MCP_ENV=production
./verify_env.sh  # harus pass 100%
```

**Backup database sebelum initialization.** Apapun yang ada di development environment, backup dulu sebelum disentuh.

**Jalankan smoke test sendiri, jangan hanya percaya laporan agent.** Buka terminal, jalankan command, lihat output dengan mata kepala sendiri.

**Catat waktu dan hasil setiap checkpoint** — bukan di kepala, tapi di dokumen atau channel. Ini penting untuk audit trail kalau ada masalah.

**Pada saat canary deployment (Step 5), pantau 30 menit penuh.** Jangan tinggalkan dashboard di menit ke-10 karena "kelihatan oke."

---

### JANGAN DILAKUKAN ❌

**Jangan skip checkpoint meskipun "kelihatan obvious."** Terutama DB health check dan knowledge health check — ini bukan formalitas.

**Jangan parallelkan Steps 1-5.** Sudah diputuskan sequential di Go/No-Go meeting. Godaan untuk mempercepat itu nyata, tapi risikonya lebih besar.

**Jangan approve laporan agent tanpa verifikasi independen** untuk step-step kritis. Agent bisa melaporkan "✅ passed" tapi Anda perlu konfirmasi sendiri minimal untuk Step 4 (smoke test) dan Step 5 (canary).

**Jangan lanjutkan kalau error rate canary >1%** meskipun agent menyarankan "masih dalam batas toleransi." Threshold sudah ditetapkan — patuhi.

**Jangan lewatkan daily monitoring jam 09:00 di Week 1.** Ini bukan opsional.

**Jangan percaya "all systems green" tanpa melihat actual metrics.** Minta angka konkret: berapa req/s, berapa p95 latency, berapa error count.

---

### Satu Prinsip Utama

> Anda adalah decision maker terakhir. Agent bisa salah, laporan bisa misleading. Kalau ada yang terasa tidak beres — **stop, investigasi, baru lanjut.**

Rollback procedure sudah ada dan sudah tested. Tidak ada yang perlu ditakuti dari keputusan untuk pause atau rollback.