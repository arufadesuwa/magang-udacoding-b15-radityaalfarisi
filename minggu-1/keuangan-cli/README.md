# Pencatat Keuangan CLI (｡•̀ᴗ-)✧

Aplikasi pencatat keuangan pribadi berbasis terminal (CLI) dengan antarmuka interaktif menggunakan `rich` dan penyimpanan data lokal berbasis CSV.

## Fitur

- **Tambah Transaksi**: Mencatat pemasukan atau pengeluaran dengan validasi tanggal (`YYYY-MM-DD`), kategori, keterangan, jenis transaksi, dan nominal positif.
- **Lihat Semua Transaksi**: Menampilkan seluruh transaksi dalam tabel terformat lengkap dengan warna pembeda dan format mata uang Rupiah (`Rp`).
- **Filter Transaksi**: Menyaring daftar transaksi berdasarkan kategori (case-insensitive) dan/atau bulan (`YYYY-MM`).
- **Ringkasan Keuangan**: Menghitung jumlah transaksi, total pemasukan, total pengeluaran, saldo, serta kategori pengeluaran terbesar (keseluruhan atau per bulan).
- **Hapus Transaksi**: Menghapus transaksi melalui menu pilihan interaktif dengan konfirmasi.
- **Export Ringkasan Bulanan**: Mengekspor ringkasan dan daftar transaksi bulan tertentu ke file `.txt` di folder `exports/`.
- **Navigasi Interaktif**: Mendukung navigasi menu menggunakan tombol panah `↑`/`↓` (atau `j`/`k`) dan `Enter`, dengan fallback input angka jika dijalankan pada mode non-TTY.

## Prasyarat

- Python `>= 3.13`
- [uv](https://docs.astral.sh/uv/) (opsional, direkomendasikan) atau `pip`

## Instalasi & Menjalankan

Masuk ke direktori proyek:

```bash
cd minggu-1/keuangan-cli
```

### Menggunakan `uv`

```bash
uv sync
uv run python main.py
```

### Menggunakan `pip` / `venv`

```bash
python -m venv .venv
source .venv/bin/activate
pip install rich>=15.0.0
python main.py
```

## Struktur Proyek

```text
keuangan-cli/
├── main.py          # Entry point dan antarmuka menu CLI interaktif
├── models.py        # Model Transaksi, validasi input, dan format Rupiah
├── storage.py       # Kelas Pencatat untuk baca/tulis CSV, filter, ringkasan, dan ekspor
├── pyproject.toml   # Konfigurasi proyek dan dependensi
├── data/            # Lokasi default penyimpanan data (data/transaksi.csv)
└── exports/         # Lokasi default hasil ekspor ringkasan (.txt)
```

## Penyimpanan & Ekspor Data

- **Data Transaksi**: Disimpan secara otomatis ke `data/transaksi.csv` dengan kolom `tanggal,kategori,keterangan,jenis,nominal`.
- **Hasil Ekspor**: Disimpan ke `exports/ringkasan_<YYYY-MM>.txt`.
