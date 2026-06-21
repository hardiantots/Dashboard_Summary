# 📊 Dashboard Interaktif: Sales & Supply Chain Intelligence

Proyek ini adalah sebuah **Sistem Pendukung Keputusan Berbasis AI (Decision Support System)** yang dirancang khusus untuk memantau, memprediksi, dan mengoptimalkan performa bisnis (Sales) serta logistik (Supply Chain) perusahaan semen. Aplikasi ini dibangun dengan framework **Streamlit** dan memadukan _Machine Learning_, _Operations Research_, serta _Generative AI_.

## ✨ Fitur Utama

Aplikasi ini mengadopsi tingkat kematangan analitik Level 4 (Predictive & Prescriptive), yang terbagi ke dalam empat modul interaktif:

1. **📊 Analisis Komersial & Revenue**
   Visualisasi komprehensif atas _revenue_, performa provinsi/distributor, dan fitur **AI Executive Briefing** yang ditenagai oleh model _Large Language Model_ (OpenRouter + Nemotron 120B) untuk menyintesis poin-poin wawasan eksekutif dan taktik bisnis seketika.

2. **📦 Manajemen & Optimasi Stok**
   Pemantauan _Coverage Ratio_ dan pemetaan gudang (_Over-capacity_ vs _Under-supplied_). Fitur unggulan di modul ini adalah **Prescriptive Solver** (menggunakan _PuLP Linear Programming_) untuk meresepkan re-alokasi logistik antar gudang yang efisien, disertai penerbitan **AI Dispatch Memo** secara otomatis.

3. **📋 Intelijen Operasional Lapangan**
   Audit kesehatan rantai pasok berbasis survei lapangan, analisis performa _Order Fill Rate_, rasio kekosongan produk (_Stockout Rate_), serta visibilitas kontribusi tiap-tiap merek/produk.

4. **🔮 Peramalan & Optimasi (ML)**
   Simulasi target interaktif di mana pengguna dapat memasukkan skenario bisnis spesifik untuk mendapatkan peramalan masa depan menggunakan model **XGBoost Regressor** (Predictive ML) yang telah di-_training_ sebelumnya.

## 🚀 Panduan Instalasi dan Penggunaan

Karena aplikasi ini dikemas secara mandiri (_standalone_), Anda dapat menjalankannya dengan mudah di lingkungan lokal maupun _Cloud_.

### 1. Prasyarat (_Prerequisites_)

Pastikan Anda memiliki instalasi Python 3.9+ di sistem Anda.
Disarankan untuk menggunakan _Virtual Environment_ (venv).

### 2. Instalasi Dependensi

Buka terminal/CMD di dalam folder `Dashboard_ExDA` dan jalankan perintah:

```bash
pip install -r requirements.txt
```

### 3. Konfigurasi Kunci API AI (Opsional tapi Direkomendasikan)

Untuk mengaktifkan fitur _Reasoning Engine_ berbasis AI (Nemotron 120B), Anda memerlukan API Key dari OpenRouter.

- Anda dapat membuat file `.streamlit/secrets.toml` di direktori ini:
  ```toml
  OPENROUTER_API_KEY = "sk-or-v1-kunci-api-anda"
  ```
- Alternatifnya, Anda dapat menempelkan API Key secara langsung (_on-the-fly_) pada antarmuka _sidebar_ dashboard.

### 4. Menjalankan Aplikasi

Setelah instalasi selesai, jalankan perintah berikut di terminal:

```bash
streamlit run app.py
```

Aplikasi akan otomatis terbuka di browser pada alamat default `http://localhost:8501`.

## 📁 Struktur Direktori Penting

- `app.py`: File eksekusi utama aplikasi.
- `dataset/`: Arsip data hasil olahan akhir (Agregasi) yang digunakan dashboard.
- `models/`: Penyimpanan objek Machine Learning ter-_serialize_ (`.pkl`) dan komponen _encoder_.
- `tabs/` & `components/`: Kumpulan modul _user interface_ modular.
- `utils/`: Skrip pembantu, termasuk `llm_engine.py` tempat orkestrasi pemanggilan AI berada.
