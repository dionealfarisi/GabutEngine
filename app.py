from flask import Flask, request, render_template
import sqlite3
from bs4 import BeautifulSoup
from threading import Thread, Lock
import time
import requests
from crawler import crawl
import urllib.parse
import mariadb

app = Flask(__name__)

def search_data(query):
    conn = None  # Inisialisasi variabel conn agar selalu terdefinisi
    try:
        # Koneksi ke MariaDB menggunakan mysql.connector
        conn = mariadb.connect(
            host='127.0.0.1',
            user='root',
            password='12345',
            database='gabut'
        )
        if conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT title, url, description
                FROM websites
                WHERE content LIKE %s OR title LIKE %s OR description LIKE %s
                ORDER BY 
                    CASE 
                        WHEN title LIKE %s THEN 1
                        WHEN description LIKE %s THEN 2
                        ELSE 3
                    END
            ''', 
            ('%' + query + '%', '%' + query + '%', '%' + query + '%', '%' + query + '%', '%' + query + '%'))

            results = cursor.fetchall()
            return results

    except mariadb.Error as e:
        print(f"Error: {e}")
        return []

    finally:
        # Cek apakah 'conn' sudah terdefinisi dan terhubung sebelum mencoba menutupnya
        if conn:
            cursor.close()
            conn.close()


# Buat list dan lock-nya
links = []
links_lock = Lock()  # Lock untuk sinkronisasi akses ke 'links'

list_query = []
query_lock = Lock()  # Lock untuk sinkronisasi akses ke 'list_query'

def process_link(link):
    # Gunakan lock untuk menghindari race condition saat memodifikasi 'links'
    with links_lock:
        links.append(link)
    return links

def process_query(query):
    # Gunakan lock untuk menghindari race condition saat memodifikasi 'list_query'
    with query_lock:
        list_query.append(query)
    
    # Proses query dan link dengan lock yang sesuai
    for q in list_query:
        link = crawl_google(q, 1)
        process_link(link)

@app.route("/", methods=["GET", "POST"])
def search():
    query = request.args.get("query")  # Ambil query dari GET parameter
    page = request.args.get("page", 1, type=int)  # Ambil halaman dari GET parameter
    per_page = 5  # Jumlah item per halaman

    # Jika ada query, lakukan pencarian
    if query:
        results = search_data(query)
        result_query = process_query(query)

        # Batasi hasil sesuai pagination
        start = (page - 1) * per_page
        end = start + per_page
        paginated_results = results[start:end]

        # Tentukan apakah ada halaman sebelumnya/berikutnya
        previous_page = page - 1 if page > 1 else None
        next_page = page + 1 if end < len(results) else None

        return render_template("index.html", query=query, results=paginated_results, 
                               previous_page=previous_page, next_page=next_page)
    
    # Jika tidak ada query, hanya tampilkan halaman pencarian kosong
    return render_template("index.html", query=None, results=[])

def google_search(query):
    url = f"https://www.google.com/search?q={query}"
    headers = {
       "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
       "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
       "Accept-Language": "en-US,en;q=0.5",
       "Connection": "keep-alive",
       "Upgrade-Insecure-Requests": "1",
    }
    
    # Debugging untuk melihat URL yang diakses
    print(f"Mengakses URL: {url}")
    
    response = requests.get(url, headers=headers)
    
    # Debugging untuk melihat status kode dan konten yang diterima
    print(f"Status Kode: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: Tidak dapat mengakses halaman, status code: {response.status_code}")
        return None
    
    return response.text

def crawl_google(query, depth, visited_urls=set()):
    if depth == 0:
        return None

    try:
        # Encode query untuk digunakan pada URL Ecosia Search
        query_encoded = urllib.parse.quote_plus(query)
        
        # Gunakan ecosia_search untuk mendapatkan hasil pencarian
        html_content = google_search(query_encoded)
        
        if html_content is None:
            print("Tidak ada konten yang diterima.")
            return None
        
        bs = BeautifulSoup(html_content, "html.parser")

        found_links = []  # List untuk mengumpulkan semua link yang ditemukan

        # Mengambil semua link hasil pencarian Ecosia
        for result in bs.find_all("a"):
            link = result.get('href')
            
            if link and link.startswith("http"):
                clean_link = link.split("&")[0]  # Membersihkan link dari parameter yang tidak diperlukan
                
                if clean_link not in visited_urls:
                    visited_urls.add(clean_link)
                    found_links.append(clean_link)
                    
                    # Melakukan crawling pada link yang ditemukan, dengan kedalaman berkurang
                    nested_links = crawl_google(clean_link, depth - 1, visited_urls)
                    if nested_links:
                        found_links.extend(nested_links)  # Menggabungkan link baru yang ditemukan

        return found_links if found_links else None

    except requests.exceptions.RequestException as e:
        print(f"Error accessing Ecosia Search: {e}")
        return None
        
def run_crawler():
    while True:
        # Seed URLs bisa berupa banyak URL
        seed_urls = links.copy()  # Membuat salinan agar tidak langsung memodifikasi 'links' saat iterasi
        
        if not seed_urls:
            print("No seed URLs available. Waiting for new links...")
            print("Seed: ",seed_urls)
            time.sleep(60)
            continue
        
        print("Starting crawler...")
        for url in seed_urls:
            # Lakukan crawling pada URL
            crawl(url, max_depth=2)
            
            # Setelah crawling selesai, hapus URL dari daftar 'links'
            links.remove(url)
            print(f"URL {url} telah di-crawl dan dihapus dari daftar.")

        print("Crawler finished. Sleeping for 1 minutes.")
        time.sleep(60)

if __name__ == '__main__':
    # Jalankan crawler di thread terpisah
    crawler_thread = Thread(target=run_crawler)
    crawler_thread.daemon = True  # Supaya thread berhenti ketika aplikasi dihentikan
    crawler_thread.start()

    app.run(debug=True)