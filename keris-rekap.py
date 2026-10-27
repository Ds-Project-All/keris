#!/usr/bin/env python3
"""Rekap pemakaian KERIS dari /var/log/nginx/keris-install.log.

Hanya membaca log, tidak menulis apa pun. Jalankan di VPS:
    sudo python3 /root/keris-rekap.py
"""
import collections
import re
import sys

LOG = "/var/log/nginx/keris-install.log"
BAD = re.compile(r"bot|crawler|spider|monitor|preview", re.I)
LINE = re.compile(r"^(\S+) - - \[([^\]]+)\] \"GET /keris-ping\?src=(\S*)")


def baca():
    try:
        with open(LOG, encoding="utf-8", errors="replace") as f:
            return f.read().splitlines()
    except FileNotFoundError:
        sys.exit(f"{LOG} belum ada — belum ada yang memasang.")


def main():
    semua = baca()
    if not semua:
        sys.exit("log kosong — belum ada yang memasang.")

    hari = collections.Counter()
    ip = collections.Counter()
    src = collections.Counter()
    ua = collections.Counter()

    for ln in semua:
        m = LINE.match(ln)
        if not m:
            continue
        addr, waktu, s = m.groups()
        tanggal = waktu.split(":")[0]
        ua_all = ln.split('"')[-2] if ln.count('"') >= 2 else "-"
        palsu = bool(BAD.search(ua_all))
        if not palsu:
            hari[tanggal] += 1
            ip[addr] += 1
        src[s or "-"] += 1
        ua[ua_all[:60]] += 1

    total = sum(hari.values())
    print(f"total pasang (tanpa bot): {total}")
    print(f"hari unik            : {len(hari)}")
    print(f"IP unik              : {len(ip)}")
    print("\nper hari:")
    for d, n in sorted(hari.items()):
        print(f"  {d}  {n:>4}")
    print("\nsumber (?src=):")
    for s, n in src.most_common():
        print(f"  {s:<16} {n}")
    print("\n10 IP teratas:")
    for a, n in ip.most_common(10):
        print(f"  {a:<18} {n}")
    print("\nuser-agent teratas:")
    for u, n in ua.most_common(8):
        print(f"  {n:>4}  {u}")
    print(f"\ntotal baris log mentah: {len(semua)}")


if __name__ == "__main__":
    main()
