import argparse
import os
import re
import sys
import time
import urllib.parse
from datetime import datetime
import pandas as pd
from playwright.sync_api import sync_playwright

import config


def clean_phone_number(raw_phone: str) -> str:
    """Membersihkan format nomor telepon lokal maupun internasional (+1, +44, +62, dll)."""
    if not raw_phone:
        return ""
    # Hapus label awalan seperti 'Phone: ', 'Telepon: ', 'Call: ', dll.
    cleaned = re.sub(r"^(Phone|Telepon|Call|Tel):\s*", "", raw_phone, flags=re.IGNORECASE).strip()
    return cleaned


def clean_reviews_count(raw_reviews: str) -> int:
    """Mengubah teks ulasan '(1,234 reviews)' atau '1.240 ulasan' menjadi angka integer."""
    if not raw_reviews:
        return 0
    numbers = re.findall(r"\d+", raw_reviews.replace(".", "").replace(",", ""))
    if numbers:
        try:
            return int("".join(numbers))
        except ValueError:
            return 0
    return 0


def clean_rating(raw_rating: str) -> float:
    """Mengubah rating '4.8 stars' atau '4,8' menjadi float."""
    if not raw_rating:
        return 0.0
    match = re.search(r"(\d+[\.,]\d+|\d+)", raw_rating)
    if match:
        val = match.group(1).replace(",", ".")
        try:
            return float(val)
        except ValueError:
            return 0.0
    return 0.0


def classify_website(website_url: str):
    """
    Mengklasifikasikan status website untuk pasar internasional & domestik:
    - Tidak ada website -> NO WEBSITE (Target Utama - Tier 1)
    - Medsos / Delivery / Linktree / Yelp / DoorDash -> ONLY SOCIAL / DELIVERY (Target Sekunder - Tier 2)
    - Website mandiri (.com, .co.uk, dll) -> HAS WEBSITE
    """
    if not website_url or website_url.strip() == "":
        return "NO WEBSITE (Prime Target)", "Tier 1 (High Conversion)"

    clean_url = website_url.lower()
    for domain in config.SOCIAL_AND_AGGREGATOR_DOMAINS:
        if domain in clean_url:
            return f"ONLY SOCIAL / DELIVERY ({domain})", "Tier 2 (Needs Official Website)"

    return "HAS WEBSITE", "Tier 3 (Already Has Website)"


def parse_multi_queries(query_input: str) -> list:
    """
    Mengurai input multi-kategori cerdas (Mendukung bahasa Indonesia 'di' & Inggris 'in', 'at', 'near').
    Contoh 1: 'restaurants, bakeries, cafes in London'
    -> ['restaurants in London', 'bakeries in London', 'cafes in London']

    Contoh 2: 'restoran, rumah makan, umkm di Cianjur'
    -> ['restoran di Cianjur', 'rumah makan di Cianjur', 'umkm di Cianjur']

    Contoh 3: 'plumbers Miami, electricians Miami'
    -> ['plumbers Miami', 'electricians Miami']
    """
    query_input = query_input.strip()
    if "," not in query_input:
        return [query_input]

    # Deteksi pola ' in/at/near/di <lokasi>' di ujung string
    location_match = re.search(r"\s+(di|in|at|near)\s+([^,]+)$", query_input, flags=re.IGNORECASE)

    if location_match:
        prep = location_match.group(1)
        location = location_match.group(2).strip()
        categories_part = query_input[:location_match.start()].strip()
        raw_cats = [c.strip() for c in categories_part.split(",") if c.strip()]
        queries = [f"{cat} {prep} {location}" for cat in raw_cats]
        return queries
    else:
        return [q.strip() for q in query_input.split(",") if q.strip()]


def handle_cookie_consent(page):
    """Menangani popup cookie consent Google Maps di wilayah Eropa (UK, EU) maupun global."""
    try:
        # Cek tombol consent umum di Google
        consent_btn = page.locator(
            "button:has-text('Accept all'), "
            "button:has-text('I agree'), "
            "button:has-text('Setuju semua'), "
            "button[aria-label*='Accept all'], "
            "form[action*='consent'] button"
        ).first
        if consent_btn.is_visible(timeout=3000):
            print(" -> Menyetujui cookie consent Google...", flush=True)
            consent_btn.click()
            page.wait_for_timeout(2000)
    except Exception:
        pass


