from __future__ import annotations

import math
import os
import select
import sys
import termios
import tty
from collections.abc import Callable
from datetime import date
from typing import TypeVar

from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from models import (
    JENIS_VALID,
    Transaksi,
    format_rupiah,
    validasi_bulan,
    validasi_tanggal,
)
from storage import Pencatat

T = TypeVar("T")
console = Console()


def _baca_tombol() -> str:
    """Baca satu tombol dari stdin dalam mode cbreak (mendukung panah ↑/↓)."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        ch = os.read(fd, 1)
        if ch == b"\x03":
            raise KeyboardInterrupt
        if ch in (b"\r", b"\n"):
            return "ENTER"
        if ch in (b"k", b"K"):
            return "UP"
        if ch in (b"j", b"J"):
            return "DOWN"
        if ch == b"\x1b":
            # Cek apakah ada lanjutan escape sequence (misal \x1b[A atau \x1b[B)
            rlist, _, _ = select.select([fd], [], [], 0.05)
            if rlist:
                seq = os.read(fd, 2)
                if seq == b"[A":
                    return "UP"
                if seq == b"[B":
                    return "DOWN"
            return "ESC"
        return ch.decode("utf-8", errors="ignore")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _render_menu_panel(judul: str, opsi: list[str], indeks_aktif: int) -> Panel:
    """Bangun Panel Rich untuk menu navigasi panah."""
    baris: list[str] = []
    for idx, label in enumerate(opsi):
        if idx == indeks_aktif:
            baris.append(f"[bold cyan]❯ {label}[/bold cyan]")
        else:
            baris.append(f"  [white]{label}[/white]")
    baris.append("")
    baris.append("[dim]↑/↓ (atau j/k) pilih • Enter konfirmasi[/dim]")
    return Panel("\n".join(baris), title=judul, border_style="blue")


def pilih_opsi_panah(
    judul: str,
    opsi: list[str],
    key_reader: Callable[[], str] | None = None,
) -> int:
    """Tampilkan menu interaktif yang dinavigasi dengan panah ↑/↓ dan Enter."""
    if key_reader is None and not sys.stdin.isatty():
        # Fallback jika dijalankan dengan input terpipa (non-TTY)
        teks_opsi = "\n".join(
            f"[cyan]{i}.[/cyan] {label}" for i, label in enumerate(opsi, start=1)
        )
        console.print(Panel(teks_opsi, title=judul, border_style="blue"))
        while True:
            raw = Prompt.ask(f"Pilih (1-{len(opsi)})", console=console).strip()
            try:
                idx = int(raw) - 1
                if 0 <= idx < len(opsi):
                    return idx
            except ValueError:
                pass
            console.print(f"[red]Masukkan angka 1 sampai {len(opsi)}.[/red]")

    baca = key_reader or _baca_tombol
    indeks = 0

    with Live(
        _render_menu_panel(judul, opsi, indeks),
        console=console,
        transient=True,
        auto_refresh=False,
    ) as live:
        while True:
            tombol = baca()
            if tombol == "UP":
                indeks = (indeks - 1) % len(opsi)
                live.update(_render_menu_panel(judul, opsi, indeks), refresh=True)
            elif tombol == "DOWN":
                indeks = (indeks + 1) % len(opsi)
                live.update(_render_menu_panel(judul, opsi, indeks), refresh=True)
            elif tombol == "ENTER":
                return indeks


def _input_tervalidasi[T](
    label: str,
    validator: Callable[[str], T],
    default: str | None = None,
) -> T:
    """Minta input berulang kali sampai validator berhasil tanpa ValueError."""
    while True:
        raw = (
            Prompt.ask(label, default=default, console=console)
            if default is not None
            else Prompt.ask(label, console=console)
        )
        try:
            return validator(raw)
        except ValueError as exc:
            console.print(f"[red]Input tidak valid:[/red] {exc}")


def _validasi_teks_wajib(nama_field: str) -> Callable[[str], str]:
    def _validator(nilai: str) -> str:
        bersih = nilai.strip()
        if not bersih:
            raise ValueError(f"{nama_field} tidak boleh kosong.")
        return bersih

    return _validator


def _validasi_nominal(nilai: str) -> float:
    try:
        angka = float(nilai.strip().replace(",", ""))
    except ValueError as exc:
        raise ValueError("Nominal harus berupa angka.") from exc
    if not math.isfinite(angka) or angka <= 0:
        raise ValueError("Nominal harus lebih besar dari 0.")
    return angka


def tampilkan_tabel(daftar: list[Transaksi], judul: str = "Daftar Transaksi") -> None:
    """Tampilkan daftar transaksi dalam bentuk tabel Rich yang rapi."""
    if not daftar:
        console.print(Panel("[yellow]Belum ada data transaksi.[/yellow]", title=judul))
        return

    table = Table(title=judul, box=box.ROUNDED, show_lines=False)
    table.add_column("No", justify="right", style="cyan", no_wrap=True)
    table.add_column("Tanggal", style="white", no_wrap=True)
    table.add_column("Jenis", no_wrap=True)
    table.add_column("Kategori", style="magenta")
    table.add_column("Keterangan", style="white")
    table.add_column("Nominal", justify="right", no_wrap=True)

    for idx, item in enumerate(daftar, start=1):
        warna_jenis = "green" if item.jenis == "pemasukan" else "red"
        table.add_row(
            str(idx),
            item.tanggal,
            f"[{warna_jenis}]{item.jenis.capitalize()}[/{warna_jenis}]",
            item.kategori,
            item.keterangan,
            f"[{warna_jenis}]{format_rupiah(item.nominal)}[/{warna_jenis}]",
        )

    console.print(table)


def menu_tambah(pencatat: Pencatat) -> None:
    """Alur interaktif untuk menambahkan transaksi baru."""
    console.print("\n[bold cyan]-- Tambah Transaksi --[/bold cyan]")
    hari_ini = date.today().isoformat()

    tanggal = _input_tervalidasi(
        "Tanggal (YYYY-MM-DD)", validasi_tanggal, default=hari_ini
    )
    kategori = _input_tervalidasi("Kategori", _validasi_teks_wajib("Kategori"))
    keterangan = _input_tervalidasi("Keterangan", _validasi_teks_wajib("Keterangan"))

    idx_jenis = pilih_opsi_panah(
        "Pilih Jenis Transaksi", [j.capitalize() for j in JENIS_VALID]
    )
    jenis = JENIS_VALID[idx_jenis]
    console.print(f"Jenis: [cyan]{jenis.capitalize()}[/cyan]")

    nominal = _input_tervalidasi("Nominal (Rp)", _validasi_nominal)

    try:
        transaksi = Transaksi(
            tanggal=tanggal,
            kategori=kategori,
            keterangan=keterangan,
            jenis=jenis,
            nominal=nominal,
        )
        pencatat.tambah_transaksi(transaksi)
    except (ValueError, RuntimeError) as exc:
        console.print(f"[red]Gagal menyimpan transaksi:[/red] {exc}")
        return

    console.print("[green]Transaksi berhasil ditambahkan dan disimpan![/green]")


def menu_lihat_semua(pencatat: Pencatat) -> None:
    """Tampilkan seluruh transaksi tersimpan."""
    console.print()
    tampilkan_tabel(pencatat.transaksi, judul="Semua Transaksi")


def menu_filter(pencatat: Pencatat) -> None:
    """Filter transaksi berdasarkan kategori dan/atau bulan."""
    console.print("\n[bold cyan]-- Filter Transaksi --[/bold cyan]")
    console.print("[dim]Tekan Enter untuk melewati filter yang tidak digunakan.[/dim]")

    kategori = Prompt.ask("Kategori", default="", console=console).strip()

    def _validasi_bulan_opsional(nilai: str) -> str:
        bersih = nilai.strip()
        if not bersih:
            return ""
        return validasi_bulan(bersih)

    bulan = _input_tervalidasi("Bulan (YYYY-MM)", _validasi_bulan_opsional, default="")

    hasil = pencatat.filter_transaksi(
        kategori=kategori or None,
        bulan=bulan or None,
    )
    judul_parts = []
    if kategori:
        judul_parts.append(f"Kategori: {kategori}")
    if bulan:
        judul_parts.append(f"Bulan: {bulan}")
    judul = "Hasil Filter" + (f" ({', '.join(judul_parts)})" if judul_parts else "")
    tampilkan_tabel(hasil, judul=judul)


def menu_ringkasan(pencatat: Pencatat) -> None:
    """Tampilkan ringkasan pemasukan, pengeluaran, saldo, dan kategori terbesar."""
    console.print("\n[bold cyan]-- Ringkasan Keuangan --[/bold cyan]")

    def _validasi_bulan_opsional(nilai: str) -> str:
        bersih = nilai.strip()
        if not bersih:
            return ""
        return validasi_bulan(bersih)

    bulan = _input_tervalidasi(
        "Bulan (YYYY-MM, kosongkan untuk semua)",
        _validasi_bulan_opsional,
        default="",
    )

    daftar = pencatat.filter_transaksi(bulan=bulan) if bulan else pencatat.transaksi
    ringkasan = pencatat.hitung_ringkasan(daftar)

    saldo = ringkasan["saldo"]
    warna_saldo = "green" if saldo >= 0 else "red"
    terbesar = ringkasan["kategori_terbesar"]
    teks_terbesar = f"{terbesar[0]} ({format_rupiah(terbesar[1])})" if terbesar else "-"

    isi = (
        f"[bold]Jumlah Transaksi             :[/bold] {ringkasan['jumlah_transaksi']}\n"
        f"[bold]Total Pemasukan              :[/bold] [green]{format_rupiah(ringkasan['total_pemasukan'])}[/green]\n"
        f"[bold]Total Pengeluaran            :[/bold] [red]{format_rupiah(ringkasan['total_pengeluaran'])}[/red]\n"
        f"[bold]Saldo                        :[/bold] [{warna_saldo}]{format_rupiah(saldo)}[/{warna_saldo}]\n"
        f"[bold]Kategori Pengeluaran Terbesar:[/bold] [magenta]{teks_terbesar}[/magenta]"
    )
    judul = f"Ringkasan ({bulan})" if bulan else "Ringkasan Keseluruhan"
    console.print(Panel(isi, title=judul, border_style="cyan"))


def menu_hapus(pencatat: Pencatat) -> None:
    """Hapus transaksi dengan navigasi panah ↑/↓."""
    console.print("\n[bold cyan]-- Hapus Transaksi --[/bold cyan]")
    if not pencatat.transaksi:
        console.print("[yellow]Tidak ada transaksi yang bisa dihapus.[/yellow]")
        return

    opsi = [
        f"[{t.tanggal}] {t.jenis.capitalize():<11} | {t.kategori} | {t.keterangan} | {format_rupiah(t.nominal)}"
        for t in pencatat.transaksi
    ]
    opsi.append("Batal")

    idx = pilih_opsi_panah("Pilih Transaksi untuk Dihapus", opsi)
    if idx == len(pencatat.transaksi):
        console.print("[yellow]Penghapusan dibatalkan.[/yellow]")
        return

    target = pencatat.transaksi[idx]
    konfirmasi = pilih_opsi_panah(
        f"Hapus '{target.keterangan}' ({format_rupiah(target.nominal)})?",
        ["Batal", "Ya, Hapus"],
    )
    if konfirmasi != 1:
        console.print("[yellow]Penghapusan dibatalkan.[/yellow]")
        return

    try:
        terhapus = pencatat.hapus_transaksi(idx)
    except (IndexError, RuntimeError) as exc:
        console.print(f"[red]Gagal menghapus transaksi:[/red] {exc}")
        return

    console.print(f"[green]Transaksi '{terhapus.keterangan}' berhasil dihapus.[/green]")


def menu_export(pencatat: Pencatat) -> None:
    """Ekspor ringkasan bulanan ke file .txt."""
    console.print("\n[bold cyan]-- Export Ringkasan Bulanan (.txt) --[/bold cyan]")
    bulan_default = date.today().strftime("%Y-%m")
    bulan = _input_tervalidasi("Bulan (YYYY-MM)", validasi_bulan, default=bulan_default)

    try:
        output_path = pencatat.export_ringkasan_bulanan(bulan)
    except (ValueError, RuntimeError) as exc:
        console.print(f"[red]Gagal mengekspor ringkasan:[/red] {exc}")
        return

    console.print(f"[green]Ringkasan berhasil diekspor ke:[/green] {output_path}")


def main() -> None:
    """Entry point aplikasi CLI."""
    try:
        pencatat = Pencatat()
    except RuntimeError as exc:
        console.print(f"[red]Error saat memuat data:[/red] {exc}")
        return

    for peringatan in pencatat.peringatan_muat:
        console.print(f"[yellow]Peringatan:[/yellow] {peringatan}")

    menu_items: list[tuple[str, Callable[[Pencatat], None] | None]] = [
        ("Tambah Transaksi", menu_tambah),
        ("Lihat Semua Transaksi", menu_lihat_semua),
        ("Filter Transaksi (Kategori / Bulan)", menu_filter),
        ("Ringkasan Keuangan", menu_ringkasan),
        ("Hapus Transaksi", menu_hapus),
        ("Export Ringkasan Bulanan (.txt)", menu_export),
        ("Keluar", None),
    ]
    opsi_menu = [label for label, _ in menu_items]

    while True:
        console.print()
        try:
            pilihan = pilih_opsi_panah("Pencatat Keuangan CLI", opsi_menu)
        except (KeyboardInterrupt, EOFError):
            console.print("\n[cyan]Sampai jumpa![/cyan]")
            break

        _, handler = menu_items[pilihan]
        if handler is None:
            console.print(
                "[cyan]Terima kasih telah menggunakan Pencatat Keuangan CLI![/cyan]"
            )
            break

        try:
            handler(pencatat)
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Aksi dibatalkan.[/yellow]")


if __name__ == "__main__":
    main()
