#!/data/data/com.termux/files/usr/bin/env bash
# install.sh — satu perintah, langsung pakai.
set -eu

RAW=https://raw.githubusercontent.com/dhimesta090418-crypto/keris/main
DIR=$HOME/keris

say() { printf '>> %s\n' "$*"; }

# 1. python
if ! command -v python3 >/dev/null 2>&1; then
  say "python belum ada, memasang..."
  pkg update -y && pkg install -y python
fi

# 2. curl
if ! command -v curl >/dev/null 2>&1; then
  say "curl belum ada, memasang..."
  pkg install -y curl
fi

# 3. unduh
say "mengunduh keris.py..."
mkdir -p "$DIR"
curl -fL --progress-bar -o "$DIR/keris.py" "$RAW/keris.py"

# 4. pendamping: README + LICENSE, tidak fatal kalau gagal
for f in README.md LICENSE; do
  curl -fsL -o "$DIR/$f" "$RAW/$f" || rm -f "$DIR/$f"
done

chmod +x "$DIR/keris.py"

# 5. wake-lock, opsional
if ! command -v termux-wake-lock >/dev/null 2>&1; then
  say "termux-api belum ada (opsional, tapi disarankan)"
  say "  pasang: pkg install termux-api"
fi

# 6. periksa hasilnya benar-benar jalan
if ! python3 "$DIR/keris.py" --versi >/dev/null 2>&1; then
  say "GAGAL: keris.py tidak bisa dijalankan"
  exit 1
fi

say "selesai — $(python3 "$DIR/keris.py" --versi)"
echo
say "pakai:"
echo "   cd ~/keris"
echo "   python3 keris.py --calibrate    # ukur jaringan"
echo "   python3 keris.py                # sergap"
echo
say "atau tanpa cd, dari mana saja:"
echo "   python3 ~/keris/keris.py"
