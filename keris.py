#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""keris.py — presisi sergap tiket UBL, v1.0

Setiap angka di bawah ini hasil ukur di HP ini (Redmi Note 13 Pro 5G,
Telkomsel LTE), bukan tebakan:

  tunda maju (kirim -> server)      25..55 ms      BUKAN RTT/2
  laju pipeline                     4.9..10.9 ms/req, urutan dijaga
  HTTP/1.1 vs HTTP/2 (32 req)       h1 respons pertama +95 ms, h2 +124 ms -> h1 menang
  keep-alive mati                   10..20 s menganggur
  batas laju                        tidak ada di 60 berurutan / 256 pipeline
  sergap di -45 ms, 8..48 req        100%% mendarat di/di atas batas detik
  sergap di -120 ms                  58%% (14/24) -- pipeline kehabisan landasan

Bentuk cookie yang dikirim app asli (dari capture):
  new_bbs_serviceToken=<urlencoded>;versionCode=500440;versionName=5.4.40;deviceId=<40 HEX>;

Pakai:
  keris.py              jalankan sergap
  keris.py --selftest   latihan mekanik pakai token palsu
  keris.py --calibrate  ukur laju + RTT sekarang
  keris.py --verify     cek token, cetak state, keluar
"""
from __future__ import annotations

import atexit
import gzip
import json
import os
import random
import re
import socket
import ssl
import struct
import subprocess
import sys
import threading
import time
import urllib.parse
from datetime import datetime, timedelta, timezone

import i18n

T = i18n.tag

VERSION = "keris 1.0"

HOST = "sgp-api.buy.mi.com"
STATE_PATH = "/bbs/api/global/user/bl-switch/state"
APPLY_PATH = "/bbs/api/global/apply/bl-auth"
USER_AGENT = "okhttp/4.12.0"
VERSION_CODE = "500440"
VERSION_NAME = "5.4.40"
BEIJING = timezone(timedelta(hours=8))

# diukur di HP ini; ubah angka di bawah kalau perlu
FIRE_MS   = -45      # tusuk sekian ms sebelum batas
TUSUKAN   = 32       # tusukan per laras
STAGGER_MS = 2.0     # jeda antar laras
SUSULAN_S = 15       # susulan pelan setelah sergap

NTP_EPOCH = 2208988800
NTP_SERVERS = ("time.google.com", "time.cloudflare.com", "id.pool.ntp.org")

# A-record endpoint Asia, dipakai kalau DNS lokal mengarah ke PoP yang
# tidak mendukung pipelining (mis. ams.aznl dari Eropa). Diukur dulu
# lewat filter_pipeline(), jadi yang mati otomatis dibuang.
EXTRA_IPS = ("47.236.122.116", "43.98.171.210",
             "47.236.97.63", "47.237.204.32")

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
CTX.set_alpn_protocols(["http/1.1"])   # h2 terukur lebih lambat untuk sergap ini

C_OK, C_ERR, C_WARN, C_INFO, C_DIM = (
    "\033[32m", "\033[31m", "\033[33m", "\033[36m", "\033[90m")
C_RST = "\033[0m"

_lock = threading.Lock()
_cliset = 0          # bitmask: 1 = --tusukan dipakai, 2 = --susulan dipakai
_DEV_RE = re.compile(r"deviceId=[^;]*")


def _cliset_add(n):
    global _cliset
    _cliset |= n


def out(tag, msg, color=C_INFO):
    with _lock:
        print(f"{color}{tag:<12}{C_RST} {msg}", flush=True)


def stamp(t):
    d = datetime.fromtimestamp(t, BEIJING)
    return d.strftime("%H:%M:%S.") + f"{int(round(t * 1000)) % 1000:03d}"


def new_dev():
    return f"{random.getrandbits(160):040X}"


def build_cookie(token, dev):
    """Rapikan apa pun yang ditempel user jadi bentuk persis seperti app kirim."""
    t = token.strip().rstrip(";").strip()
    if "new_bbs_serviceToken=" in t:
        t = t.split("new_bbs_serviceToken=", 1)[1].split(";", 1)[0].strip()
    return (f"new_bbs_serviceToken={t};"
            f"versionCode={VERSION_CODE};versionName={VERSION_NAME};deviceId={dev}; ")


# ───────────────────────────── clock ─────────────────────────────

def ntp_query(server, timeout=0.7):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    try:
        t1 = time.time()
        s.sendto(b"\x1b" + b"\0" * 47, (server, 123))
        data, _ = s.recvfrom(1024)
        t4 = time.time()
    finally:
        s.close()
    if len(data) < 48:
        raise ValueError("short ntp")

    def ts(o):
        return (struct.unpack("!I", data[o:o + 4])[0] - NTP_EPOCH
                + struct.unpack("!I", data[o + 4:o + 8])[0] / 2 ** 32)

    t2, t3 = ts(32), ts(40)
    off = ((t2 - t1) + (t3 - t4)) / 2 * 1000.0
    delay = ((t4 - t1) - (t3 - t2)) * 1000.0
    # sampel korup bisa memberi offset raksasa (pernah terlihat 126 tahun).
    # Buang yang di luar ±5 s atau delay negatif / > 2 s: pasti bukan jam asli.
    if not (-5000.0 <= off <= 5000.0):
        raise ValueError(f"offset gila {off:.0f} ms")
    if not (0.0 <= delay <= 2000.0):
        raise ValueError(f"delay gila {delay:.0f} ms")
    return off, delay


def best_ntp(rounds=12, budget_s=None):
    """Lowest-delay sample wins: least path asymmetry, least offset error.

    budget_s caps the whole sweep. Without it a dead NTP server costs a 2 s
    socket timeout per round and can eat the entire pre-fire margin.
    """
    best = None
    deadline = (time.monotonic() + budget_s) if budget_s else None
    for _ in range(max(1, rounds // len(NTP_SERVERS))):
        for srv in NTP_SERVERS:
            if deadline and time.monotonic() >= deadline:
                break
            try:
                off, delay = ntp_query(srv)
                if best is None or delay < best[1]:
                    best = (off, delay, srv)
            except Exception:
                pass
        if deadline and time.monotonic() >= deadline:
            break
    return best


class Clock:
    """Jam dinding terkoreksi NTP. Bisa disinkron ulang: tunggu lama bikin melenceng."""

    def __init__(self, offset_ms):
        self.p0 = time.perf_counter()
        self.t0 = time.time() + offset_ms / 1000.0

    def now(self):
        return self.t0 + (time.perf_counter() - self.p0)

    def resync(self, offset_ms):
        """Re-anchor without a time jump: keep monotonic continuity."""
        cur = self.now()
        new_t0 = time.time() + offset_ms / 1000.0
        self.p0 = time.perf_counter()
        self.t0 = new_t0
        return (new_t0 - cur) * 1000.0   # correction applied, in ms

    def spin_until(self, target):
        while True:
            rem = target - self.now()
            if rem <= 0:
                return
            if rem > 0.02:
                time.sleep(rem - 0.02)


# ───────────────────────────── wake lock ─────────────────────────────

_wake_held = False


def acquire_wake_lock():
    """Cegah Android membekukan Termux selama menunggu.

    Butuh Termux:API (`pkg install termux-api`). Kalau tidak ada, cukup
    peringatan — sisa program tetap jalan.
    """
    global _wake_held
    import shutil
    if shutil.which("termux-wake-lock") is None:
        return False
    try:
        if subprocess.run(["termux-wake-lock"], timeout=5,
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode == 0:
            _wake_held = True
            atexit.register(release_wake_lock)
            return True
    except Exception:
        pass
    return False


def release_wake_lock():
    global _wake_held
    if _wake_held:
        try:
            subprocess.run(["termux-wake-unlock"], timeout=5,
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        except Exception:
            pass
        _wake_held = False


# ───────────────────────────── http ─────────────────────────────

def parse_head(head):
    lines = head.split(b"\r\n")
    status = lines[0].decode("latin1", "replace")
    hdr = {}
    for line in lines[1:]:
        if b":" in line:
            k, v = line.split(b":", 1)
            hdr[k.strip().lower()] = v.strip()
    return status, hdr


def read_response(buf, ss):
    """Return (hdr, body, rest) or (None, None, buf) if more bytes needed."""
    while True:
        sep = buf.find(b"\r\n\r\n")
        if sep >= 0:
            head, rest = buf[:sep], buf[sep + 4:]
            _, hdr = parse_head(head)
            if hdr.get(b"transfer-encoding", b"").lower() == b"chunked":
                i, parts, need = 0, [], False
                while True:
                    j = rest.find(b"\r\n", i)
                    if j < 0:
                        need = True
                        break
                    try:
                        size = int(rest[i:j].split(b";")[0], 16)
                    except ValueError:
                        need = True
                        break
                    if size == 0:
                        k = rest.find(b"\r\n", j + 2)
                        if k < 0:
                            need = True
                            break
                        body = b"".join(parts)
                        if hdr.get(b"content-encoding", b"").lower() == b"gzip":
                            try:
                                body = gzip.decompress(body)
                            except Exception:
                                pass
                        return hdr, body, rest[k + 2:]
                    end = j + 2 + size
                    if len(rest) < end + 2:
                        need = True
                        break
                    parts.append(rest[j + 2:end])
                    i = end + 2
                if not need:
                    return None, None, buf
            else:
                n = int(hdr.get(b"content-length", b"0"))
                if len(rest) >= n:
                    body = rest[:n]
                    if hdr.get(b"content-encoding", b"").lower() == b"gzip":
                        try:
                            body = gzip.decompress(body)
                        except Exception:
                            pass
                    return hdr, body, rest[n:]
        try:
            chunk = ss.recv(65536)
        except socket.timeout:
            return None, None, buf
        if not chunk:
            return None, None, buf
        buf += chunk


class Laras:
    """Satu laras: socket TLS keep-alive yang sudah dipanaskan ke satu A-record."""

    def __init__(self, ip, timeout=6.0):
        raw = socket.create_connection((ip, 443), timeout=timeout)
        raw.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        try:
            raw.setsockopt(socket.IPPROTO_TCP,
                           getattr(socket, "TCP_QUICKACK", 12), 1)
        except OSError:
            pass
        self.ip = ip
        self.ss = CTX.wrap_socket(raw, server_hostname=HOST)
        self.ss.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.buf = b""
        # satu deviceId per laras: itu yang dilakukan app asli. Server
        # menerima 40-hex apa pun (diuji: id asli, id acak, tanpa id semua
        # membalas 200 + state yang sama), jadi cukup terlihat stabil.
        self.dev = new_dev()

    def req(self, token):
        body = b'{"is_retry":true}'
        cookie = build_cookie(token, self.dev)
        return (
            f"POST {APPLY_PATH} HTTP/1.1\r\n"
            f"Host: {HOST}\r\n"
            f"User-Agent: {USER_AGENT}\r\n"
            f"Accept: application/json\r\n"
            f"Content-Type: application/json; charset=utf-8\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"Cookie: {cookie}\r\n"
            f"Accept-Encoding: gzip\r\n"
            f"Connection: keep-alive\r\n"
            f"\r\n"
        ).encode() + body

    def read(self, timeout=8.0):
        self.ss.settimeout(timeout)
        hdr, body, self.buf = read_response(self.buf, self.ss)
        if hdr is None:
            raise ConnectionError("closed / timeout")
        return hdr, body

    def warm(self, token):
        self.ss.sendall(self.req(token))
        self.read()

    def fire(self, blob):
        self.ss.sendall(blob)

    def close(self):
        try:
            self.ss.close()
        except Exception:
            pass


# ───────────────────────────── probes ─────────────────────────────

def resolve_all():
    """Semua A-record. Sebagian endpoint CDN menutup koneksi setelah satu
    respons, jadi pipeline hanya jalan di endpoint yang mendukung keep-alive."""
    try:
        ips = sorted({i[4][0] for i in socket.getaddrinfo(
            HOST, 443, socket.AF_INET, socket.SOCK_STREAM)})
    except (socket.gaierror, OSError):
        ips = []                        # DNS mati — pakai cadangan saja
    # DNS lokal bisa mengarahkan ke PoP yang tidak mendukung pipeline
    # (mis. ams.aznl dari Eropa). Tambahkan A-record Asia sebagai cadangan.
    for extra in EXTRA_IPS:
        if extra not in ips:
            ips.append(extra)
    return ips


def probe_pipeline(ip, token, timeout=3.0):
    """Kirim 2 request sekaligus; berapa respons yang balik?

    Endpoint CDN Xiaomi tidak seragam. Yang menjawab 1 dari 2 tidak bisa
    dipakai untuk sergap berpipa, jadi harus disaring lebih dulu.
    """
    try:
        g = Laras(ip)
        g.warm(token)
        g.fire(g.req(token) * 2)
        n = 0
        for _ in range(2):
            try:
                g.read(timeout=timeout)
                n += 1
            except Exception:
                break
        g.close()
        return n
    except Exception:
        return 0


def filter_pipeline(ips, token, want=4):
    """Ambil `want` endpoint yang benar-benar mendukung pipelining.

    Diukur lebih dulu, bukan diasumsikan: DNS bisa mengarahkan ke PoP yang
    berbeda tergantung lokasi, dan tidak semuanya bisa dipakai.
    """
    good, bad = [], []
    for ip in ips:
        n = probe_pipeline(ip, token)
        (good if n >= 2 else bad).append((ip, n))
        if len(good) >= want:
            break
    if bad:
        out(T("lane"), i18n.t("lane_dilewati",
                              ips=", ".join(f"{ip} ({n}/2)" for ip, n in bad)), C_DIM)
    return [ip for ip, _ in good]


def rtt(ip, n=5):
    vals = []
    for _ in range(n):
        try:
            t = time.perf_counter()
            s = socket.create_connection((ip, 443), timeout=3)
            vals.append((time.perf_counter() - t) * 1000.0)
            s.close()
        except Exception:
            pass
        time.sleep(0.08)
    vals.sort()
    return vals[len(vals) // 2] if vals else None


def check_token(token):
    """Return (usable, description, raw_json)."""
    cookie = build_cookie(token, new_dev())
    head = (f"GET {STATE_PATH} HTTP/1.1\r\nHost: {HOST}\r\n"
            f"User-Agent: {USER_AGENT}\r\nAccept: application/json\r\n"
            f"Cookie: {cookie}\r\nAccept-Encoding: gzip\r\n"
            f"Connection: close\r\n\r\n").encode()
    try:
        raw = socket.create_connection((HOST, 443), timeout=8)
        ss = CTX.wrap_socket(raw, server_hostname=HOST)
        ss.sendall(head)
        buf = b""
        while True:
            c = ss.recv(8192)
            if not c:
                break
            buf += c
        ss.close()
    except Exception as e:
        return False, f"sambungan gagal: {e}", None

    hdr, body, _ = read_response(buf, None) if False else (None, None, None)
    sep = buf.find(b"\r\n\r\n")
    if sep < 0:
        return False, "respons kosong", None
    _, h = parse_head(buf[:sep])
    body = buf[sep + 4:]
    if h.get(b"transfer-encoding", b"").lower() == b"chunked":
        i, parts = 0, []
        while True:
            j = body.find(b"\r\n", i)
            if j < 0:
                break
            try:
                size = int(body[i:j].split(b";")[0], 16)
            except ValueError:
                break
            if size == 0:
                body = b"".join(parts)
                break
            parts.append(body[j + 2:j + 2 + size])
            i = j + 2 + size + 2
    if h.get(b"content-encoding", b"").lower() == b"gzip":
        try:
            body = gzip.decompress(body)
        except Exception:
            pass
    try:
        j = json.loads(body.decode("utf-8", "replace"))
    except Exception:
        return False, f"bukan JSON: {body[:60]!r}", None

    if j.get("code") == 100004:
        return False, "token ditolak (perlu login) — kedaluwarsa atau salah salin", j
    d = j.get("data") or {}
    is_pass = d.get("is_pass", -1)
    btn = d.get("button_state", -1)
    dl = d.get("deadline_format", "")
    if is_pass == 1:
        return True, f"SUDAH punya tiket (deadline {dl})", j
    if (is_pass, btn) == (4, 1):
        return True, "siap sergap", j
    if (is_pass, btn) == (4, 2):
        return False, f"diblokir s/d {dl}", j
    if (is_pass, btn) == (4, 3):
        return True, "status belum jelas (is_pass=4 btn=3) — tetap dicoba", j
    return False, f"belum memenuhi syarat (is_pass={is_pass} btn={btn})", j

# ───────────────────────────── sergap ─────────────────────────────

class Sergap:
    def __init__(self, clock, ips, tokens, tusukan=TUSUKAN, fire_ms=FIRE_MS,
                 stagger_ms=STAGGER_MS, susulan_s=SUSULAN_S):
        self.clock = clock
        self.ips = ips
        self.tokens = tokens
        self.tusukan = tusukan
        self.fire_ms = fire_ms
        self.stagger = stagger_ms / 1000.0
        self.susulan_s = susulan_s
        self.laras = []
        self.gap_ms = 6.0
        self.results = []
        self.winner = None
        self.lock = threading.Lock()

    def prepare(self):
        self.laras = []
        tok = self.tokens[0]
        # saring IP yang benar-benar bisa pipeline (CDN Xiaomi tidak seragam)
        usa = filter_pipeline(self.ips, tok)
        if not usa:
            out(T("lane"), i18n.t("lane_semua_gagal"), C_ERR)
            return
        for i, ip in enumerate(usa):
            tok = self.tokens[i % len(self.tokens)]
            try:
                g = Laras(ip)
                g.warm(tok)
                self.laras.append((g, tok))
            except Exception as e:
                out(T("lane"), i18n.t("lane_gagal", ip=ip, err=e), C_ERR)
        out(T("lane"), i18n.t("lane_siap", n=len(self.laras),
                              total=len(usa), acc=len(self.tokens)), C_OK)

    def calibrate(self):
        if not self.laras:
            return
        g, tok = self.laras[0]
        n = 8
        g.fire(b"".join(g.req(tok) for _ in range(n)))
        gaps, prev = [], None
        for _ in range(n):
            g.read()
            t = self.clock.now()
            if prev is not None:
                gaps.append((t - prev) * 1000.0)
            prev = t
        gaps.sort()
        if gaps:
            self.gap_ms = gaps[len(gaps) // 2]
        out(T("ukur"), i18n.t("ukur_hasil", gap=self.gap_ms,
                              n=self.tusukan, span=self.tusukan*self.gap_ms), C_OK)
        # jaringan lambat: tusukan yang mendarat dulu sudah mengambil kuota,
        # sisanya cuma spam. Kecilkan tusukan biar muat ~300 ms burst.
        # Minimum 2: satu tusukan tanpa cadangan kalah kalau kena 429.
        if self.tusukan * self.gap_ms > 300.0:
            old = self.tusukan
            self.tusukan = max(2, min(old, round(300.0 / self.gap_ms)))
            out(T("ukur"), i18n.t("ukur_lambat", old=old, new=self.tusukan), C_WARN)
            if self.gap_ms > 60.0:
                out(T("AWAS"), i18n.t("ukur_terlalu_lambat", gap=self.gap_ms), C_ERR)

    def run(self, target):
        if not self.laras:
            out(T("gagal"), i18n.t("lane_tidak_ada"), C_ERR)
            return
        base = target + self.fire_ms / 1000.0
        fire = [base + i * self.stagger for i in range(len(self.laras))]
        out(T("sergap"), i18n.t("sergap_rencana", lanes=len(self.laras),
                                n=self.tusukan,
                                total=len(self.laras)*self.tusukan), C_INFO)
        out(T("sergap"), i18n.t("sergap_tusuk", fire=self.fire_ms,
                                span=self.tusukan*self.gap_ms), C_INFO)

        threads = [threading.Thread(target=self._shoot, args=(g, tok, ft), daemon=True)
                   for (g, tok), ft in zip(self.laras, fire)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=45)

        if self.winner is None and self.susulan_s > 0:
            self._susulan()

    def _shoot(self, gun, tok, fire_time):
        blob = b"".join(gun.req(tok) for _ in range(self.tusukan))
        self.clock.spin_until(fire_time)
        sent = self.clock.now()
        try:
            gun.fire(blob)
        except Exception as e:
            out(T("tusuk"), i18n.t("tusuk_gagal", ip=gun.ip, err=e), C_ERR)
            return
        out(T("tusuk"), i18n.t("tusuk_kirim", ip=gun.ip, size=len(blob), time=stamp(sent)), C_OK)

        for k in range(self.tusukan):
            try:
                _, body = gun.read()
            except Exception as e:
                out(T("serap"), i18n.t("serap_putus", ip=gun.ip, n=k, err=e), C_WARN)
                return
            got = self.clock.now()
            try:
                j = json.loads(body.decode("utf-8", "replace"))
            except Exception:
                j = {}
            result = (j.get("data") or {}).get("apply_result")
            with self.lock:
                self.results.append((gun.ip, k, got, j.get("code"), result,
                                     j.get("msg", "")))
                if result in (1, 2) and self.winner is None:
                    self.winner = (gun.ip, k, got, j)
            if result in (1, 2):
                return

    def _susulan(self):
        g, tok = self.laras[0]
        end = self.clock.now() + self.susulan_s
        out(T("susul"), i18n.t("susul_mulai", sec=self.susulan_s), C_INFO)
        hits = 0
        while self.clock.now() < end and self.winner is None:
            try:
                g.fire(g.req(tok))
                _, body = g.read(timeout=5)
                j = json.loads(body.decode("utf-8", "replace"))
                result = (j.get("data") or {}).get("apply_result")
                hits += 1
                if result in (1, 2):
                    with self.lock:
                        self.winner = (g.ip, -1, self.clock.now(), j)
                    break
            except Exception:
                try:
                    g.close()
                    g = Laras(g.ip)
                    g.warm(tok)
                except Exception:
                    break
            time.sleep(0.1)
        out(T("susul"), i18n.t("susul_hasil", n=hits), C_DIM)

    def report(self):
        print()
        if self.winner:
            ip, k, when, j = self.winner
            res = (j.get("data") or {}).get("apply_result")
            label = "sergap" if k >= 0 else "susul"
            out(T("putusan"),
                i18n.t("tiket_dapat" if res == 1 else "tiket_ada",
                       ip=ip, via=label, time=stamp(when)),
                C_OK if res == 1 else C_WARN)
            print(json.dumps(j, indent=2, ensure_ascii=False))
            return res == 1

        out(T("putusan"), i18n.t("putusan_tidak_ada", n=len(self.results)), C_WARN)
        agg = {}
        for _, _, _, code, result, msg in self.results:
            key = f"code={code} apply_result={result} msg={msg!r}"
            agg[key] = agg.get(key, 0) + 1
        for k, v in sorted(agg.items(), key=lambda x: -x[1]):
            out(T("putusan"), f"  x{v}  {k}", C_DIM)
        if self.results:
            ts = sorted(r[2] for r in self.results)
            out(T("putusan"), i18n.t("putusan_respons",
                                     first=stamp(ts[0]), last=stamp(ts[-1])), C_DIM)
        return False


# ───────────────────────────── ui ─────────────────────────────

def next_beijing_midnight():
    now = datetime.now(BEIJING)
    return (now.replace(hour=0, minute=0, second=0, microsecond=0)
            + timedelta(days=1)).timestamp()


def countdown(clock, label, target):
    while True:
        rem = target - clock.now()
        if rem <= 0:
            break
        h, r = divmod(int(rem), 3600)
        m, s = divmod(r, 60)
        print(f"\r{C_INFO}{'[tunggu]':<12}{C_RST} {label} {h:02d}:{m:02d}:{s:02d}    ",
              end="", flush=True)
        time.sleep(0.05)
    print()


def ask(prompt, default):
    try:
        v = input(f"{C_INFO}{'[masuk]':<12}{C_RST} {prompt} [{default}]: ").strip()
    except EOFError:
        return default
    return v or str(default)


def ask_tokens():
    import getpass
    found = []
    for label in ("Token A", "Token B"):
        try:
            v = getpass.getpass(f"{C_INFO}{'[masuk]':<12}{C_RST} {label} "
                                f"(kosong = skip): ")
        except Exception:
            v = ""
        v = v.strip()
        if not v:
            out(T("lewat"), i18n.t("token_kosong", label=label), C_DIM)
            continue
        ok, desc, _ = check_token(v)
        out(T("periksa"), f"{label}: {desc}", C_OK if ok else C_ERR)
        if ok:
            found.append(v)
    return found


def cmd_verify(clock, ips):
    import getpass
    try:
        v = getpass.getpass(f"{C_INFO}{'[masuk]':<12}{C_RST} Token: ").strip()
    except Exception:
        v = ""
    if not v:
        out(T("gagal"), i18n.t("token_kosong", label="token"), C_ERR)
        return 2
    ok, desc, raw = check_token(v)
    out(T("periksa"), desc, C_OK if ok else C_ERR)
    if raw:
        print(json.dumps(raw, indent=2, ensure_ascii=False))
    return 0 if ok else 1


def cmd_calibrate(clock, ips):
    out(T("ukur"), i18n.t("ukur_mulai"), C_INFO)
    tok = "DUMMY"
    # pakai endpoint yang benar-benar bisa pipeline, sama seperti mode sergap
    usa = filter_pipeline(ips, tok)
    if not usa:
        out(T("ukur"), i18n.t("ukur_tidak_ada"), C_ERR)
        return 2
    g = Laras(usa[0])
    g.warm(tok)
    sergap = Sergap(clock, [usa[0]], [tok], tusukan=8)
    sergap.laras = [(g, tok)]
    sergap.calibrate()
    g.close()
    for ip in ips:
        v = rtt(ip, 5)
        if v:
            out(T("rtt"), i18n.t("rtt_hasil", ip=ip, rtt=v, half=v/2), C_DIM)
    out(T("catatan"), i18n.t("catatan_setelan", fire=FIRE_MS, n=TUSUKAN), C_INFO)
    return 0


def cmd_selftest(clock, ips):
    out(T("uji"), i18n.t("uji_mulai"), C_INFO)
    sergap = Sergap(clock, ips, ["DUMMY"], tusukan=16, susulan_s=0)
    sergap.prepare()
    sergap.calibrate()
    target = clock.now() + 6.0
    out(T("uji"), i18n.t("uji_target", time=stamp(target)), C_INFO)
    countdown(clock, "selftest", target - 3)
    sergap.run(target)
    reached = sum(1 for r in sergap.results if r[3] == 100004)
    out(T("uji"), i18n.t("uji_hasil", n=len(sergap.results), ok=reached), C_OK)
    if sergap.results:
        ts = sorted(r[2] for r in sergap.results)
        out(T("uji"), i18n.t("uji_respons",
                             first=1000*(ts[0]-target),
                             last=1000*(ts[-1]-target)), C_DIM)
    for g, _ in sergap.laras:
        g.close()
    return 0


def cmd_sergap(clock, ips):
    tokens = ask_tokens()
    if not tokens:
        out(T("gagal"), i18n.t("token_tidak_ada"), C_ERR)
        return 2

    # flag yang tidak dipakai tetap ditanya; yang dipakai tidak ditanya
    tusukan = TUSUKAN if _cliset & 1 else int(
        ask(i18n.t("tanya_tusukan"), TUSUKAN))
    susulan = SUSULAN_S if _cliset & 2 else int(
        ask(i18n.t("tanya_susulan"), SUSULAN_S))

    target = next_beijing_midnight()
    wait_h = (target - clock.now()) / 3600.0
    out(T("jadwal"), i18n.t("jadwal_target", cst=stamp(target),
                            wib=datetime.fromtimestamp(target).strftime('%H:%M:%S')), C_INFO)
    out(T("jadwal"), i18n.t("jadwal_tunggu", h=wait_h), C_INFO)

    if wait_h > 2.0:
        out(T("AWAS"), i18n.t("jadwal_awas", h=wait_h), C_WARN)
        out(T("AWAS"), i18n.t("jadwal_saran"), C_WARN)
        if ask(i18n.t("tanya_lanjut"), "n").lower() != "y":
            return 3

    if acquire_wake_lock():
        out(T("jaga"), i18n.t("jaga_aktif"), C_OK)
    else:
        out(T("jaga"), i18n.t("jaga_gagal"), C_WARN)
        out(T("jaga"), i18n.t("jaga_saran"), C_WARN)

    sergap = Sergap(clock, ips, tokens, tusukan=tusukan, susulan_s=susulan)
    # prepare+calibrate cost 0.8-2.6 s and final resync up to 1.5 s.
    # Kerjakan 30 s sebelum batas, tapi tidak lebih awal dari sekarang.
    prep = max(target - 30, clock.now())
    countdown(clock, "siaga", prep)
    sergap.prepare()
    if not sergap.laras:
        out(T("gagal"), i18n.t("lane_tidak_ada"), C_ERR)
        return 4
    sergap.calibrate()

    # keep-alive dies 10..20 s idle -> re-warm every 6 s.
    # Also re-sync NTP once per minute: a multi-hour wait drifts.
    last_sync = clock.now()
    while clock.now() < target - 4:
        nap = min(6.0, target - 4 - clock.now())
        if nap <= 0:
            break
        time.sleep(nap)
        if clock.now() >= target - 4:
            break
        for g, tok in sergap.laras:
            try:
                g.warm(tok)
            except Exception:
                pass
        if clock.now() - last_sync > 60:
            b = best_ntp(rounds=6, budget_s=1.0)
            if b:
                corr = clock.resync(b[0])
                last_sync = clock.now()
                if abs(corr) > 2:
                    out(T("sinkron"), i18n.t("sinkron_koreksi",
                                             corr=corr, off=b[0]), C_DIM)

    # sinkron final tepat sebelum tusukan: ini yang paling menentukan.
    # Batas keras 1.5 s supaya server NTP mati tidak memakan margin, dan lewati
    # sepenuhnya kalau sudah terlalu dekat batas.
    if clock.now() < target - 2.5:
        b = best_ntp(rounds=9, budget_s=1.5)
        if b:
            corr = clock.resync(b[0])
            out(T("sinkron"), i18n.t("sinkron_akhir", off=b[0],
                                     delay=b[1], corr=corr), C_OK)
    else:
        out(T("sinkron"), i18n.t("sinkron_lewat"), C_DIM)

    countdown(clock, "aba-aba", target - 1.0)
    sergap.run(target)
    won = sergap.report()
    for g, _ in sergap.laras:
        g.close()
    return 0 if won else 1


USAGE = """pakai: keris.py [opsi]

  (tanpa opsi)      jalankan sergap
  --verify          cek token, cetak state, keluar
  --calibrate       ukur laju pipeline + RTT
  --selftest        latihan mekanik pakai token palsu
  --tusukan N       tusukan per laras (default 32)
  --susulan DETIK   susulan setelah sergap, 0=mati (default 15)
  --fire-ms MS      tusuk sekian ms sebelum batas (default -45)
  --versi           cetak versi
  --help            tampilkan bantuan ini
