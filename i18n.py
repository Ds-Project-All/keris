"""i18n.py — teks dua bahasa untuk KERIS.

Pilih bahasa sekali saat pertama jalan, disimpan di ~/.config/keris/lang.
Kunci yang tidak ada di kamus jatuh ke bahasa Inggris.
"""
from __future__ import annotations

import os

CONFIG_DIR = os.path.expanduser("~/.config/keris")
LANG_FILE = os.path.join(CONFIG_DIR, "lang")

EN = {
    # ── umum ──
    "banner": "KERIS — UBL ticket sniper   {ver}",
    "by": "by Ds Project",
    "gagal": "FAILED",
    "lewat": "skip",
    "catatan": "note",
    "jadwal": "schedule",
    "jaga": "keep-awake",
    "sinkron": "sync",
    "periksa": "check",
    "tunggu": "waiting",
    "putusan": "verdict",
    "opsi": "option",
    # ── pilih bahasa ──
    "pilih_bahasa": "Choose language / Pilih bahasa:",
    "bahasa_1": "1) English",
    "bahasa_2": "2) Indonesia",
    "bahasa_pilih": "Number (1/2)",
    "bahasa_disimpan": "Language saved. Change anytime: keris --lang",
    # ── dns / jaringan ──
    "dns": "dns",
    "dns_hasil": "{host} -> {ips}",
    "dns_cadangan": "DNS failed — using backup IPs",
    # ── ntp ──
    "ntp": "ntp",
    "ntp_selisih": "offset {off:+.1f} ms (delay {delay:.1f}, {server})",
    "ntp_gagal": "NTP failed — using phone clock",
    # ── laras / pipeline ──
    "lane": "lane",
    "lane_dilewati": "skipped (no pipelining): {ips}",
    "lane_semua_gagal": "all IPs failed pipeline test",
    "lane_gagal": "{ip} failed: {err}",
    "lane_siap": "{n}/{total} ready ({acc} account(s))",
    "lane_tidak_ada": "no working lane — check signal/data, then retry",
    # ── ukur ──
    "ukur": "measure",
    "ukur_mulai": "measuring pipeline rate + RTT",
    "ukur_hasil": "{gap:.1f} ms/req -> {n} shots cover {span:.0f} ms",
    "ukur_lambat": "slow network: shots {old} -> {new} (fit 300 ms)",
    "ukur_terlalu_lambat": "{gap:.0f} ms/req too slow to win quota. Use WiFi or 4G.",
    "ukur_tidak_ada": "no IP can pipeline",
    "rtt": "rtt",
    "rtt_hasil": "{ip}: RTT {rtt:.1f} ms -> RTT/2 {half:.1f} ms",
    "catatan_setelan": "current: fire {fire} ms before boundary, {n} shots/lane",
    # ── sergap ──
    "sergap": "snipe",
    "sergap_rencana": "{lanes} lanes x {n} = {total} shots",
    "sergap_tusuk": "fire {fire} ms before boundary, each lane covers {span:.0f} ms",
    "tusuk": "fire",
    "tusuk_gagal": "{ip} failed: {err}",
    "tusuk_kirim": "{ip} {size}B @ {time}",
    "serap": "drain",
    "serap_putus": "{ip} closed #{n}: {err}",
    "susul": "follow-up",
    "susul_mulai": "slow follow-up {sec:.0f}s",
    "susul_hasil": "{n} extra shots",
    # ── hasil ──
    "tiket_dapat": "TICKET GRANTED via {ip} ({via}) @ {time}",
    "tiket_ada": "TICKET ALREADY HELD via {ip} ({via}) @ {time}",
    "putusan_tidak_ada": "{n} responses, no ticket",
    "putusan_respons": "  responses {first} .. {last}",
    # ── token ──
    "token": "token",
    "token_a": "Token A",
    "token_kosong": "{label} empty",
    "token_siap": "{label}: ready",
    "token_tidak_ada": "no valid token",
    "token_tolak": "token rejected (login needed) — expired",
    # ── prompt ──
    "tanya_tusukan": "Shots per lane",
    "tanya_susulan": "Follow-up after snipe (sec, 0=off)",
    "tanya_lanjut": "Continue? (y/n)",
    # ── jadwal ──
    "jadwal_target": "target {cst} CST = {wib} WIB",
    "jadwal_tunggu": "starting now means waiting {h:.1f} hours",
    "jadwal_awas": "waiting {h:.1f} hours. Risk: Android kills Termux, phone restarts, or signal drops.",
    "jadwal_saran": "safer to start 22:55-22:59 WIB.",
    # ── wake lock ──
    "jaga_aktif": "on — Android will not freeze Termux",
    "jaga_gagal": "FAILED (must run inside Termux app, not adb)",
    "jaga_saran": "open Termux, run termux-wake-lock once",
    # ── sinkron ──
    "sinkron_koreksi": "clock correction {corr:+.1f} ms (offset {off:+.1f})",
    "sinkron_akhir": "final offset {off:+.1f} ms (delay {delay:.1f}), correction {corr:+.1f} ms",
    "sinkron_lewat": "skipped — too close to boundary",
    # ── uji ──
    "uji": "test",
    "uji_mulai": "fake token — mechanics & timing only",
    "uji_target": "target {time}",
    "uji_hasil": "{n} responses, {ok} reached server",
    "uji_respons": "responses {first:+.0f} .. {last:+.0f} ms from target",
    # ── argumen ──
    "arg_angka": "{flag} needs a number",
    "arg_bukan_angka": "{flag} needs a number, not {val}",
    "arg_unknown": "unknown option: {flag}",
}

