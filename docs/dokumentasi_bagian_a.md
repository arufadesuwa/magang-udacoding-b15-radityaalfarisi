# Dokumentasi Bagian A - Setup Tools & Git/GitHub (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧

## 1. Tools & Akun
- **Editor Kode:** Menggunakan **Zed** sebagai code editor utama.
- **Jupyter Lab:** Dijalankan menggunakan `uv`:
  ```bash
  uv run --with jupyter jupyter lab
  ```
  Kemudian diakses melalui browser di `http://localhost:8888/lab`.
- **Akun Kaggle:** [kaggle.com/radityaalfarisi](https://www.kaggle.com/radityaalfarisi)

## 2. Virtual Environment & Manajemen Dependensi (`uv`)
Untuk mengelola proyek dan virtual environment Python, saya menggunakan `uv` dengan alur berikut:
1. Inisialisasi proyek:
   ```bash
   uv init
   ```
2. Membuat virtual environment:
   ```bash
   uv venv
   ```
3. Menginstal paket/dependensi:
   ```bash
   uv add <nama-paket>
   # atau
   uv pip install <nama-paket>
   ```
4. Mengecek daftar paket terpasang dan mengekspornya ke `requirements.txt`:
   ```bash
   uv pip freeze
   uv export --format requirements-txt -o requirements.txt
   ```