"""


def parse_args(argv):
    """Parser manual: tidak butuh argparse, jalan di Python 3.6+."""
    opts = {"verify": False, "calibrate": False, "selftest": False,
            "tusukan": None, "susulan": None, "fire_ms": None,
            "lang": None, "help": False}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("-h", "--help"):
            opts["help"] = True
        elif a == "--versi":
            print(VERSION)
            raise SystemExit(0)
        elif a == "--lang":
            if i + 1 >= len(argv):
                print("--lang butuh en atau id")
                raise SystemExit(2)
            opts["lang"] = argv[i + 1]
            i += 1
        elif a == "--verify":
            opts["verify"] = True
        elif a == "--calibrate":
            opts["calibrate"] = True
        elif a == "--selftest":
            opts["selftest"] = True
        elif a in ("--tusukan", "--susulan", "--fire-ms"):
            if i + 1 >= len(argv):
                print(f"{a} butuh angka")
                raise SystemExit(2)
            try:
                v = int(argv[i + 1])
            except ValueError:
                print(f"{a} butuh angka, bukan {argv[i + 1]!r}")
                raise SystemExit(2)
            opts[a.lstrip("-").replace("-", "_")] = v
            i += 1
        else:
            print(f"opsi tidak dikenal: {a}\n")
            print(USAGE)
            raise SystemExit(2)
        i += 1
    return opts


def pick_language():
    """Tanya bahasa sekali di awal. Simpan supaya tidak ditanya lagi."""
    code = i18n.saved_lang()
    if code:
        i18n.set_lang(code)
        return
    # belum pernah pilih: tanya. Jawaban kosong/ngawur -> Inggris.
    print(f"{C_INFO}{'=' * 58}{C_RST}")
    print("  KERIS — UBL ticket sniper / penembak tiket UBL")
    print(f"  {i18n.t('by')}")
    print(f"{C_INFO}{'=' * 58}{C_RST}\n")
    print("  Pilih bahasa / Choose language:")
    print("    1) English")
    print("    2) Indonesia")
    try:
        ans = input("  Nomor / Number (1/2) [1]: ").strip()
    except (EOFError, KeyboardInterrupt):
        ans = "1"
    code = "id" if ans == "2" else "en"
    i18n.save_lang(code)
    i18n.set_lang(code)
    print(f"  {i18n.t('bahasa_disimpan')}\n")


def banner():
    print(f"{C_INFO}{'=' * 58}{C_RST}")
    print(f"  {i18n.t('banner', ver=VERSION)}")
    print(f"  {i18n.t('by')}")
    print(f"{C_INFO}{'=' * 58}{C_RST}\n")


def help_text():
    """Bantuan dua bahasa, mengikuti bahasa aktif."""
    if i18n.lang() == "id":
        return f"""KERIS — penembak tiket Unlock Bootloader Xiaomi
