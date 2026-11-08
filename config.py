"""
Konfigurasi scraping Google Maps untuk Pasar Internasional & Domestik.
Fokus: Menemukan Bisnis yang Belum Memiliki Website Resmi untuk Prospek Klien Jasa Pembuatan Website.
"""

# Folder tempat menyimpan hasil file Excel
OUTPUT_DIR = "hasil_scraping"

# Daftar domain yang dikategorikan sebagai Media Sosial / Agregator Pihak Ketiga (Bukan Website Mandiri)
# Jika bisnis luar negeri menggunakan link DoorDash, UberEats, Yelp, atau Instagram sebagai website,
# mereka adalah TARGET EMAS (Tier 2) karena mereka membutuhkan website resmi mandiri!
SOCIAL_AND_AGGREGATOR_DOMAINS = [
    # Social Media
    "instagram.com",
    "facebook.com",
    "fb.com",
    "tiktok.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    
    # Microsite / Free Website Subdomains (Tanda belum punya domain/website profesional)
    "linktr.ee",
    "linktree.com",
    "bio.link",
    "beacons.ai",
    "campsite.bio",
    "heylink.me",
    "taplink.cc",
    "wixsite.com",        # Free Wix subdomain
    "wordpress.com",      # Free WordPress subdomain
    "business.site",      # Old Google Business Site (sudah ditutup oleh Google!)
    "sites.google.com",   # Free Google Sites
    
    # Messaging
    "wa.me",
    "api.whatsapp.com",
    
    # Food Delivery & Aggregators Internasional (US, UK, AUS, Global)
    "yelp.com",
    "tripadvisor.com",
    "opentable.com",
    "doordash.com",
    "ubereats.com",
    "grubhub.com",
    "deliveroo.com",
    "deliveroo.co.uk",
    "just-eat.co.uk",
    "just-eat.com",
    "menulog.com.au",
    "zomato.com",
    
    # Food Delivery Domestik (Indonesia)
    "gofood.co.id",
    "gofood.link",
    "grab.com",
    "shopee.co.id",
    "traveloka.com",
]

# Kriteria Filter Kualifikasi Prospek
MIN_REVIEWS = 0             # 0 agar semua bisnis aktif tetap terjaring (bisa disesuaikan ke 5 atau 10)
MIN_RATING = 0.0            # 0.0 agar tidak membuang data potensial

# PENTING: Jika SAVE_ALL_LEADS = True, semua bisnis akan tetap disimpan ke Excel dengan status jelas:
# - 'NO WEBSITE (Prime Target)' -> Target nomor 1
# - 'ONLY SOCIAL / AGGREGATOR'  -> Target nomor 2
# - 'HAS WEBSITE'               -> Sudah ada website
# Sehingga file Excel TIDAK AKAN PERNAH KOSONG! Anda bisa filter/sortir di Excel sesuai kebutuhan.
SAVE_ALL_LEADS = True

# Jika ONLY_WITHOUT_WEBSITE = True dan SAVE_ALL_LEADS = False, hanya yang tanpa website yang disimpan
ONLY_WITHOUT_WEBSITE = False

# Konfigurasi Browser
HEADLESS = False            # Tampilkan browser saat scraping (True jika ingin berjalan di latar belakang)
MAX_RESULTS = 30            # Target jumlah tempat per kategori
TIMEOUT = 30000             # Timeout per aksi dalam milidetik (30 detik)
