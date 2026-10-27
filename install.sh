#!/data/data/com.termux/files/usr/bin/env bash
# keris — pemasang satu perintah untuk Termux
set -eu

RAW=https://raw.githubusercontent.com/Ds-Project-All/keris/main
DIR=$HOME/keris
PY=$DIR/keris.py
BIN=${PREFIX:-/data/data/com.termux/files/usr}/bin

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
for f in keris.py i18n.py; do
  if ! curl -fL --progress-bar -o "$DIR/$f" "$RAW/$f"; then
    warn "gagal mengunduh $f. periksa koneksi lalu ulangi."
    exit 1
  fi
done
for f in README.md LICENSE; do
  curl -fsL -o "$DIR/$f" "$RAW/$f" || rm -f "$DIR/$f"
done
chmod +x "$PY"

# ── 4. perintah ───────────────────────────────────────────────────────
# Pakai skrip pembungkus di $PREFIX/bin, bukan alias: alias hanya terbaca
# saat shell dimulai ulang, jadi `keris` gagal "command not found" sampai
# Termux ditutup. File di PATH langsung jalan di sesi yang sedang aktif.
say "memasang perintah keris"
mkdir -p "$BIN"
put() {                       # put <nama> <argumen...>
  n=$1; shift
  printf '#!/data/data/com.termux/files/usr/bin/sh\nexec python3 %s %s "$@"\n' \
    "$PY" "$*" > "$BIN/$n"
  chmod +x "$BIN/$n"
}
put keris
put keris-cek --verify
put keris-cal --calibrate
put keris-test --selftest
put keris-help --help

# keris-update tidak menjalankan python: ia menjalankan pemasang lagi
cat > "$BIN/keris-update" <<EOF
#!/data/data/com.termux/files/usr/bin/sh
curl -fsSL $RAW/install.sh | bash
EOF
chmod +x "$BIN/keris-update"

# bersihkan alias lama yang sekarang berlebih / menunjuk file hilang
for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
  [ -e "$rc" ] || continue
  sed -i '/^alias keris/d' "$rc" 2>/dev/null || true
  while IFS= read -r line; do
    tgt=$(printf '%s' "$line" | sed -n "s/.*python3 \([^ ']*\).*/\1/p")
    [ -n "$tgt" ] || continue
    [ -f "$tgt" ] && continue
    sed -i "\|^$(printf '%s' "$line" | sed 's/[][\.*^$/]/\\&/g')$|d" "$rc" 2>/dev/null || true
  done <<EOT
$(grep '^alias ' "$rc" 2>/dev/null || true)
EOT
done
hash -r 2>/dev/null || true

# ── 5. wake-lock ──────────────────────────────────────────────────────
if command -v termux-wake-lock >/dev/null 2>&1; then
  say "mengaktifkan wake-lock"
  termux-wake-lock 2>/dev/null || warn "wake-lock ditolak — izinkan notifikasi Termux:API"
else
  warn "termux-api belum ada — Android bisa membekukan Termux saat menunggu"
  warn "  pasang: pkg install termux-api  (lalu app Termux:API dari F-Droid)"
fi

# ── 6. storage (opsional) ─────────────────────────────────────────────
if [ ! -d "$HOME/storage" ] && command -v termux-setup-storage >/dev/null 2>&1; then
  say "minta izin storage (boleh ditolak, tidak wajib)"
  termux-setup-storage 2>/dev/null || true
fi

# ── 7. buktikan jalan ─────────────────────────────────────────────────
if ! python3 "$PY" --versi >/dev/null 2>&1; then
  warn "GAGAL: keris.py tidak bisa dijalankan"
  exit 1
fi
if ! command -v keris >/dev/null 2>&1; then
  warn "GAGAL: perintah keris tidak masuk PATH ($BIN)"
  exit 1
fi

echo
say "selesai — $(python3 "$PY" --versi)"
echo
say "langsung bisa dipakai sekarang:"
echo "   keris-cal      ukur jaringan (lakukan sekali)"
echo "   keris-cek      cek token"
echo "   keris          sergap"
echo "   keris-update   ambil versi terbaru"
echo
say "tanpa perintah: python3 $PY"
