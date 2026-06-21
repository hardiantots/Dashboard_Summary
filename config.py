"""
config.py — Konfigurasi Terpusat Dashboard SIG
===============================================
Berisi konstanta bisnis, mapping kode produk, dan parameter analitik
yang digunakan bersama oleh seluruh modul dashboard.

Dengan memusatkan konfigurasi di sini, setiap perubahan bisnis
(nama produk, threshold KPI, dll.) cukup dilakukan di satu tempat.
"""

# ── Mapping Material Code ke Nama Produk ──────────────────────────────────────
# Sumber: Skema produk SIG (Semen Indonesia Group)
# Digunakan di: tabs/tab_stock.py, components/sidebar.py
MAT_DICT = {
    "MAT001": "Semen Portland Tipe I",
    "MAT002": "Semen PCC Premium",
    "MAT003": "Semen Tecton Khusus",
    "MAT004": "Semen Portland Komposit",
    "MAT_OTHER": "Produk Lainnya",
}

# ── Parameter Coverage Ratio (Supply Chain) ───────────────────────────────────
# Definisi: Coverage Ratio = Sell-In / Sell-Out (SI/SO)
#
# Interpretasi bisnis:
#   SI/SO < COVERAGE_LOWER → Pasokan < Demand → Defisit / Under-supplied
#                            Pasar menyerap lebih cepat dari pengiriman masuk.
#                            Tindakan: tambah injeksi pasokan segera.
#
#   SI/SO > COVERAGE_UPPER → Pasokan > Demand → Surplus / Over-stocked
#                            Terjadi akumulasi stok di gudang.
#                            Tindakan: relokasi stok atau dorong promosi.
#
#   COVERAGE_LOWER ≤ SI/SO ≤ COVERAGE_UPPER → Seimbang (Balanced)
#
COVERAGE_LOWER = 0.90   # batas bawah — di bawah ini: Defisit Pasokan
COVERAGE_UPPER = 1.10   # batas atas  — di atas ini : Surplus Pasokan

# ── Peta Warna Status Coverage (konsisten di seluruh visualisasi) ─────────────
COVERAGE_COLOR_MAP = {
    "Defisit Pasokan (Under-supplied)": "#e74c3c",   # merah  — butuh pasokan
    "Seimbang (Balanced)":              "#2ecc71",   # hijau  — kondisi ideal
    "Surplus Pasokan (Over-stocked)":   "#3498db",   # biru   — perlu relokasi
}
