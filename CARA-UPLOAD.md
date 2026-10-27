# Cara Upload ke GitHub

Repo sudah siap di:
```
C:\Users\Ds Project\AppData\Local\Temp\keris_repo
```

Sudah ada commit `ba19f68`. Tinggal push. Pilih **satu** cara.

---

## Cara A — lewat website GitHub (paling mudah, tanpa terminal)

Cocok kalau kamu tidak mau menyentuh git lagi.

### 1. Buat repo kosong

1. Buka https://github.com/new
2. **Repository name**: `keris`
3. **Description**: `Presisi sergap tiket Unlock Bootloader Xiaomi`
4. Pilih **Public**
5. **JANGAN** centang "Add a README file", "Add .gitignore", atau "Choose a license"
   — repo harus benar-benar kosong, kalau tidak nanti bentrok saat push
6. Klik **Create repository**

### 2. Ambil URL repo

Setelah dibuat, GitHub menampilkan halaman "Quick setup". Copy URL yang bentuknya:
```
https://github.com/USERNAME/keris.git
```

### 3. Push dari PC

Buka **Git Bash** (bukan CMD), lalu:

```bash
cd "/c/Users/Ds Project/AppData/Local/Temp/keris_repo"

git remote add origin https://github.com/USERNAME/keris.git
git branch -M main
git push -u origin main
```

Ganti `USERNAME` dengan username GitHub kamu.

### 4. Login saat diminta

Git akan membuka jendela browser (Git Credential Manager). Klik **Sign in with
your browser**, izinkan, selesai. Tidak perlu ketik password.

Kalau muncul prompt terminal minta username/password: **password GitHub tidak
berlaku**. Harus Personal Access Token — lihat bagian bawah.

---

## Cara B — pakai GitHub CLI (kalau mau sekali perintah)

`gh` belum terpasang di PC kamu. Kalau mau pakai:

```bash
winget install --id GitHub.cli
```

Tutup dan buka ulang terminal, lalu:

```bash
gh auth login
```

Pilih: **GitHub.com** → **HTTPS** → **Login with a web browser** → copy kode →
Enter.

Setelah login:

```bash
cd "/c/Users/Ds Project/AppData/Local/Temp/keris_repo"
gh repo create keris --public --source=. --push \
  --description "Presisi sergap tiket Unlock Bootloader Xiaomi"
```

Selesai — repo dibuat dan di-push sekaligus.

---

## Kalau diminta password

GitHub tidak menerima password akun sejak 2021. Pakai **Personal Access Token**:

1. Buka https://github.com/settings/tokens?type=beta
2. **Generate new token**
3. **Token name**: `keris-push`
4. **Expiration**: 30 days
5. **Repository access**: pilih **Only select repositories** → `keris`
6. **Permissions** → **Repository permissions** → **Contents**: **Read and write**
7. **Generate token**
8. Copy token (`github_pat_...`) — **hanya muncul sekali**

Saat git minta password, tempel token itu (bukan password akun).
Saat minta username, isi username GitHub kamu.

Simpan token di tempat aman. Kalau hilang, harus generate ulang.

---

## Setelah berhasil

Cek di browser: `https://github.com/USERNAME/keris`

Yang harus terlihat:
- `keris.py`, `README.md`, `LICENSE`, `.gitignore`, `.gitattributes`
- README tampil rapi dengan tabel
- License badge "MIT" di sidebar kanan

---

## Update berikutnya

Kalau nanti ada perubahan file:

```bash
cd "/c/Users/Ds Project/AppData/Local/Temp/keris_repo"
git add -A
git commit -m "jelaskan perubahannya"
git push
```

---

## Kalau gagal

**`remote origin already exists`**
```bash
git remote set-url origin https://github.com/USERNAME/keris.git
```

**`failed to push some refs` / `rejected`**
Repo di GitHub tidak kosong. Hapus repo di GitHub, buat ulang tanpa centang
apa pun.

**`Authentication failed`**
Token salah atau kedaluwarsa. Generate token baru, lalu:
```bash
git credential-manager erase
```
lalu push lagi.

**`src refspec main does not match any`**
Belum ada commit. Jalankan `git log --oneline` — kalau kosong, commit dulu.

**File keris.py tidak bisa dieksekusi di Linux setelah clone**
```bash
chmod +x keris.py
```
Git tidak menyimpan permission executable dengan sempurna di semua platform.
