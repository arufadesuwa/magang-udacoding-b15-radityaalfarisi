from datetime import date

from models import (
    JENIS_VALID,
    Transaksi,
    format_rupiah,
    validasi_bulan,
    validasi_tanggal,
)
from storage import Pencatat


def pilih_menu(judul: str, opsi: list[str]) -> int:
    """Tampilkan daftar menu bernomor dan kembalikan indeks pilihan (mulai dari 0)."""
    print(f"\n=== {judul} ===")
    for i, label in enumerate(opsi, start=1):
        print(f"{i}. {label}")

    while True:
        pilihan = input(f"Pilih (1-{len(opsi)}): ").strip()
        try:
            angka = int(pilihan)
            if 1 <= angka <= len(opsi):
                return angka - 1
            print(f"Masukkan angka antara 1 sampai {len(opsi)}.")
        except ValueError:
            print("Input harus berupa angka.")


def input_teks_wajib(prompt_teks: str) -> str:
    """Meminta input teks yang tidak boleh kosong."""
    while True:
        nilai = input(f"{prompt_teks}: ").strip()
        if nilai:
            return nilai
        print("Input tidak boleh kosong.")


def input_nominal() -> float:
    """Meminta input nominal angka positif."""
    while True:
        nilai = input("Nominal (Rp): ").strip()
        try:
            angka = float(nilai.replace(",", ""))
            if angka <= 0:
                print("Nominal harus lebih besar dari 0.")
                continue
            return angka
        except ValueError:
            print("Nominal harus berupa angka yang valid.")


def input_tanggal() -> str:
    """Meminta input tanggal dengan format YYYY-MM-DD."""
    hari_ini = date.today().isoformat()
    while True:
        nilai = input(f"Tanggal (YYYY-MM-DD) [{hari_ini}]: ").strip()
        if not nilai:
            nilai = hari_ini
        try:
            return validasi_tanggal(nilai)
        except ValueError as err:
            print(err)


def tampilkan_tabel(daftar: list[Transaksi], judul: str = "Daftar Transaksi") -> None:
    """Menampilkan daftar transaksi dalam bentuk tabel sederhana."""
    if not daftar:
        print("Belum ada data transaksi.")
        return

    print(f"\n--- {judul} ---")
    print(f"{'ID':<4} {'Tanggal':<12} {'Jenis':<12} {'Kategori':<15} {'Keterangan':<20} {'Nominal':>15}")
    print("-" * 82)
    for t in daftar:
        print(
            f"{t.id:<4} {t.tanggal:<12} {t.jenis:<12} "
            f"{t.kategori:<15} {t.keterangan:<20} {format_rupiah(t.nominal):>15}"
        )


def menu_tambah(pencatat: Pencatat) -> None:
    """Menu untuk menambah transaksi baru."""
    print("\n=== Tambah Transaksi ===")
    tanggal = input_tanggal()
    kategori = input_teks_wajib("Kategori (cth: Makan, Gaji, Transport)")
    keterangan = input_teks_wajib("Keterangan")

    opsi_jenis = list(JENIS_VALID)
    indeks_jenis = pilih_menu("Pilih Jenis Transaksi", opsi_jenis)
    jenis = opsi_jenis[indeks_jenis]

    nominal = input_nominal()

    transaksi = pencatat.tambah(
        tanggal=tanggal,
        kategori=kategori,
        keterangan=keterangan,
        jenis=jenis,
        nominal=nominal,
    )
    print(f"Berhasil ditambahkan (ID: {transaksi.id}).")


def menu_lihat_semua(pencatat: Pencatat) -> None:
    """Menu untuk menampilkan semua transaksi."""
    tampilkan_tabel(pencatat.semua(), "Semua Transaksi")


