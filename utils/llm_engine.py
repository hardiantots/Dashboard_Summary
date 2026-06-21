import json
from openai import OpenAI
import pandas as pd


def get_openai_client(api_key):
    if not api_key:
        return None
    return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)


def generate_executive_briefing(df_revenue, df_survey, api_key):
    """
    Menyintesis minimal 5 poin wawasan eksekutif dari data revenue dan survey produk.
    """
    client = get_openai_client(api_key)
    if not client:
        return "⚠️ Gagal menyintesis penalaran AI. Periksa koneksi atau kunci API Anda."

    try:
        total_revenue = df_revenue["target_revenue"].sum()
        top_province = (
            df_revenue.groupby("province_desc")["target_revenue"].sum().idxmax()
        )
        top_distributor = df_revenue.groupby("soldto")["target_revenue"].sum().idxmax()
        avg_price = df_revenue["avg_price_per_ton"].mean()
        
        if not df_survey.empty and 'brand' in df_survey.columns:
            top_brand = df_survey.groupby("brand")["total_volume_sales"].sum().idxmax()
            avg_fill_rate = df_survey["avg_fill_rate"].mean()
        else:
            top_brand = "N/A"
            avg_fill_rate = 0

        prompt = f"""
        Anda adalah Principal Data Analyst untuk perusahaan semen (SIG).
        Berikut adalah ringkasan performa bisnis saat ini berdasarkan filter yang ditetapkan pengguna:
        
        [Data Revenue & Distribusi]
        - Total Revenue: Rp {total_revenue:,.0f}
        - Rata-rata Harga per Ton: Rp {avg_price:,.0f}
        - Provinsi Tertinggi: {top_province}
        - Distributor Tertinggi: {top_distributor}
        - Jumlah Transaksi Data Revenue: {len(df_revenue)}
        
        [Data Optimalisasi Produk & Lapangan]
        - Brand Terlaris: {top_brand}
        - Rata-rata Order Fill Rate (Pemenuhan Pesanan): {avg_fill_rate:.1f}%
        
        Tugas Anda:
        Berikan MINIMAL 5 poin (tanpa preamble) yang berisi wawasan inti (core insights) dan saran penanganan bisnis (business handling suggestions) yang tajam.
        Fokuskan saran Anda pada:
        1. Strategi memaksimalkan penetrasi di provinsi atau distributor potensial.
        2. Taktik optimalisasi produk/brand terlaris.
        3. Mitigasi perbaikan supply chain jika Order Fill Rate belum maksimal (di bawah 100%).
        
        Gunakan Bahasa Indonesia korporat tingkat eksekutif.
        """

        response = client.chat.completions.create(
            model="nvidia/nemotron-3-super-120b-a12b:free",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        return "⚠️ Gagal menyintesis penalaran AI. Periksa koneksi atau kunci API Anda."


def generate_dispatch_memo(df_pulp, api_key):
    """
    Membuat draf Surat Instruksi Rebalancing Kepala Gudang berdasarkan hasil defisit PuLP.
    """
    client = get_openai_client(api_key)
    if not client:
        return "⚠️ Gagal menyintesis penalaran AI. Periksa koneksi atau kunci API Anda."

    try:
        # Deteksi defisit (Alokasi < Kebutuhan)
        df_deficit = df_pulp[df_pulp["Alokasi (TON)"] < df_pulp["Kebutuhan ML (TON)"]]
        if df_deficit.empty:
            summary = "Semua gudang mendapatkan alokasi penuh sesuai kebutuhan (Tidak ada defisit)."
        else:
            summary = "Terdapat defisit alokasi pada gudang berikut:\n"
            for _, row in df_deficit.iterrows():
                summary += f"- {row['Gudang']}: Butuh {row['Kebutuhan ML (TON)']:,.0f} TON, Dialokasikan {row['Alokasi (TON)']:,.0f} TON\n"

        prompt = f"""
        Anda adalah Lead Supply Chain Manager untuk perusahaan semen (SIG).
        Berdasarkan hasil run Linear Programming (PuLP) hari ini, berikut adalah ringkasan alokasi logistik:
        
        {summary}
        
        Tuliskan draf "Surat Instruksi Rebalancing" singkat (maksimal 3 paragraf) kepada para Kepala Gudang.
        Surat ini harus menjelaskan tindakan mitigasi atas defisit yang terjadi (misal: pengalihan rute atau prioritas tier 1).
        Gunakan Bahasa Indonesia korporat tingkat eksekutif yang tegas dan berwibawa.
        """

        response = client.chat.completions.create(
            model="nvidia/nemotron-3-super-120b-a12b:free",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        return "⚠️ Gagal menyintesis penalaran AI. Periksa koneksi atau kunci API Anda."
