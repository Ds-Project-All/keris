#!/data/data/com.termux/files/usr/bin/env bash
# keris — pemasang satu perintah untuk Termux
set -eu

RAW=https://raw.githubusercontent.com/dhimesta090418-crypto/keris/main
DIR=$HOME/keris
PY=$DIR/keris.py

say()  { printf '>> %s\n' "$*"; }
warn() { printf '!! %s\n' "$*"; }

say "memasang keris..."

# ── 1. python ─────────────────────────────────────────────────────────
if ! command -v python3 >/dev/null 2>&1; then
  say "python belum ada — memasang (perlu beberapa menit)"
  pkg update -y && pkg install -y python
fi

# ── 2. curl ───────────────────────────────────────────────────────────
if ! command -v curl >/dev/null 2>&1; then
  say "curl belum ada — memasang"
  pkg install -y curl
fi

# ── 3. unduh ──────────────────────────────────────────────────────────
say "mengunduh keris.py"
mkdir -p "$DIR"
if ! curl -fL --progress-bar -o "$PY" "$RAW/keris.py"; then
  warn "gagal mengunduh. periksa koneksi lalu ulangi."
  exit 1
fi
for f in README.md LICENSE; do
  curl -fsL -o "$DIR/$f" "$RAW/$f" || rm -f "$DIR/$f"
done
chmod +x "$PY"

# ── 4. alias ──────────────────────────────────────────────────────────
# Alias lama (ubl-go, ublx.py, herorbl.py) dibuang: filenya sudah tidak ada
# dan cuma bikin "command not found".
say "memasang perintah keris"
for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
  [ -e "$rc" ] || continue
  # buang alias lama yang menunjuk file hilang (mis. ublx.py sudah dihapus).
  # Alias yang targetnya masih ada dibiarkan.
  while IFS= read -r line; do
    tgt=$(printf '%s' "$line" | sed -n "s/.*python3 \([^ ']*\).*/\1/p")
    if [ -n "$tgt" ] && [ ! -f "$tgt" ]; then
      sed -i "\|^$(printf '%s' "$line" | sed 's/[][\.*^$/]/\\&/g')$|d" "$rc" 2>/dev/null || true
    fi
  done <<EOF
$(grep '^alias ' "$rc" 2>/dev/null || true)
EOF
  # pasang yang baru, jangan dobel
  for a in keris keris-cek keris-cal keris-test keris-update; do
    sed -i "/^alias $a=/d" "$rc" 2>/dev/null || true
  done
  {
    echo "alias keris='python3 $PY'"
    echo "alias keris-cek='python3 $PY --verify'"
    echo "alias keris-cal='python3 $PY --calibrate'"
    echo "alias keris-test='python3 $PY --selftest'"
    echo "alias keris-update='curl -fsSL $RAW/install.sh | bash'"
  } >> "$rc"
done

# ── 5. wake-lock ──────────────────────────────────────────────────────
# Tanpa ini Android bisa membekukan Termux saat menunggu 3 menit — sergap
# gagal tanpa pesan. Sengaja tidak dipasang otomatis: butuh izin notifikasi,
# dan installer tidak boleh memblokir menunggu user klik Allow.
if command -v termux-wake-lock >/dev/null 2>&1; then
  say "mengaktifkan wake-lock"
  termux-wake-lock 2>/dev/null || warn "wake-lock ditolak — izinkan notifikasi Termux:API"
else
  warn "termux-api belum ada — Android bisa membekukan Termux saat menunggu"
  warn "  pasang: pkg install termux-api  (lalu pasang app Termux:API dari F-Droid)"
fi

# ── 6. storage (opsional) ─────────────────────────────────────────────
# Hanya berguna kalau nanti mau simpan log ke /sdcard. Tidak wajib.
if [ ! -d "$HOME/storage" ] && command -v termux-setup-storage >/dev/null 2>&1; then
  say "minta izin storage (boleh ditolak, tidak wajib)"
  termux-setup-storage 2>/dev/null || true
fi

# ── 7. buktikan jalan ─────────────────────────────────────────────────
if ! python3 "$PY" --versi >/dev/null 2>&1; then
  warn "GAGAL: keris.py tidak bisa dijalankan"
  exit 1
fi

echo
say "selesai — $(python3 "$PY" --versi)"
echo
say "tutup Termux, buka lagi, lalu:"
echo "   keris-cal      ukur jaringan (lakukan sekali)"
echo "   keris-cek      cek token"
echo "   keris          sergap"
echo "   keris-update   ambil versi terbaru"
echo
say "tanpa alias: python3 $PY"
