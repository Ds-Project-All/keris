# KERIS

Presisi sergap tiket Unlock Bootloader Xiaomi (HyperOS / Mi Community Global).

Satu perintah, 128 tusukan dalam ~200 ms, dijadwalkan ke milidetik batas
`00:00:00 CST` (23:00:00 WIB).

```
==========================================================
  KERIS — presisi sergap tiket UBL   keris 1.0
==========================================================

[dns]        sgp-api.buy.mi.com -> 43.98.171.210, 47.236.122.116, ...
[ntp]        selisih +251.2 ms (tunda 30.0, id.pool.ntp.org)
[masuk]      Token A (kosong = lewat):
[periksa]    Token A: siap sergap
[laras]      4/4 siap (1 akun)
[ukur]       5.3 ms/req -> 32 tusukan menutup 170 ms
[sinkron]    selisih akhir +243.1 ms (tunda 33.7), koreksi +0.4 ms
[sergap]     4 laras x 32 = 128 tusukan
[tusuk]      47.236.122.116 18048B @ 23:59:59.961
[putusan]    TIKET DIDAPAT via 47.236.122.116 (sergap) @ 00:00:02.859
```

## Kenapa beda

Bot UBL biasa menembak 4–6 request dalam bracket simetris ±70 ms. Setengahnya
mendarat **sebelum** batas dan otomatis gagal. KERIS memakai data ukur:

| Yang diukur | Hasil | Kenapa penting |
|---|---|---|
| Tunda maju (kirim → server) | 25–55 ms | Bukan `RTT/2`. Salah di sini = telat 100 ms |
| Laju pipeline | 4.9–10.9 ms/req | 32 request menutup 170–350 ms jendela |
| HTTP/1.1 vs HTTP/2 | h1 +95 ms, h2 +124 ms | h1 menang 30 ms untuk sergap |
| Keep-alive mati | 10–20 s menganggur | Laras dipanaskan ulang tiap 6 s |
| Batas laju | tidak ada (256 pipeline) | Aman kirim banyak sekaligus |
| Mendarat di −45 ms | 100% (24/24) | Selisih terpilih |

Tabel landing yang dipakai memilih `-45 ms`:

| Offset | Mendarat setelah batas |
|---|---|
| −120 ms | 58% |
| −90 ms | 75% |
| −60 ms | 96% |
| **−45 ms** | **100%** |

Bracket simetris membuang separuh percobaan. KERIS hanya menembak ke depan.

## Pasang

Satu file, tanpa dependensi di luar stdlib. Python 3.8+.

### Android (Termux) — disarankan

