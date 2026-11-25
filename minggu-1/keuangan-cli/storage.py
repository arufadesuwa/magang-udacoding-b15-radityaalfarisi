from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

from models import Transaksi, format_rupiah, validasi_bulan


class Pencatat:
    """Mengelola daftar transaksi, persistensi CSV, filter, ringkasan, dan ekspor."""

    FIELDNAMES = ["tanggal", "kategori", "keterangan", "jenis", "nominal"]  # noqa: RUF012

    def __init__(self, file_path: Path | str = "data/transaksi.csv") -> None:
        self.file_path = Path(file_path)
        self.transaksi: list[Transaksi] = []
        self.peringatan_muat: list[str] = []
        self.muat_data()

    def muat_data(self) -> None:
        """Muat transaksi dari file CSV jika tersedia."""
        self.transaksi.clear()
        self.peringatan_muat.clear()

        if not self.file_path.exists():
            return

        try:
            with self.file_path.open("r", encoding="utf-8", newline="") as file:
                reader = csv.DictReader(file)
                if reader.fieldnames is None:
                    return
                for nomor_baris, row in enumerate(reader, start=2):
                    try:
                        self.transaksi.append(Transaksi.from_dict(row))
                    except ValueError as exc:
                        self.peringatan_muat.append(
                            f"Baris {nomor_baris} dilewati: {exc}"
                        )
        except (OSError, csv.Error) as exc:
            raise RuntimeError(
                f"Gagal membaca file CSV '{self.file_path}': {exc}"
            ) from exc

    def simpan_data(self) -> None:
        """Simpan seluruh transaksi saat ini ke file CSV."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with self.file_path.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=self.FIELDNAMES)
                writer.writeheader()
                for item in self.transaksi:
                    writer.writerow(item.to_dict())
        except (OSError, csv.Error) as exc:
            raise RuntimeError(
                f"Gagal menyimpan file CSV '{self.file_path}': {exc}"
            ) from exc

    def tambah_transaksi(self, transaksi: Transaksi) -> None:
        """Tambahkan transaksi baru dan simpan ke CSV."""
        self.transaksi.append(transaksi)
        self.simpan_data()

    def hapus_transaksi(self, index: int) -> Transaksi:
        """Hapus transaksi berdasarkan indeks 0-based dan simpan perubahan."""
        if index < 0 or index >= len(self.transaksi):
            raise IndexError("Nomor transaksi tidak ditemukan.")
        terhapus = self.transaksi.pop(index)
        self.simpan_data()
        return terhapus

    def daftar_kategori(self) -> list[str]:
        """Kembalikan daftar unik kategori yang tersimpan (urut alfabetis)."""
        return sorted({t.kategori for t in self.transaksi}, key=str.lower)

    def daftar_bulan(self) -> list[str]:
        """Kembalikan daftar unik bulan YYYY-MM yang tersimpan (terbaru dulu)."""
        return sorted({t.tanggal[:7] for t in self.transaksi}, reverse=True)

    def filter_transaksi(
        self, kategori: str | None = None, bulan: str | None = None
    ) -> list[Transaksi]:
        """Filter transaksi berdasarkan kategori (case-insensitive) dan/atau bulan (YYYY-MM)."""
        hasil = list(self.transaksi)

        if kategori is not None and kategori.strip():
            target_kategori = kategori.strip().lower()
            hasil = [t for t in hasil if t.kategori.lower() == target_kategori]

        if bulan is not None and bulan.strip():
            target_bulan = validasi_bulan(bulan)
            hasil = [t for t in hasil if t.tanggal.startswith(target_bulan)]

        return hasil

    def hitung_ringkasan(
        self, transaksi_list: list[Transaksi] | None = None
    ) -> dict[str, Any]:
        """Hitung total pemasukan, pengeluaran, saldo, dan kategori pengeluaran terbesar."""
        sumber = self.transaksi if transaksi_list is None else transaksi_list

        total_pemasukan = 0.0
        total_pengeluaran = 0.0
        pengeluaran_per_kategori: dict[str, float] = defaultdict(float)

        for item in sumber:
            if item.jenis == "pemasukan":
                total_pemasukan += item.nominal
            else:
                total_pengeluaran += item.nominal
                pengeluaran_per_kategori[item.kategori] += item.nominal

        kategori_terbesar: tuple[str, float] | None = None
        if pengeluaran_per_kategori:
            kategori_terbesar = max(
                pengeluaran_per_kategori.items(), key=lambda pair: pair[1]
            )

        return {
            "jumlah_transaksi": len(sumber),
            "total_pemasukan": total_pemasukan,
            "total_pengeluaran": total_pengeluaran,
            "saldo": total_pemasukan - total_pengeluaran,
            "kategori_terbesar": kategori_terbesar,
        }

    def export_ringkasan_bulanan(
        self, bulan: str, output_dir: Path | str = "exports"
    ) -> Path:
        """Ekspor ringkasan dan daftar transaksi bulan tertentu (YYYY-MM) ke file .txt."""
        bulan_valid = validasi_bulan(bulan)
        daftar = self.filter_transaksi(bulan=bulan_valid)
        ringkasan = self.hitung_ringkasan(daftar)

        target_dir = Path(output_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        output_path = target_dir / f"ringkasan_{bulan_valid}.txt"

        garis = "=" * 64
        sub_garis = "-" * 64
        kategori_info = (
            f"{ringkasan['kategori_terbesar'][0]} "
            f"({format_rupiah(ringkasan['kategori_terbesar'][1])})"
            if ringkasan["kategori_terbesar"]
            else "-"
        )

        lines = [
            garis,
            f"RINGKASAN KEUANGAN BULANAN ({bulan_valid})",
            garis,
            f"Jumlah Transaksi            : {ringkasan['jumlah_transaksi']}",
            f"Total Pemasukan             : {format_rupiah(ringkasan['total_pemasukan'])}",
            f"Total Pengeluaran           : {format_rupiah(ringkasan['total_pengeluaran'])}",
            f"Saldo                       : {format_rupiah(ringkasan['saldo'])}",
            f"Kategori Pengeluaran Terbesar: {kategori_info}",
            sub_garis,
            "DAFTAR TRANSAKSI",
            sub_garis,
        ]

        if not daftar:
            lines.append("Tidak ada transaksi pada bulan ini.")
        else:
            for idx, item in enumerate(daftar, start=1):
                lines.append(
                    f"{idx:>2}. [{item.tanggal}] {item.jenis.upper():<11} | "
                    f"{item.kategori} | {item.keterangan} | {format_rupiah(item.nominal)}"
                )

        lines.append(garis)

        try:
            output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        except OSError as exc:
            raise RuntimeError(
                f"Gagal menulis file ekspor '{output_path}': {exc}"
            ) from exc

        return output_path
