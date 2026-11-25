from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, get_args

JenisTransaksi = Literal["pemasukan", "pengeluaran"]
JENIS_VALID: tuple[JenisTransaksi, ...] = get_args(JenisTransaksi)


def validasi_tanggal(tanggal: str) -> str:
    """Validasi format tanggal YYYY-MM-DD dan kembalikan string yang sudah dirapikan."""
    nilai = tanggal.strip()
    try:
        datetime.strptime(nilai, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(
            "Format tanggal tidak valid. Gunakan format YYYY-MM-DD (contoh: 2026-11-25)."
        ) from exc
    return nilai


def validasi_bulan(bulan: str) -> str:
    """Validasi format bulan YYYY-MM dan kembalikan string yang sudah dirapikan."""
    nilai = bulan.strip()
    try:
        datetime.strptime(nilai, "%Y-%m")
    except ValueError as exc:
        raise ValueError(
            "Format bulan tidak valid. Gunakan format YYYY-MM (contoh: 2026-11)."
        ) from exc
    return nilai


def format_rupiah(nominal: float) -> str:
    """Format angka ke representasi mata uang Rupiah (contoh: Rp 1.500.000)."""
    negatif = nominal < 0
    nilai_bulat = round(abs(nominal))
    angka_terformat = f"{nilai_bulat:,}".replace(",", ".")
    prefix = "-Rp " if negatif else "Rp "
    return f"{prefix}{angka_terformat}"


@dataclass
class Transaksi:
    """Merepresentasikan satu entri transaksi keuangan."""

    tanggal: str
    kategori: str
    keterangan: str
    jenis: JenisTransaksi | str
    nominal: float

    def __post_init__(self) -> None:
        self.tanggal = validasi_tanggal(self.tanggal)

        self.kategori = self.kategori.strip()
        if not self.kategori:
            raise ValueError("Kategori tidak boleh kosong.")

        self.keterangan = self.keterangan.strip()
        if not self.keterangan:
            raise ValueError("Keterangan tidak boleh kosong.")

        self.jenis = self.jenis.strip().lower()
        if self.jenis not in JENIS_VALID:
            raise ValueError("Jenis transaksi harus 'pemasukan' atau 'pengeluaran'.")

        try:
            nilai_nominal = float(self.nominal)
        except (TypeError, ValueError) as exc:
            raise ValueError("Nominal harus berupa angka.") from exc

        if not math.isfinite(nilai_nominal) or nilai_nominal <= 0:
            raise ValueError("Nominal harus berupa angka positif lebih dari 0.")

        self.nominal = nilai_nominal

    def to_dict(self) -> dict[str, str]:
        """Konversi transaksi ke dictionary string untuk penulisan CSV."""
        nominal_str = (
            str(int(self.nominal))
            if self.nominal.is_integer()
            else f"{self.nominal:.2f}"
        )
        return {
            "tanggal": self.tanggal,
            "kategori": self.kategori,
            "keterangan": self.keterangan,
            "jenis": self.jenis,
            "nominal": nominal_str,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> Transaksi:
        """Buat objek Transaksi dari satu baris dictionary CSV."""
        try:
            nominal_str = str(data["nominal"]).strip()
            nominal = float(nominal_str)
        except KeyError as exc:
            raise ValueError(f"Kolom CSV tidak lengkap: {exc}") from exc
        except ValueError as exc:
            raise ValueError("Nominal pada file CSV bukan angka valid.") from exc

        return cls(
            tanggal=str(data.get("tanggal", "")),
            kategori=str(data.get("kategori", "")),
            keterangan=str(data.get("keterangan", "")),
            jenis=str(data.get("jenis", "")),
            nominal=nominal,
        )
