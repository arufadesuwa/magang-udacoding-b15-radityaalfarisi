from datetime import datetime

JENIS_VALID = ("pemasukan", "pengeluaran")


def validasi_tanggal(nilai: str) -> str:
    """Pastikan format tanggal sesuai YYYY-MM-DD."""
    teks = nilai.strip()
    try:
        datetime.strptime(teks, "%Y-%m-%d")
        return teks
    except ValueError as err:
        raise ValueError("Format tanggal harus YYYY-MM-DD (contoh: 2026-11-27).") from err


def validasi_bulan(nilai: str) -> str:
    """Pastikan format bulan sesuai YYYY-MM."""
    teks = nilai.strip()
    try:
        datetime.strptime(teks, "%Y-%m")
        return teks
    except ValueError as err:
        raise ValueError("Format bulan harus YYYY-MM (contoh: 2026-11).") from err


def format_rupiah(nominal: float) -> str:
    """Format angka menjadi string Rupiah, contoh: Rp 50.000."""
    return f"Rp {nominal:,.0f}".replace(",", ".")


class Transaksi:
    """Merepresentasikan satu data transaksi keuangan."""

    def __init__(
        self,
        id: int,
        tanggal: str,
        kategori: str,
        keterangan: str,
        jenis: str,
        nominal: float,
    ) -> None:
        self.id = id
        self.tanggal = validasi_tanggal(tanggal)
        self.kategori = kategori.strip()
        self.keterangan = keterangan.strip()
        self.jenis = jenis.strip().lower()
        if self.jenis not in JENIS_VALID:
            raise ValueError(f"Jenis harus salah satu dari: {', '.join(JENIS_VALID)}")
        if nominal <= 0:
            raise ValueError("Nominal harus lebih besar dari 0.")
        self.nominal = float(nominal)
