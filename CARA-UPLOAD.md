# Upload ke GitHub — pakai SSH

Kunci SSH sudah dibuat di PC ini. Tinggal didaftarkan ke GitHub, lalu push.
Tidak perlu Personal Access Token.

Repo sudah siap di:
```
C:\Users\Ds Project\AppData\Local\Temp\keris_repo
```
Branch `main`, working tree bersih.

---

## Langkah 1 — daftarkan kunci SSH ke GitHub

Buka file ini, copy **seluruh isinya** (satu baris panjang):

```
C:\Users\Ds Project\.ssh\id_ed25519.pub
```

Isinya:

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGcNRab2Lk7NwtMNnMhw38j+NdZIX4HHdxI6ddzxX7sz ds-keris@DESKTOP-1POG8AF
```

Lalu:

1. Buka https://github.com/settings/keys
2. Klik **New SSH key**
3. **Title**: `PC ds keris`
4. **Key type**: `Authentication Key`
5. **Key**: paste baris di atas
6. Klik **Add SSH key**

Kalau GitHub minta password, masukkan password akun GitHub kamu.

---

## Langkah 2 — buat repo kosong

1. Buka https://github.com/new
2. **Repository name**: `keris`
3. **Description**: `Sergap tiket Unlock Bootloader Xiaomi dari HP Android`
4. Pilih **Public**
5. **JANGAN** centang "Add a README file", "Add .gitignore", atau "Choose a license"
   — repo harus benar-benar kosong, kalau tidak nanti bentrok saat push
6. Klik **Create repository**

---

## Langkah 3 — push

Buka **Git Bash** (bukan CMD), lalu (ganti `USERNAME`):

```bash
cd "/c/Users/Ds Project/AppData/Local/Temp/keris_repo"

git remote add origin git@github.com:USERNAME/keris.git
git push -u origin main
```

Tidak ada prompt password. Kalau berhasil:

```
Enumerating objects: 12, done.
Writing objects: 100% (12/12), 8.42 KiB | 1.2 MiB/s, done.
To github.com:USERNAME/keris.git
 * [new branch]      main -> main
```

---

## Langkah 4 — cek

Buka `https://github.com/USERNAME/keris`

Yang harus terlihat: `keris.py`, `README.md`, `LICENSE`, `CARA-UPLOAD.md`,
`.gitignore`, `.gitattributes`. Badge **MIT** di sidebar kanan.

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

**`Permission denied (publickey)`**
Kunci belum terdaftar atau salah copy. Buka
https://github.com/settings/keys, pastikan baris `ssh-ed25519 AAAA...` ada
utuh. Tes:

```bash
ssh -T git@github.com
```

Harus jawab: `Hi USERNAME! You've successfully authenticated...`

**`Repository not found`**
Salah username di URL, atau repo belum dibuat. Cek:

```bash
git remote -v
```

**`remote origin already exists`**
```bash
git remote set-url origin git@github.com:USERNAME/keris.git
```

**`failed to push some refs` / `rejected`**
Repo di GitHub tidak kosong. Hapus repo di GitHub, buat ulang tanpa centang
apa pun.

**`src refspec main does not match any`**
Belum ada commit. Jalankan `git log --oneline` — kalau kosong, commit dulu.

**`Host key verification failed`**
```bash
ssh-keyscan github.com >> ~/.ssh/known_hosts
```

**File keris.py tidak bisa dieksekusi setelah clone**
```bash
chmod +x keris.py
```
Git tidak menyimpan permission executable dengan sempurna di semua platform.

---

## Catatan keamanan

File `~/.ssh/id_ed25519` (tanpa `.pub`) adalah **kunci privat**. Jangan pernah
di-copy, di-upload, atau dikirim ke siapa pun. Yang didaftarkan ke GitHub hanya
file `.pub`.

Kunci ini tidak punya passphrase — nyaman untuk push otomatis, tapi siapa pun
yang bisa membaca file itu di PC ini bisa push ke repo kamu. Kalau mau lebih
aman:

```bash
ssh-keygen -p -f ~/.ssh/id_ed25519
```

Lalu masukkan passphrase. Setelah itu setiap push akan minta passphrase
(atau simpan sekali lewat ssh-agent).