def get_listing_urls(page, query: str, limit: int = 30) -> list:
    """
    Mencari query di Google Maps dan mengumpulkan URL listing tempat.
    Menggunakan parameter '?hl=en' agar bahasa UI Google Maps selalu dalam bahasa Inggris secara konsisten.
    """
    search_url = f"https://www.google.com/maps/search/{urllib.parse.quote(query)}?hl=en"
    print(f"\n[1/3] Membuka Google Maps: {search_url}", flush=True)

    try:
        page.goto(search_url, timeout=config.TIMEOUT, wait_until="domcontentloaded")
    except Exception as e:
        print(f"[!] Gagal membuka Google Maps: {e}", flush=True)
        return []

    # Tangani persetujuan cookie jika ada
    handle_cookie_consent(page)
    page.wait_for_timeout(3000)

    # Jika langsung dialihkan ke detail 1 tempat
    if "/maps/place/" in page.url:
        print("[i] Hasil pencarian langsung membuka 1 tempat spesifik.", flush=True)
        return [page.url]

    # Tunggu setidaknya 1 tempat muncul di hasil pencarian
    print(f"[2/3] Mengumpulkan daftar tempat (Target: hingga {limit} tempat)...", flush=True)
    try:
        page.wait_for_selector("a[href*='/maps/place/']", timeout=12000)
    except Exception:
        print(f"[!] Tidak menemukan listing tempat untuk query: '{query}'. Cek koneksi atau coba query lain.", flush=True)
        return []

    # Identifikasi kontainer scrollable
    feed_locators = [
        page.locator("div[role='feed']"),
        page.locator("div.m6QErb[aria-label]"),
        page.locator("div.m6QErb.DxyBCb"),
    ]
    scrollable_feed = None
    for loc in feed_locators:
        if loc.count() > 0 and loc.first.is_visible():
            scrollable_feed = loc.first
            break

    listing_urls = []
    seen_urls = set()
    stagnant_count = 0
    max_stagnant = 5

    for _ in range(40):  # Maksimal 40x scroll
        # Ambil semua anchor link tempat
        anchors = page.locator("a[href*='/maps/place/']").all()

        prev_count = len(listing_urls)
        for a in anchors:
            href = a.get_attribute("href")
            if href and href not in seen_urls:
                seen_urls.add(href)
                listing_urls.append(href)
                if len(listing_urls) >= limit:
                    break

        print(f" -> Terkumpul: {len(listing_urls)} tempat...", end="\r", flush=True)

        if len(listing_urls) >= limit:
            break

        if len(listing_urls) == prev_count:
            stagnant_count += 1
            if stagnant_count >= max_stagnant:
                break
        else:
            stagnant_count = 0

        # Scroll panel ke bawah
        if scrollable_feed:
            scrollable_feed.evaluate("el => el.scrollBy(0, 1000)")
        else:
            page.mouse.wheel(0, 1000)

        time.sleep(1.8)

        # Cek apakah sudah mencapai akhir daftar
        end_notice = page.locator("text=\"You've reached the end of the list.\", text='Anda telah mencapai bagian akhir daftar.'")
        if end_notice.count() > 0 and end_notice.first.is_visible():
            print("\n[i] Telah mencapai bagian akhir daftar Google Maps.", flush=True)
            break

    print(f"\n[OK] Selesai mengumpulkan {len(listing_urls)} link tempat.", flush=True)
    return listing_urls


