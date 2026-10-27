# KERIS

Xiaomi bootloader-unlock (UBL) ticket sniper for Android. Single file, stdlib
only, no root. **by Ds Project**

```
dns          sgp-api.buy.mi.com -> 47.236.122.116, 43.98.171.210, ...
ntp          offset +263.8 ms (delay 34.3, time.google.com)
lane         4/4 ready (1 account)
measure      5.3 ms/req -> 32 shots cover 169 ms
snipe        4 lanes x 32 = 128 shots
test         64 responses, 64 reached server
test         responses +0 .. +89 ms from target
```

> **Status: Production Ready.** GPL-3.0. See [License](#license).

---

## Why phone, not PC

Quota opens at exactly `00:00:00 CST` (Beijing) = `23:00:00 WIB`. The winner is
not the fastest code — it is whoever's packet **arrives first**.

| From | RTT to server (Singapore) | Odds |
|---|---|---|
| Phone in Indonesia, 4G | ~40 ms | best |
| EU VPS | ~166 ms | loses 126 ms |
| Home WiFi | ~20-60 ms | fine |

Xiaomi's global API sits in Singapore. From Indonesia the path is short. From
Europe no code trick closes 126 ms.

---

## Install

### 1. Termux

Get it from [F-Droid](https://f-droid.org/packages/com.termux/) or
[GitHub release](https://github.com/termux/termux-app/releases). The Play Store
build is out of date and `pkg install` fails there.

Fresh install? After opening Termux for the first time, wait for its welcome
text (`Welcome to Termux!`) — the package manager is still setting itself up in
the background. Then update the package list first; a new Termux has **no**
`curl` yet:

```bash
pkg update -y
pkg install -y curl
```

`pkg update` may print mirror questions — just press Enter and accept the
defaults. If it complains about unknown packages, run `termux-change-repo`,
pick a mirror, then repeat.

### 2. One command

```bash
bash <(curl -s https://raw.githubusercontent.com/Ds-Project-All/keris/main/install.sh)
```

The installer does everything: installs `python` if missing, downloads
`keris.py` and `i18n.py` to `~/keris/`, puts the `keris` command on your PATH,
and turns on the wake-lock. At the end it runs `keris.py --versi` and stops with
a clear error if that fails.

### 3. Pick a language

First run asks once — English or Indonesian — and remembers. Change any time:

```bash
keris --lang en     # or: keris --lang id
```

### Commands

| Command | Does |
|---|---|
| `keris` | full snipe |
| `keris-cal` | measure network rate |
| `keris-cek` | check a token is valid |
| `keris-test` | rehearsal with a fake token |
| `keris-help` | full help |
| `keris-update` | fetch the latest version |

Without the wrapper: `python3 ~/keris/keris.py`

### Wake-lock

The installer runs `termux-wake-lock` so Android does not freeze Termux during
the 3-minute countdown. If `termux-api` is missing it warns and continues — but
install it:

```bash
pkg install termux-api
```

Then install the **Termux:API** app from F-Droid and allow its notifications.
At minimum: Settings → Apps → Termux → Battery → **Unrestricted**, and lock
Termux in recents.

### Update

```bash
keris-update
```

---

## Use

### Check the token first

```bash
keris-cek
```

Paste the token. `state=4` or `ok` means it is alive.

### Measure the network

```bash
keris-cal
```

```
measure      5.3 ms/req -> 32 shots cover 169 ms
```

Above 60 ms/req, switch to WiFi or 4G.

### Snipe

```bash
keris
```

Asks for shots per lane (Enter = 32) and follow-up seconds (Enter = 15), then
counts down and fires on its own.

**Start 22:57-22:59 WIB.** Earlier risks Android killing Termux mid-wait.

### Rehearse first

```bash
keris-test
```

Fake token, does not touch the server. Confirms timing works on your phone.

---

## Options

```
--tusukan N       shots per lane
--susulan SEC     follow-up after snipe, 0=off
--fire-ms MS      fire this many ms before the boundary
--lang en|id      switch language
--verify          check token
--calibrate       measure network
--selftest        rehearsal
--versi           print version
--help            full help
```

---

## How it works

**1. Precise clock.** NTP against `time.google.com`. Phone clocks are routinely
200-700 ms off — enough to lose before you start. KERIS measures the offset and
runs on `perf_counter` so system clock changes cannot move the schedule.

**2. Fire before the boundary.** Measured on-device: forward delay (`send()` to
server) is **25-55 ms**, not half the RTT. Firing at 00:00:00 lands 45 ms late,
so KERIS fires **45 ms early** and the first packet lands just after the gate.

**3. Pipeline, not sequential.** One TLS connection carries many requests at
once. Measured: **4.9-10.9 ms per request** when pipelined. 32 requests cover
~170 ms. A fresh connection per request costs 80-120 ms in handshake alone.

**4. Multiple lanes.** One connection per server IP (4 IPs = 4 connections). One
lane hitting a 429 does not stop the others.

**5. Follow-up.** After the first wave, KERIS keeps firing every ~300 ms for 15
seconds, in case quota opens gradually.

---

## Slow networks

KERIS measures the rate before firing. If 32 shots would take more than 300 ms,
it shrinks the count so they all land:

```
measure      150.2 ms/req -> 32 shots cover 4805 ms
measure      slow network: shots 32 -> 2 (fit 300 ms)
WARNING      150 ms/req too slow to win quota. Use WiFi or 4G.
```

At 150 ms/req, 32 shots take 4.8 seconds. Shot 3 onward lands after someone
already took the quota — that is spam, not sniping.

---

## Endpoints that cannot pipeline

Xiaomi runs several CDNs. European endpoints (`ams.aznl.pubproxy.lb.mi.com`,
IPs `20.157.x` / `20.47.x`) **close the connection after one response**, so
pipelining is dead there — 8 requests get 1 reply.

KERIS tests this automatically before firing:

```
lane         skipped (no pipelining): 20.157.18.26 (0/2), 20.47.97.185 (0/2)
lane         4/4 ready (1 account)
```

From Indonesia DNS returns Asian endpoints that do pipeline. If local DNS hands
out European ones, `EXTRA_IPS` adds Asian A-records as fallback and the filter
drops what fails.

---

## Getting a token

The token is the `new_bbs_serviceToken` cookie from the Mi Community app. It is
valid for **one day**, so capture it on the day.

### 1. Install Reqable (recommended)

Reqable reads the app's HTTPS traffic so the cookie line can be copied.

1. Install **Reqable** from Play Store or https://reqable.com (APK).
2. First run → allow the **VPN** prompt (record mode = VPN, this is the default).
   This is a *local* VPN on the phone; it does not route through any server.
3. Open the side drawer (☰) → **Certificate Management** → **Install Root
   Certificate** → **Export / save the CA file**.
4. Install it as a CA: Settings → **Security** → **More security settings** →
   **Encryption & credentials** → **Install a certificate** → **CA certificate**
   → pick the Reqable file → name it `reqable`. Android shows a warning —
   confirm.

### 2. Make Mi Community trust the certificate

Apps targeting Android 7+ only trust **system** certificates, so a plain user
certificate may fail with SSL errors. Two ways:

- **Rooted phone (most reliable):** in Reqable → Certificate Management →
  install the root certificate **to the system store** (requires root), or use
  the Magisk module *Always Trust User Certs*.
- **No root:** try the user certificate first. If Mi Community pages fail to
  load while capturing, that is the cause — a rooted path is the workaround.

### 3. Capture

1. Reqable → **Enhanced Mode** on, **Record Mode = VPN**.
2. Target apps: tick **Mi Community** only (less noise).
3. Press the capture button (dot) — VPN permission → **Allow**.
4. Open **Mi Community** → **Profile** → **Unlock Bootloader**.
5. Back to Reqable: find `POST https://sgp-api.buy.mi.com/bbs/api/global/apply/bl-auth`.
6. Open the request → **Request** tab → copy the whole **Cookie** header value.

KERIS only needs the `new_bbs_serviceToken=...` part — `versionCode` and
`deviceId` are rebuilt automatically. Pasting the whole line is also fine.

If nothing appears: check the capture dot is on, VPN mode is selected, filters
are cleared, and open www.google.com in a browser — if that appears in Reqable,
the app filter or Enhanced Mode is the problem (per Reqable's Android FAQ).

If the **Unlock bootloader** menu is missing, set the app region to **Global**.

**Turn off capture and any VPN before firing.** A local VPN adds 50-150 ms and
destroys the precision.

### Optional capture apps

Reqable above is the recommended one. Any of these work the same way if you
already have them: **PCAPdroid** (Play Store, no root for user-certs),
**HTTP Toolkit** (Android app), or any MITM proxy with a system CA. The steps
are always: install CA → capture → copy the `Cookie:` line of the
`bl-auth` request.

---

## Response codes

State (`bl-switch/state`):

| `is_pass` / `button_state` | Meaning |
|---|---|
| `1` / – | Already permitted |
| `4` / `1` | Ready to snipe |
| `4` / `2` | Blocked until `deadline` |
| `4` / `3` | Account younger than 30 days |

Apply (`apply/bl-auth`):

| `apply_result` | Meaning |
|---|---|
| `1` | **Approved** — `deadline` ~1 year |
| `2` | Already held / account error |
| `3` | Quota gone — `deadline` tomorrow |
| `6` | Server busy |

`apply_result: 3` can appear even when the backend already approved ("silent
approval"). If a shot lands in the opening second, check by binding the account
on the phone.

---

## After you get the ticket

Permission is **not** active yet:

1. **On the phone** — Developer options → Status Mi Unlock → **Add account and
   device**. Requires **WiFi off, mobile data on**, SIM with data left. Success
   shows *"Added successfully"*.
2. **On a PC** — download [Mi Unlock Tool](https://unlock.update.miui.com), sign
   in with the **same** Xiaomi account.
3. Phone to **fastboot** (Volume Down + Power), plug in USB, click **Unlock**.
4. Expect *"Couldn't unlock. Please unlock 168 hours later"*. **Normal.** Wait 7
   days, repeat steps 3-4.

During those 7 days: **no factory reset**, **no signing out the Xiaomi account**,
**no removing the old SIM**. Any of those resets the 168-hour timer.

> Unlocking the bootloader **wipes the phone**. Back up before clicking Unlock.
> "Find device" stops working once the bootloader is open.

---

## Files

```
keris.py     the sniper
i18n.py      English + Indonesian strings
install.sh   Termux installer
```

Internal modules:

| Part | Job |
|---|---|
| `Clock` | NTP clock on `perf_counter`, re-sync without jumps |
| `Laras` | one TLS socket, pre-warmed, fires the burst |
| `Sergap` | owns the lanes, calibrates, reports |
| `ntp_query` / `best_ntp` | lowest-delay sample under a deadline |

---

## Technical notes

- **Cookie** stays URL-encoded. Do not decode it.
- **deviceId** is 40 hex, generated per lane. The server does not validate it
  (tested: real ID, random ID, no ID — all 200).
- **ALPN** is forced to `http/1.1`. HTTP/2 needs `:authority` instead of `host`
  and 400s otherwise.
- **NTP** is capped by `budget_s`. Uncapped, one dead server at 2 s timeout times
  nine rounds burns 6.9 s right before the shot.
- **Final resync** is skipped when under 2.5 s remain.
- **NTP samples are filtered**: offsets beyond ±5 s or delays outside 0-2 s are
  dropped. Without it one corrupt packet shifted the clock 126 years and ruined
  the whole schedule.

---

## Limits

- Needs Python 3.6+ (stdlib only, no `pip install`).
- Tested on Android 16/Termux. Android 7-15 not tested on real hardware, but no
  API changed across that range.
- Location decides the outcome. From Indonesia RTT is ~40 ms; from Europe
  ~166 ms and its CDN endpoints cannot pipeline. **A phone in Indonesia is the
  fastest path** — a PC/VPS is only a spare.
- Daily quota can vanish in under 50 ms. 128 shots in 200 ms is already max; with
  thousands of competitors, the closest path to Singapore still wins.
- Networks under 60 ms/req (3G/2G) almost always lose — KERIS warns instead of
  failing silently.
- Tokens last one day.
- Xiaomi can patch the endpoint any time.

---

## License

**GPL-3.0** — see `LICENSE`. Copyright (C) 2026 Ds Project.

### Attribution

KERIS was built by measuring the protocol itself, not by copying code. The
starting reference was [mchrbl-cli](https://github.com/ProjectRedis/mchrbl-cli)
(`herorbl.py`, GPL-3.0): it showed which endpoint the Mi Community app calls and
which headers it sends. KERIS is GPL-3.0 for that reason.

Measured against that reference — 1093 vs 968 lines, and only **49 lines
identical**, of which 20 are `import` statements and 5 are HTTP header names.
Both programs imitate the same official app, so those parts cannot differ.

Both are raw-socket, stdlib-only, NTP-synced snipers. The differences are
strategic:

| | herorbl | KERIS |
|---|---|---|
| Attack shape | symmetric bracket around the boundary (offset −b..+b per hero, `BRACKET_FACTOR=0.8`) | forward-only, staggered after the boundary |
| Connections | one fresh socket per shot, `Connection: close` | one keep-alive socket, 32 requests pipelined |
| Timing | 5-ping weighted median before the run, then fixed offsets + random jitter 1-8 ms | recomputed from a live RTT right before firing; each lane fires forward |
| Sweep window | half the shots land before the boundary and fail | nothing lands before the boundary by construction |
| Network-aware | no | shrinks shot count on slow links, drops CDN endpoints that cannot pipeline |
| `deviceId` | 39 hex | 40 hex, from a real capture |
| Language | one | English + Indonesian, chosen on first run |

**Why forward-only wins.** herorbl spreads offsets across the bracket — with the
example `[-70, -23, 23, 70]` ms, half your shots sit *before* `00:00:00` and fail
before the quota opens. KERIS fires the first shot to land `−1..−5 ms` before the
boundary, then staggers the rest forward. Every KERIS shot has a chance.

Built from public protocol research. Every timing number was measured on a
Redmi Note 13 Pro 5G / Telkomsel LTE.

---

## Bahasa Indonesia

Installer dan script menanyakan bahasa sekali di awal — pilih `2` untuk
Indonesia. Semua output, help, dan prompt ikut bahasa itu. Ganti kapan saja
dengan `keris --lang id` atau `keris --lang en`.

Panduan lengkap berbahasa Indonesia ada di dalam `keris-help` setelah installer
selesai.
