import csv
import os

from models import Transaksi, format_rupiah


class Pencatat:
    """Mengelola daftar transaksi dan penyimpanan ke file CSV."""

    def __init__(self, path_csv: str = "data/transaksi.csv") -> None:
        self.path_csv = path_csv
        self.daftar: list[Transaksi] = []
        self._muat_csv()

    def _muat_csv(self) -> None:
        """Membaca data transaksi dari file CSV jika sudah ada."""
        if not os.path.exists(self.path_csv):
            return

        with open(self.path_csv, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for i, row in enumerate(reader, start=1):
                id_transaksi = int(row["id"]) if row.get("id") else i
                self.daftar.append(
                    Transaksi(
                        id=id_transaksi,
                        tanggal=row["tanggal"],
                        kategori=row["kategori"],
                        keterangan=row["keterangan"],
                        jenis=row["jenis"],
                        nominal=float(row["nominal"]),
                    )
                )

    def _simpan_csv(self) -> None:
        """Menyimpan seluruh data transaksi ke file CSV."""
        folder = os.path.dirname(self.path_csv)
        if folder:
            os.makedirs(folder, exist_ok=True)

        fieldnames = ["id", "tanggal", "kategori", "keterangan", "jenis", "nominal"]
        with open(self.path_csv, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for t in self.daftar:
                writer.writerow(
                    {
                        "id": t.id,
                        "tanggal": t.tanggal,
                        "kategori": t.kategori,
                        "keterangan": t.keterangan,
                        "jenis": t.jenis,
                        "nominal": t.nominal,
                    }
                )

    def semua(self) -> list[Transaksi]:
        """Mengembalikan seluruh daftar transaksi."""
        return list(self.daftar)

    def tambah(
        self,
        tanggal: str,
        kategori: str,
        keterangan: str,
        jenis: str,
        nominal: float,
    ) -> Transaksi:
        """Menambah transaksi baru dan menyimpannya ke CSV."""
        id_baru = max((t.id for t in self.daftar), default=0) + 1
        transaksi = Transaksi(
            id=id_baru,
            tanggal=tanggal,
            kategori=kategori,
            keterangan=keterangan,
            jenis=jenis,
            nominal=nominal,
        )
        self.daftar.append(transaksi)
        self._simpan_csv()
        return transaksi

    def filter(
        self, kategori: str | None = None, bulan: str | None = None
    ) -> list[Transaksi]:
        """Menyaring transaksi berdasarkan kategori dan/atau bulan (YYYY-MM)."""
        hasil = []
        for t in self.daftar:
            if kategori and t.kategori.lower() != kategori.lower():
                continue
            if bulan and not t.tanggal.startswith(bulan):
                continue
            hasil.append(t)
        return hasil

    def ringkasan(self, bulan: str | None = None) -> dict:
        """Menghitung total pemasukan, pengeluaran, saldo, dan kategori terbesar."""
        data = self.filter(bulan=bulan) if bulan else self.daftar
        total_pemasukan = 0.0
        total_pengeluaran = 0.0
        per_kategori: dict[str, float] = {}

        for t in data:
            if t.jenis == "pemasukan":
                total_pemasukan += t.nominal
            else:
                total_pengeluaran += t.nominal
                per_kategori[t.kategori] = per_kategori.get(t.kategori, 0.0) + t.nominal

        kategori_terbesar = None
        nilai_terbesar = 0.0
        for kat, total in per_kategori.items():
            if total > nilai_terbesar:
                nilai_terbesar = total
                kategori_terbesar = kat

        return {
            "jumlah_transaksi": len(data),
            "total_pemasukan": total_pemasukan,
            "total_pengeluaran": total_pengeluaran,
            "saldo": total_pemasukan - total_pengeluaran,
            "kategori_terbesar": kategori_terbesar,
        }

    def hapus(self, id_target: int) -> bool:
        """Menghapus transaksi berdasarkan ID. Mengembalikan True jika berhasil."""
        for i, t in enumerate(self.daftar):
            if t.id == id_target:
                self.daftar.pop(i)
                self._simpan_csv()
                return True
        return False

    def export_bulanan(self, bulan: str) -> str:
        """Mengekspor ringkasan dan daftar transaksi bulan tertentu ke file .txt."""
        os.makedirs("exports", exist_ok=True)
        path_file = os.path.join("exports", f"ringkasan_{bulan}.txt")

        data = self.ringkasan(bulan=bulan)
        daftar = self.filter(bulan=bulan)

        baris = [
            f"=== Ringkasan Keuangan Bulan {bulan} ===",
            f"Jumlah Transaksi     : {data['jumlah_transaksi']}",
            f"Total Pemasukan      : {format_rupiah(data['total_pemasukan'])}",
            f"Total Pengeluaran    : {format_rupiah(data['total_pengeluaran'])}",
            f"Saldo                : {format_rupiah(data['saldo'])}",
            f"Pengeluaran Terbesar : {data['kategori_terbesar'] or '-'}",
            "",
            "--- Daftar Transaksi ---",
        ]

        if not daftar:
            baris.append("Tidak ada transaksi pada bulan ini.")
        else:
            for t in daftar:
                baris.append(
                    f"[{t.id}] {t.tanggal} | {t.jenis:<11} | {t.kategori} | "
                    f"{t.keterangan} | {format_rupiah(t.nominal)}"
                )

        with open(path_file, mode="w", encoding="utf-8") as file:
            file.write("\n".join(baris) + "\n")

        return path_file