def scrape_place_detail(page, url: str) -> dict:
    """Membuka halaman profil tempat dan mengekstrak seluruh informasi secara mendalam."""
    data = {
        "nama_bisnis": "",
        "kategori": "",
        "status_website": "NO WEBSITE (Prime Target)",
        "tipe_target": "Tier 1 (High Conversion)",
        "url_website": "",
        "telepon": "",
        "rating": 0.0,
        "jumlah_ulasan": 0,
        "alamat": "",
        "gmaps_url": url,
    }

    try:
        # Paksa hl=en agar semua label konsisten
        detail_url = url + ("&hl=en" if "?" in url else "?hl=en")
        page.goto(detail_url, timeout=config.TIMEOUT, wait_until="domcontentloaded")
        page.wait_for_selector("h1", timeout=8000)
    except Exception as e:
        print(f"   [!] Timeout memuat detail: {url[:50]}... ({e})", flush=True)
        return data

    time.sleep(1.0)

    # 1. Nama Bisnis (Business Name)
    try:
        name_elem = page.locator("h1.DUwDvf, h1").first
        data["nama_bisnis"] = name_elem.inner_text().strip()
    except Exception:
        data["nama_bisnis"] = ""

    # 2. Kategori (Category / Niche)
    try:
        cat_elem = page.locator("button.DkEaL, button[jsaction*='category'], span.fontBodyMedium").first
        data["kategori"] = cat_elem.inner_text().strip()
    except Exception:
        data["kategori"] = ""

    # 3. Rating
    try:
        rating_elem = page.locator("div.F7nice span[aria-hidden='true'], span.ceNzKf").first
        data["rating"] = clean_rating(rating_elem.inner_text())
    except Exception:
        data["rating"] = 0.0

    # 4. Total Ulasan (Reviews Count)
    try:
        reviews_elem = page.locator(
            "div.F7nice span:last-child, "
            "span[aria-label*='reviews'], "
            "span[aria-label*='ulasan']"
        ).first
        data["jumlah_ulasan"] = clean_reviews_count(reviews_elem.inner_text() or reviews_elem.get_attribute("aria-label") or "")
    except Exception:
        data["jumlah_ulasan"] = 0

    # 5. Website / Social Media Link
    try:
        website_elem = page.locator(
            "a[data-item-id='authority'], "
            "a[aria-label*='Website'], "
            "a[aria-label*='Situs web'], "
            "a[data-tooltip*='Open website']"
        ).first
        if website_elem.is_visible():
            href = website_elem.get_attribute("href")
            data["url_website"] = href if href else ""
    except Exception:
        data["url_website"] = ""

    # Klasifikasikan Website (No Website / Social Media / Has Website)
    status_web, tipe_target = classify_website(data["url_website"])
    data["status_website"] = status_web
    data["tipe_target"] = tipe_target

    # 6. Nomor Telepon (Phone Number - Mendukung format internasional)
    try:
        phone_elem = page.locator(
            "button[data-item-id*='phone:'], "
            "button[aria-label*='Phone:'], "
            "button[aria-label*='Telepon:'], "
            "button[data-tooltip*='Copy phone']"
        ).first
        if phone_elem.is_visible():
            raw_phone = phone_elem.inner_text() or phone_elem.get_attribute("aria-label") or ""
            data["telepon"] = clean_phone_number(raw_phone)
    except Exception:
        data["telepon"] = ""

    # 7. Alamat Lengkap (Full Address)
    try:
        addr_elem = page.locator(
            "button[data-item-id='address'], "
            "button[aria-label*='Address:'], "
            "button[aria-label*='Alamat:'], "
            "button[data-tooltip*='Copy address']"
        ).first
        if addr_elem.is_visible():
            raw_addr = addr_elem.inner_text() or addr_elem.get_attribute("aria-label") or ""
            data["alamat"] = re.sub(r"^(Address|Alamat):\s*", "", raw_addr, flags=re.IGNORECASE).strip()
    except Exception:
        data["alamat"] = ""

    return data


def generate_output_filename(query: str) -> str:
    """
    Membuat nama file dengan format:
    hasil_scraping/DD-MM-YYYY_nama-file_001.xlsx
    (menggunakan tanda '-' untuk tanggal karena tanda '/' adalah karakter terlarang di Windows)
    dengan penomoran urut otomatis (001, 002, dst.) agar file lama tidak tertimpa.
    """
    output_dir = getattr(config, "OUTPUT_DIR", "hasil_scraping")
    os.makedirs(output_dir, exist_ok=True)

    date_str = datetime.now().strftime("%d-%m-%Y")
    clean_query = re.sub(r"[^\w\-]", "_", query).strip("_")
    clean_query = re.sub(r"_+", "_", clean_query)[:40].strip("_")

    counter = 1
    while True:
        counter_str = f"{counter:03d}"
        filename = f"{date_str}_{clean_query}_{counter_str}.xlsx"
        full_path = os.path.join(output_dir, filename)
        if not os.path.exists(full_path):
            return full_path
        counter += 1


def export_to_excel(results: list, filename: str):
    """Menyimpan data hasil scraping ke file Excel dengan layout rapi."""
    if not results:
        print("[!] Tidak ada data untuk disimpan ke Excel.", flush=True)
        return

    df = pd.DataFrame(results)

    # Mapping nama kolom bilingual / standar profesional
    column_mapping = {
        "nama_bisnis": "Business Name",
        "kategori": "Category",
        "kata_kunci_sumber": "Search Query / Niche",
        "status_website": "Website Status",
        "tipe_target": "Target Priority",
        "url_website": "Website / Social Link",
        "telepon": "Phone Number",
        "rating": "Rating",
        "jumlah_ulasan": "Total Reviews",
        "alamat": "Address",
        "gmaps_url": "Google Maps Link",
    }
    df = df.rename(columns=column_mapping)

    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Leads")
        worksheet = writer.sheets["Leads"]

        # Auto-adjust lebar kolom
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = min(max(max_len + 3, 14), 50)

    print(f"\n" + "=" * 60, flush=True)
    print(f"[BERHASIL] File Excel tersimpan di: {filename}", flush=True)
    print(f"Total data tersimpan: {len(results)} bisnis", flush=True)
    print("=" * 60, flush=True)