ID = {
    "banner": "KERIS — penembak tiket UBL   {ver}",
    "by": "oleh Ds Project",
    "gagal": "GAGAL",
    "lewat": "lewat",
    "catatan": "catatan",
    "jadwal": "jadwal",
    "jaga": "jaga",
    "sinkron": "sinkron",
    "periksa": "periksa",
    "tunggu": "tunggu",
    "putusan": "putusan",
    "opsi": "opsi",
    "pilih_bahasa": "Pilih bahasa / Choose language:",
    "bahasa_1": "1) Indonesia",
    "bahasa_2": "2) English",
    "bahasa_pilih": "Nomor (1/2)",
    "bahasa_disimpan": "Bahasa disimpan. Ganti kapan saja: keris --lang",
    "dns": "dns",
    "dns_hasil": "{host} -> {ips}",
    "dns_cadangan": "DNS gagal — pakai IP cadangan",
    "ntp": "ntp",
    "ntp_selisih": "selisih {off:+.1f} ms (tunda {delay:.1f}, {server})",
    "ntp_gagal": "NTP gagal — pakai jam HP",
    "lane": "laras",
    "lane_dilewati": "dilewati (tidak bisa pipeline): {ips}",
    "lane_semua_gagal": "semua IP gagal tes pipeline",
    "lane_gagal": "{ip} gagal: {err}",
    "lane_siap": "{n}/{total} siap ({acc} akun)",
    "lane_tidak_ada": "tidak ada laras hidup — cek sinyal/data, lalu ulangi",
    "ukur": "ukur",
    "ukur_mulai": "ukur laju pipeline + RTT",
    "ukur_hasil": "{gap:.1f} ms/req -> {n} tusukan menutup {span:.0f} ms",
    "ukur_lambat": "jaringan lambat: tusukan {old} -> {new} (biar muat 300 ms)",
    "ukur_terlalu_lambat": "{gap:.0f} ms/req terlalu lambat untuk rebutan kuota. Pakai WiFi atau 4G.",
    "ukur_tidak_ada": "tidak ada IP yang bisa pipeline",
    "rtt": "rtt",
    "rtt_hasil": "{ip}: RTT {rtt:.1f} ms -> RTT/2 {half:.1f} ms",
    "catatan_setelan": "setelan sekarang: tusuk {fire} ms sebelum batas, {n} tusukan/laras",
    "sergap": "sergap",
    "sergap_rencana": "{lanes} laras x {n} = {total} tusukan",
    "sergap_tusuk": "tusuk {fire} ms sebelum batas, tiap laras menutup {span:.0f} ms",
    "tusuk": "tusuk",
    "tusuk_gagal": "{ip} gagal: {err}",
    "tusuk_kirim": "{ip} {size}B @ {time}",
    "serap": "serap",
    "serap_putus": "{ip} putus #{n}: {err}",
    "susul": "susul",
    "susul_mulai": "susul pelan {sec:.0f}s",
    "susul_hasil": "{n} tusukan tambahan",
    "tiket_dapat": "TIKET DIDAPAT via {ip} ({via}) @ {time}",
    "tiket_ada": "TIKET SUDAH ADA via {ip} ({via}) @ {time}",
    "putusan_tidak_ada": "{n} respons, tidak ada tiket",
    "putusan_respons": "  respons {first} .. {last}",
    "token": "token",
    "token_a": "Token A",
    "token_kosong": "{label} kosong",
    "token_siap": "{label}: siap sergap",
    "token_tidak_ada": "tidak ada token sah",
    "token_tolak": "token ditolak (perlu login) — kedaluwarsa",
    "tanya_tusukan": "Tusukan per laras",
    "tanya_susulan": "Susulan setelah sergap (detik, 0=mati)",
    "tanya_lanjut": "Teruskan? (y/n)",
    "jadwal_target": "target {cst} CST = {wib} WIB",
    "jadwal_tunggu": "mulai sekarang berarti menunggu {h:.1f} jam",
    "jadwal_awas": "menunggu {h:.1f} jam. Risiko: Termux dibunuh Android, HP restart, atau sinyal hilang.",
    "jadwal_saran": "lebih aman jalankan 22:55-22:59 WIB.",
    "jaga_aktif": "aktif — Android tidak akan bekukan Termux",
    "jaga_gagal": "GAGAL (harus dari dalam app Termux, bukan adb)",
    "jaga_saran": "buka Termux, jalankan termux-wake-lock sekali",
    "sinkron_koreksi": "koreksi jam {corr:+.1f} ms (selisih {off:+.1f})",
    "sinkron_akhir": "selisih akhir {off:+.1f} ms (tunda {delay:.1f}), koreksi {corr:+.1f} ms",
    "sinkron_lewat": "dilewati — sudah terlalu dekat batas",
    "uji": "uji",
    "uji_mulai": "token palsu — mekanik & timing saja",
    "uji_target": "target {time}",
    "uji_hasil": "{n} respons, {ok} sampai ke server",
    "uji_respons": "respons {first:+.0f} .. {last:+.0f} ms dari target",
    "arg_angka": "{flag} butuh angka",
    "arg_bukan_angka": "{flag} butuh angka, bukan {val}",
    "arg_unknown": "opsi tidak dikenal: {flag}",
}

