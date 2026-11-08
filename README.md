# Google Maps Global Lead Generator (Target Klien Pembuatan Website)

Tool otomatis untuk mencari calon klien pembuatan website dari Google Maps di **seluruh dunia (Internasional & Domestik)** yang **belum memiliki website mandiri** atau **hanya menggunakan media sosial / aplikasi pihak ketiga**.

---

## 🌍 Fitur Internasional & Keunggulan

1. **Dukungan Pasar Global (Semua Negara)**:
   - Bahasa antarmuka distandarisasi ke bahasa Inggris (`?hl=en`) sehingga dapat mengambil data bisnis di negara mana pun (AS, Inggris, Australia, Singapura, UEA/Dubai, Eropa, dll.) secara akurat.
   - Format nomor telepon internasional (`+1`, `+44`, `+61`, `+65`, `+971`, `+62`, dll.) tersimpan rapi tanpa terpotong.
2. **Deteksi Website Cerdas (Global & Domestik)**:
   - **Tier 1 (Target Utama - NO WEBSITE)**: Bisnis yang sama sekali tidak memiliki link website di Google Maps.
   - **Tier 2 (Target Sekunder - ONLY SOCIAL / AGGREGATOR)**: Bisnis yang link websitenya hanya mengarah ke aplikasi pesan antar / medsos seperti **DoorDash, UberEats, Yelp, TripAdvisor, Deliveroo, OpenTable, Instagram, Facebook, TikTok, Linktree, bio.link, atau free Wix/WordPress**.
   - **Tier 3 (HAS WEBSITE)**: Bisnis yang sudah memiliki domain sendiri (.com, .co.uk, dsb.).
3. **Pencarian Multi-Kategori Otomatis**:
   - Mendukung bahasa Inggris (`in`, `at`, `near`) dan Indonesia (`di`):
     - `"restaurants, bakeries, cafes in London"`
     - `"plumbers, electricians, roofers in Miami"`
     - `"restoran, rumah makan, umkm, cake shop di Cianjur"`
   - Otomatis menghapus duplikat dan menggabungkan seluruh hasil ke **1 file Excel**.
4. **Penyimpanan Pasti & Terorganisir**:
   - Tersimpan otomatis di folder khusus: **`hasil_scraping/`**.
   - Penomoran urut otomatis: `DD-MM-YYYY_nama-file_001.xlsx` (tidak akan menimpa file lama).

---

## 📂 Struktur File

```text
Scraping GMaps/
│
├── hasil_scraping/     # Folder khusus output file Excel (otomatis dibuat)
├── config.py           # Konfigurasi filter, domain medsos & delivery internasional
├── scraper.py          # Script utama scraping
├── run_scraper.bat     # Launcher 1-klik untuk Windows
├── requirements.txt    # Dependensi library
└── README.md           # Panduan penggunaan
```

---

## 🚀 Cara Menjalankan

### Cara 1: Menggunakan Launcher (Paling Mudah)
Cukup **klik dua kali (double click)** pada file [**`run_scraper.bat`**](run_scraper.bat):
1. Masukkan kata kunci pencarian (contoh: `restaurants, cafes in London` atau `restoran di Cianjur`).
2. Masukkan target data per kategori (default `20`).
3. Tekan Enter. Jendela browser akan terbuka dan mengumpulkan data secara otomatis ke folder `hasil_scraping/`.

### Cara 2: Lewat Command Line (CLI)
```bash
# Contoh 1: Target Pasar UK (Inggris)
python scraper.py --query "restaurants, bakeries in London" --limit 20

# Contoh 2: Target Pasar US (Amerika Serikat - Home Services / Kontraktor)
python scraper.py --query "plumbers, electricians in Miami" --limit 25

# Contoh 3: Target Pasar Australia
python scraper.py --query "hair salons, barbershops in Sydney" --limit 20

# Contoh 4: Target Pasar Indonesia
python scraper.py --query "restoran, rumah makan, umkm di Cianjur" --limit 20

# Opsi: Hanya simpan yang 100% tanpa website
python scraper.py --query "coffee shops in Melbourne" --limit 20 --no-web-only
```

---

## 📊 Kolom Data di File Excel

File Excel akan memiliki kolom-kolom berstandar internasional:
- **Business Name** (Nama Bisnis)
- **Category** (Kategori Bisnis di Google)
- **Search Query / Niche** (Kata kunci pencarian asal)
- **Website Status** (`NO WEBSITE (Prime Target)` / `ONLY SOCIAL / DELIVERY` / `HAS WEBSITE`)
- **Target Priority** (`Tier 1 (High Conversion)` / `Tier 2`)
- **Website / Social Link** (URL link medsos/delivery jika ada)
- **Phone Number** (Nomor telepon format internasional)
- **Rating** (Rating bintang)
- **Total Reviews** (Jumlah ulasan pelanggan)
- **Address** (Alamat lengkap)
- **Google Maps Link** (Link langsung ke listing Google Maps)