oleh Ds Project

PAKAI
  keris              sergap (tanya token, lalu tunggu batas)
  keris-cek          cek token masih sah, tanpa menunggu
  keris-cal          ukur laju jaringan sekarang
  keris-test         latihan pakai token palsu
  keris-update       ambil versi terbaru

OPSI
  --tusukan N        tusukan per laras (default {TUSUKAN})
  --susulan DETIK    susulan setelah sergap, 0=mati (default {SUSULAN_S})
  --fire-ms MS       tusuk sekian ms sebelum batas (default {FIRE_MS})
  --lang             ganti bahasa (en/id)
  --verify           sama dengan keris-cek
  --calibrate        sama dengan keris-cal
  --selftest         sama dengan keris-test
  --versi            cetak versi
  --help             tampilkan bantuan ini

ALUR MALAM H
  1. 22:55  keris-cal          ukur jaringan
  2. 22:57  keris-cek          tempel token, pastikan "siap sergap"
  3. 22:58  keris              tempel token, Enter, Enter
  4.        tunggu            script menembak otomatis

  Batas: 00:00:00 CST = 23:00:00 WIB.

TOKEN
  Ambil dari app Mi Community lewat PCAPdroid:
  request ke sgp-api.buy.mi.com/bbs/api/global/apply/bl-auth
  copy seluruh baris Cookie. Berlaku satu hari.