DICTS = {"en": EN, "id": ID}

# nama tag terminal ikut bahasa, supaya tidak campur
TAGS = {
    "en": {"dns": "dns", "ntp": "ntp", "lane": "lane", "ukur": "measure",
           "sergap": "snipe", "tusuk": "fire", "serap": "drain",
           "susul": "follow-up", "putusan": "verdict", "jadwal": "schedule",
           "jaga": "keep-awake", "sinkron": "sync", "uji": "test",
           "gagal": "FAILED", "AWAS": "WARNING", "periksa": "check",
           "catatan": "note", "tunggu": "waiting", "lewat": "skip",
           "rtt": "rtt", "token": "token"},
    "id": {"dns": "dns", "ntp": "ntp", "lane": "laras", "ukur": "ukur",
           "sergap": "sergap", "tusuk": "tusuk", "serap": "serap",
           "susul": "susul", "putusan": "putusan", "jadwal": "jadwal",
           "jaga": "jaga", "sinkron": "sinkron", "uji": "uji",
           "gagal": "gagal", "AWAS": "AWAS", "periksa": "periksa",
           "catatan": "catatan", "tunggu": "tunggu", "lewat": "lewat",
           "rtt": "rtt", "token": "token"},
}

_lang = None


def saved_lang():
    """Bahasa tersimpan, atau None kalau belum pernah dipilih."""
    try:
        with open(LANG_FILE, encoding="utf-8") as f:
            v = f.read().strip()
        return v if v in DICTS else None
    except OSError:
        return None


def save_lang(code):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(LANG_FILE, "w", encoding="utf-8") as f:
            f.write(code + "\n")
    except OSError:
        pass


def set_lang(code):
    global _lang
    _lang = code if code in DICTS else "en"


def lang():
    return _lang or "en"


def t(key, **kw):
    """Terjemahan. Kunci hilang -> bahasa Inggris -> kunci itu sendiri."""
    d = DICTS.get(_lang or "en", EN)
    s = d.get(key) or EN.get(key) or key
    try:
        return s.format(**kw)
    except (KeyError, IndexError):
        return s


def tag(name):
    """Nama tag terminal sesuai bahasa aktif."""
    return TAGS.get(_lang or "en", TAGS["en"]).get(name, name)