Pakai Termux dari [F-Droid](https://f-droid.org/packages/com.termux/) atau
[GitHub release](https://github.com/termux/termux-app/releases). Versi Play
Store sudah usang dan tidak bisa `pkg install`.

```bash
pkg update && pkg install python -y
termux-wake-lock
python keris.py --selftest
```

`termux-wake-lock` mencegah Android membekukan proses saat menunggu.

### Linux

```bash
python3 -m pip install --upgrade pip   # opsional
chmod +x keris.py
./keris.py --selftest
```

Debian/Ubuntu yang belum punya Python: `sudo apt install python3`.

### macOS

```bash
python3 keris.py --selftest
```

Python 3 sudah ada di macOS 12+. Kalau belum: `brew install python3`.

### Windows

```powershell
python keris.py --selftest
```

Butuh [Python 3.8+](https://python.org/downloads) — centang **Add Python to PATH**
saat instalasi. PowerShell dan CMD sama-sama bisa.

### Diuji di

| OS | Versi | Hasil |
|---|---|---|
| Android 16 / Termux | Python 3.14.8 | semua mode lolos, 64/64 tusukan |
| Ubuntu 24.04 (VPS) | Python 3.12.3 | semua mode lolos, 64/64 tusukan |
| Windows 10 | Python 3.14.7 | semua mode lolos, 64/64 tusukan |
| macOS | — | belum diuji langsung |

macOS memakai API socket POSIX yang sama dengan Linux, jadi seharusnya jalan.

### Kalau endpoint tidak bisa pipeline

Xiaomi memakai beberapa CDN. Endpoint Eropa (`ams.aznl.pubproxy.lb.mi.com`,
IP `20.157.x` / `20.47.x`) **menutup koneksi setelah satu respons**, jadi
pipelining tidak jalan di sana — 8 request hanya dibalas 1.

KERIS mengukur ini otomatis sebelum sergap:

```
[laras]  dilewati (tidak bisa pipeline): 20.157.18.26 (0/2), 20.47.97.185 (0/2)
[laras]  4/4 siap (1 akun)
```

Kalau DNS lokal hanya memberi endpoint Eropa, `EXTRA_IPS` menambahkan
A-record Asia sebagai cadangan, lalu disaring lagi. Yang tidak lolos tes
2-request otomatis dibuang.

Konsekuensinya: dari Eropa RTT ke Asia ~166 ms, dari Indonesia ~40 ms.
**HP di Indonesia tetap jalur tercepat.**

## Ambil token

Token = cookie `new_bbs_serviceToken` dari app Mi Community.

1. Pasang sniffer: [PCAPdroid](https://play.google.com/store/apps/details?id=com.emanuelef.remote_capture),
   [Proxyman](https://play.google.com/store/apps/details?id=com.proxyman.proxymanandroid),
   atau [HTTP Toolkit](https://play.google.com/store/apps/details?id=tech.httptoolkit.android.v1).
2. Buka **Mi Community** → tab **Me** → **Unlock bootloader**.
3. Matikan sniffer, cari request:
   ```
   POST https://sgp-api.buy.mi.com/bbs/api/global/apply/bl-auth
   ```
4. Copy nilai `Cookie:` mulai dari `new_bbs_serviceToken=` sampai sebelum `;versionCode`.

Kalau menu **Unlock bootloader** tidak muncul, ganti region app ke **Global**.

**Penting:** matikan sniffer dan VPN sebelum menjalankan `keris.py`. VPN lokal
menambah 50–150 ms dan membunuh seluruh presisi.

## Pakai

| Perintah | Fungsi |
|---|---|
| `python keris.py` | sergap penuh (tanya token + parameter) |
| `python keris.py --verify` | cek token masih sah, tanpa nunggu |
| `python keris.py --calibrate` | ukur laju pipeline + RTT sekarang |
| `python keris.py --selftest` | latihan mekanik pakai token palsu |
| `python keris.py --help` | daftar semua opsi |

### Opsi lanjutan

| Flag | Default | Arti |
|---|---|---|
| `--fire-ms MS` | `-45` | tusuk sekian ms sebelum batas |
| `--tusukan N` | `32` | tusukan per laras |
| `--susulan DETIK` | `15` | susulan setelah sergap, `0` = mati |
| `--versi` | — | cetak versi |

Kalau `--tusukan` atau `--susulan` dipakai, prompt-nya dilewati:

```bash
python keris.py --tusukan 48 --susulan 30
```

### Alur malam H

```bash
termux-wake-lock          # sekali, cegah Android freeze
python keris.py --verify  # 22:57 — pastikan "siap sergap"
python keris.py           # 22:58 — tempel token, Enter, Enter
```

`--verify` aman dijalankan kapan saja. Tidak makan kuota, tidak mengubah state.

### Start jam berapa

KERIS selalu mengejar `00:00:00 CST` **berikutnya**. Lewat 23:00 WIB sedikit
saja = lompat ke besok.

| Start (WIB) | Nunggu | Catatan |
|---|---|---|
| 22:50 | 10 menit | aman |
| **22:57** | **3 menit** | **disarankan** |
| 22:59:30 | 30 detik | aman |
| 23:00 | 24 jam | lewat |

Batas bawah teknis ~5 detik (persiapan laras + kalibrasi). Jangan lebih mepet —
kamu masih harus mengetik token.

Nunggu >2 jam memicu peringatan + konfirmasi, karena risiko Android membunuh
Termux, HP restart, atau sinyal hilang jauh lebih besar daripada manfaatnya.

## Arti kode

State (`bl-switch/state`):

| `is_pass` / `button_state` | Arti |
|---|---|
| `1` / – | Sudah punya izin |
| `4` / `1` | Siap sergap |
| `4` / `2` | Diblokir sampai `deadline` |
| `4` / `3` | Akun < 30 hari |

Apply (`apply/bl-auth`):

| `apply_result` | Arti |
|---|---|
| `1` | **Disetujui** — `deadline` ~1 tahun |
| `2` | Sudah punya / error akun |
| `3` | Kuota habis — `deadline` besok |
| `6` | Server sibuk |

`apply_result: 3` bisa muncul walau backend sudah menyetujui ("silent
approval"). Kalau tusukan mendarat di detik pembukaan, cek efeknya — tautkan akun
di HP. Kalau bind berhasil, izin benar-benar ada.

## Setelah dapat tiket

Izin **tidak** langsung aktif. Urutannya:

1. **Di HP** — Developer options → Status Mi Unlock → **Tambah akun dan perangkat**.
   Syarat: **WiFi mati, data seluler nyala**, SIM dengan kuota data tersisa.
   Berhasil kalau muncul *"Berhasil ditambahkan"*.
2. **Di PC** — unduh [Mi Unlock Tool](https://unlock.update.miui.com), login
   akun Xiaomi yang **sama**.
3. HP ke **fastboot** (Volume Down + Power), sambung USB, klik **Unlock**.
4. Kemungkinan besar muncul *"Couldn't unlock. Please unlock 168 hours later"*.
   **Normal.** Tunggu 7 hari, ulangi langkah 3–4.

Selama 7 hari itu: **jangan factory reset**, **jangan sign out akun Xiaomi**,
**jangan lepas SIM lama**. Salah satu = timer 168 jam reset.

> Unlock bootloader **menghapus seluruh data HP**. Backup sebelum klik Unlock.
> "Cari perangkat" tidak berfungsi lagi setelah bootloader terbuka.

## Struktur

```
keris.py     satu file, tanpa dependensi di luar stdlib
```

Modul internal:

| Bagian | Fungsi |
|---|---|
| `Clock` | jam NTP + `perf_counter`, bisa re-sync tanpa lompat |
| `Laras` | satu socket TLS, dipanaskan dulu, kirim sergap |
| `Sergap` | orkestrasi 4 laras, kalibrasi, laporan |
| `ntp_query` / `best_ntp` | sampel delay terendah, dibatasi deadline |

## Catatan teknis

- **Cookie** dibiarkan URL-encoded. Jangan di-decode.
- **deviceId** 40 hex, dibuat per laras. Server tidak memvalidasinya
  (diuji: ID asli, ID acak, tanpa ID — semua 200).
- **ALPN** dipaksa `http/1.1`. HTTP/2 butuh `:authority`, bukan `host`, kalau
  tidak → 400.
- **NTP** dibatasi `budget_s`. Tanpa itu, satu server mati = 2 s timeout ×
  sembilan ronde = 6.9 s terbuang tepat sebelum tusukan.
- **Resync final** dilewati kalau sisa waktu < 2.5 s.
- **Sampel NTP disaring**: offset di luar ±5 s atau delay di luar 0–2 s
  dibuang. Tanpa ini satu paket korup bisa menggeser jam 126 tahun dan
  membuat seluruh jadwal meleset.

## Batasan

- Butuh Python 3.8+ (stdlib saja, tanpa `pip install`).
- Diuji langsung di Android/Termux, Ubuntu 24.04, dan Windows 10. macOS belum.
- Lokasi menentukan hasil. Dari Indonesia RTT ~40 ms; dari Eropa ~166 ms dan
  endpoint CDN-nya tidak mendukung pipelining. **HP di Indonesia tetap
  jalur tercepat** — PC/VPS berguna sebagai cadangan.
- Kuota harian bisa habis dalam <50 ms. 128 tusukan dalam 200 ms sudah maksimal;
  kalau ada ribuan pesaing, yang menang tetap jalur terdekat ke Singapura.
- Endpoint bisa ditambal Xiaomi kapan saja.

## Lisensi

MIT — lihat [LICENSE](LICENSE).

Dibangun dari riset protokol publik. Angka timing diukur sendiri di
Redmi Note 13 Pro 5G / Telkomsel LTE.