"""
    return f"""KERIS — Xiaomi bootloader-unlock ticket sniper
by Ds Project

USAGE
  keris              snipe (asks token, waits for boundary)
  keris-cek          check token is still valid, no waiting
  keris-cal          measure network rate now
  keris-test         rehearsal with a fake token
  keris-update       fetch latest version

OPTIONS
  --tusukan N        shots per lane (default {TUSUKAN})
  --susulan SEC      follow-up after snipe, 0=off (default {SUSULAN_S})
  --fire-ms MS       fire this many ms before boundary (default {FIRE_MS})
  --lang             change language (en/id)
  --verify           same as keris-cek
  --calibrate        same as keris-cal
  --selftest         same as keris-test
  --versi            print version
  --help             show this help

NIGHT-OF RUN
  1. 22:55  keris-cal          measure network
  2. 22:57  keris-cek          paste token, expect "ready"
  3. 22:58  keris              paste token, Enter, Enter
  4.        wait             it fires automatically

  Boundary: 00:00:00 CST = 23:00:00 WIB (UTC+7).

TOKEN
  Capture from the Mi Community app via PCAPdroid:
  request to sgp-api.buy.mi.com/bbs/api/global/apply/bl-auth
  copy the whole Cookie line. Valid for one day.
"""


def main(argv):
    global FIRE_MS, TUSUKAN, SUSULAN_S

    args = parse_args(argv)

    # bahasa: --lang menang, lalu yang tersimpan, lalu tanya sekali
    if args.get("lang"):
        if args["lang"] in ("en", "id"):
            i18n.save_lang(args["lang"])
            i18n.set_lang(args["lang"])
        else:
            print(f"--lang needs 'en' or 'id', not {args['lang']!r}")
            return 2
    else:
        pick_language()

    if args.get("help"):
        banner()
        print(help_text())
        return 0

    banner()

    ips = resolve_all()
    if ips:
        out(T("dns"), i18n.t("dns_hasil", host=HOST, ips=", ".join(ips)), C_INFO)
    else:
        out(T("dns"), i18n.t("dns_cadangan"), C_WARN)

    best = best_ntp(budget_s=2.0)
    if best:
        out(T("ntp"), i18n.t("ntp_selisih", off=best[0], delay=best[1],
                             server=best[2]), C_OK)
        offset = best[0]
    else:
        out(T("ntp"), i18n.t("ntp_gagal"), C_ERR)
        offset = 0.0
    clock = Clock(offset)

    if args["verify"]:
        return cmd_verify(clock, ips)
    if args["calibrate"]:
        return cmd_calibrate(clock, ips)
    if args["selftest"]:
        return cmd_selftest(clock, ips)

    # nilai dari CLI menimpa default konstanta
    if args["fire_ms"] is not None:
        FIRE_MS = args["fire_ms"]
    if args["tusukan"] is not None:
        TUSUKAN = args["tusukan"]
        _cliset_add(1)
    if args["susulan"] is not None:
        SUSULAN_S = args["susulan"]
        _cliset_add(2)
    return cmd_sergap(clock, ips)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        print()
        sys.exit(130)
