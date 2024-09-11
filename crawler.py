import requests
from bs4 import BeautifulSoup
import mariadb
import time
from urllib.parse import urljoin

def save_to_db(title, url, description, content):
    conn = None  # Inisialisasi variabel conn
    try:
        # Koneksi ke MariaDB menggunakan mysql.connector
        conn = mariadb.connect(
            host='127.0.0.1',
            user='root',
            password='12345',
            database='gabut'
        )
        if conn:
            print("Connect to database")
        
        cursor = conn.cursor()

        # Simpan data ke database
        cursor.execute('''
            INSERT INTO websites (title, url, description, content)
            VALUES (%s, %s, %s, %s)
        ''', (title, url, description, content))

        conn.commit()

    except mariadb.Error as e:
        print(f"Error inserting into database: {e}")

    finally:
        # Cek apakah 'conn' sudah terhubung sebelum menutup koneksi
        if conn:
            cursor.close()
            conn.close()

# Fungsi untuk scraping satu halaman
def scrape_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Untuk memeriksa apakah ada error
    except requests.RequestException as e:
        print(f"Error scraping {url}: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    # Ambil title, description, dan content
    title = soup.title.string if soup.title else 'No title'
    
    description = ''
    desc_tag = soup.find('meta', attrs={'name': 'description'})
    if desc_tag and 'content' in desc_tag.attrs:
        description = desc_tag['content']

    content = soup.get_text()

    # Simpan ke database MariaDB
    save_to_db(title, url, description, content)

    # Temukan semua link di halaman untuk di-crawl lebih lanjut
    links = set()  # Menggunakan set untuk menghindari duplikasi
    for link_tag in soup.find_all('a', href=True):
        href = link_tag['href']
        # Gabungkan URL yang relatif dengan URL dasar
        full_url = urljoin(url, href)
        if full_url.startswith('http'):  # Hanya crawl URL yang valid
            links.add(full_url)
    
    return links

# Fungsi crawler untuk menjalankan scraping secara rekursif dari banyak seed URL
def crawl(seed_urls, max_depth=2):
    crawled_urls = set()  # Untuk melacak URL yang sudah di-crawl
    urls_to_crawl = set(seed_urls)  # Set berisi seed URLs
    depth = 0

    while urls_to_crawl and depth < max_depth:
        print(f"Depth: {depth} - URLs to crawl: {len(urls_to_crawl)}")
        new_urls = set()

        for url in urls_to_crawl:
            if url not in crawled_urls:
                print(f"Crawling: {url}")
                links = scrape_page(url)
                if links:
                    # Tambahkan hanya link yang belum di-crawl
                    new_urls.update(links - crawled_urls)

                crawled_urls.add(url)
                time.sleep(1)  # Delay untuk menghindari overload ke server

        urls_to_crawl = new_urls
        depth += 1

    print("Crawling finished!")