def run_scraper(query: str, limit: int = 30, only_no_website: bool = False, headless: bool = None):
    if headless is None:
        headless = config.HEADLESS

    # 1. Parsing jika user memasukkan beberapa kategori sekaligus
    sub_queries = parse_multi_queries(query)

    print("=" * 60, flush=True)
    print(" GOOGLE MAPS LEAD GENERATION SCRAPER (GLOBAL / INTERNATIONAL)", flush=True)
    print(" Fokus: Menemukan Bisnis Tanpa Website Mandiri (Target Klien Web Dev)", flush=True)
    print("=" * 60, flush=True)
    if len(sub_queries) > 1:
        print(f"Pencarian Multi-Kategori Terdeteksi ({len(sub_queries)} kategori):", flush=True)
        for idx, sq in enumerate(sub_queries, 1):
            print(f"  {idx}. {sq}", flush=True)
        print(f"Target per Kategori : {limit} tempat", flush=True)
    else:
        print(f"Kata Kunci          : {sub_queries[0]}", flush=True)
        print(f"Target Data         : {limit} tempat", flush=True)
    print(f"Filter Non-Website  : {'Hanya yang belum punya website' if only_no_website else 'Simpan semua dengan status (Filterable di Excel)'}", flush=True)
    print(f"Mode Browser        : {'Headless (Background)' if headless else 'Headed (Tampilkan Browser)'}", flush=True)
    print("-" * 60, flush=True)

    results = []
    global_seen_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
        )
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080} if headless else None,
            locale="en-US",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        for q_idx, current_query in enumerate(sub_queries, 1):
            if len(sub_queries) > 1:
                print(f"\n>>> Menjalankan kategori [{q_idx}/{len(sub_queries)}]: '{current_query}'", flush=True)

            # Ambil link tempat
            listing_urls = get_listing_urls(page, current_query, limit=limit)

            if not listing_urls:
                print(f"[!] Tidak ada tempat yang ditemukan untuk '{current_query}'. Melanjutkan...", flush=True)
                continue

            print(f"\n[3/3] Mengekstrak informasi detail {len(listing_urls)} tempat dari '{current_query}'...", flush=True)
            for i, url in enumerate(listing_urls, 1):
                # Cegah scraping tempat duplikat
                if url in global_seen_urls:
                    print(f" [{i}/{len(listing_urls)}] [DUPLIKAT] Sudah didapatkan sebelumnya, dilewati.", flush=True)
                    continue
                global_seen_urls.add(url)

                detail = scrape_place_detail(page, url)
                detail["kata_kunci_sumber"] = current_query

                # Cek apakah hanya menyimpan yang tanpa website
                if only_no_website and "HAS WEBSITE" in detail["status_website"]:
                    print(f" [{i}/{len(listing_urls)}] [SKIP] {detail['nama_bisnis']} -> Sudah punya website ({detail['url_website']})", flush=True)
                else:
                    status_badge = "[TARGET!]" if "NO WEBSITE" in detail["status_website"] else "[POTENTIAL]" if "ONLY SOCIAL" in detail["status_website"] else "[HAS WEB]"
                    print(f" [{i}/{len(listing_urls)}] {status_badge} {detail['nama_bisnis']} | {detail['status_website']} | Phone: {detail['telepon'] or '-'}", flush=True)
                    results.append(detail)

                # Jeda human-like agar tidak diblokir
                time.sleep(1.2)

        browser.close()

    # 3. Simpan ke Excel di folder 'hasil_scraping/'
    if results:
        output_filename = generate_output_filename(query)
        export_to_excel(results, output_filename)
    else:
        print("\n[!] Tidak ada data prospek yang memenuhi kriteria pencarian.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Google Maps Lead Scraper untuk mencari calon klien pembuatan website.")
    parser.add_argument("--query", "-q", type=str, default="", help="Kata kunci pencarian (contoh: 'restaurants in London' atau 'restoran di Cianjur')")
    parser.add_argument("--limit", "-l", type=int, default=config.MAX_RESULTS, help="Maksimal target listing per kategori")
    parser.add_argument("--no-web-only", action="store_true", help="Hanya simpan bisnis yang 100% tanpa website (default: simpan semua dengan label status)")
    parser.add_argument("--headless", action="store_true", help="Jalankan di background tanpa memunculkan jendela browser")

    args = parser.parse_args()

    search_query = args.query
    if not search_query:
        if sys.stdin and sys.stdin.isatty():
            try:
                search_query = input("Masukkan kata kunci pencarian (contoh: 'restaurants in London' atau 'restoran di Cianjur'): ").strip()
            except Exception:
                search_query = ""
        if not search_query:
            search_query = "restaurants in London"

    only_no_web = args.no_web_only or config.ONLY_WITHOUT_WEBSITE
    is_headless = True if args.headless else config.HEADLESS
    run_scraper(query=search_query, limit=args.limit, only_no_website=only_no_web, headless=is_headless)