def menu_filter(pencatat: Pencatat) -> None:
    """Menu untuk menyaring transaksi berdasarkan kategori atau bulan."""
    print("\n=== Filter Transaksi ===")
    kategori = input("Filter kategori (kosongkan jika semua): ").strip() or None

    bulan = None
    while True:
        input_bln = input("Filter bulan YYYY-MM (kosongkan jika semua): ").strip()
        if not input_bln:
            break
        try:
            bulan = validasi_bulan(input_bln)
            break
        except ValueError as err:
            print(err)

    hasil = pencatat.filter(kategori=kategori, bulan=bulan)
    tampilkan_tabel(hasil, "Hasil Filter Transaksi")


def menu_ringkasan(pencatat: Pencatat) -> None:
    """Menu untuk menampilkan ringkasan pemasukan, pengeluaran, dan saldo."""
    print("\n=== Ringkasan Keuangan ===")
    bulan = None
    while True:
        input_bln = input("Bulan YYYY-MM (kosongkan untuk semua): ").strip()
        if not input_bln:
            break
        try:
            bulan = validasi_bulan(input_bln)
            break
        except ValueError as err:
            print(err)

    data = pencatat.ringkasan(bulan=bulan)
    judul = f"Ringkasan ({bulan})" if bulan else "Ringkasan Keseluruhan"
    print(f"\n--- {judul} ---")
    print(f"Jumlah Transaksi     : {data['jumlah_transaksi']}")
    print(f"Total Pemasukan      : {format_rupiah(data['total_pemasukan'])}")
    print(f"Total Pengeluaran    : {format_rupiah(data['total_pengeluaran'])}")
    print(f"Saldo                : {format_rupiah(data['saldo'])}")
    print(f"Pengeluaran Terbesar : {data['kategori_terbesar'] or '-'}")


def menu_hapus(pencatat: Pencatat) -> None:
    """Menu untuk menghapus transaksi berdasarkan ID."""
    daftar = pencatat.semua()
    if not daftar:
        print("Belum ada transaksi untuk dihapus.")
        return

    tampilkan_tabel(daftar, "Pilih ID Transaksi yang Akan Dihapus")
    while True:
        input_id = input("Masukkan ID transaksi (atau 0 untuk batal): ").strip()
        try:
            id_target = int(input_id)
            break
        except ValueError:
            print("ID harus berupa angka.")

    if id_target == 0:
        print("Penghapusan dibatalkan.")
        return

    if pencatat.hapus(id_target):
        print(f"Transaksi ID {id_target} berhasil dihapus.")
    else:
        print(f"Transaksi dengan ID {id_target} tidak ditemukan.")


def menu_export(pencatat: Pencatat) -> None:
    """Menu untuk mengekspor ringkasan bulanan ke file .txt."""
    print("\n=== Export Ringkasan Bulanan ===")
    bulan_sekarang = date.today().strftime("%Y-%m")
    while True:
        input_bln = input(f"Bulan (YYYY-MM) [{bulan_sekarang}]: ").strip()
        if not input_bln:
            input_bln = bulan_sekarang
        try:
            bulan = validasi_bulan(input_bln)
            break
        except ValueError as err:
            print(err)

    path_file = pencatat.export_bulanan(bulan)
    print(f"Ringkasan berhasil diekspor ke: {path_file}")


def main() -> None:
    """Fungsi utama untuk menjalankan loop menu aplikasi."""
    pencatat = Pencatat()
    daftar_menu = [
        "Tambah Transaksi",
        "Lihat Semua Transaksi",
        "Filter Transaksi",
        "Ringkasan Keuangan",
        "Hapus Transaksi",
        "Export Ringkasan Bulanan (.txt)",
        "Keluar",
    ]

    while True:
        pilihan = pilih_menu("Pencatat Keuangan Harian", daftar_menu)

        if pilihan == 0:
            menu_tambah(pencatat)
        elif pilihan == 1:
            menu_lihat_semua(pencatat)
        elif pilihan == 2:
            menu_filter(pencatat)
        elif pilihan == 3:
            menu_ringkasan(pencatat)
        elif pilihan == 4:
            menu_hapus(pencatat)
        elif pilihan == 5:
            menu_export(pencatat)
        elif pilihan == 6:
            print("Terima kasih! Sampai jumpa.")
            break


if __name__ == "__main__":
    main()
