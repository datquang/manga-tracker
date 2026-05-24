import sys
import io

# Cấu hình UTF-8 cho console để tránh lỗi mã hóa chữ Tiếng Việt
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import json
import os
import time
from scraper import fetch_publication_data
from ai_helper import analyze_manga_info
from anilist_api import search_anilist
from config import DATA_FILE, OUTPUT_HTML
from jinja2 import Environment, FileSystemLoader

def process_books():
    print("Bắt đầu lấy dữ liệu từ website...")
    # Lấy 20 trang để quét được lượng truyện tranh lớn hơn
    raw_books = fetch_publication_data(pages=20)
    print(f"Lấy được {len(raw_books)} sách từ các NXB truyện tranh.")
    
    # Đọc dữ liệu cũ để tránh gọi lại API cho sách đã xử lý
    existing_data = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                pass
                
    # Lấy danh sách số đăng ký đã có
    existing_reg_nums = {b['registration_number'] for b in existing_data}
    
    new_manga_list = []
    
    for book in raw_books:
        reg_num = book['registration_number']
        if reg_num in existing_reg_nums:
            continue
            
        print(f"Đang phân tích sách mới: {book['title']}...")
        
        # 1. Gọi AI để phân tích
        ai_info = analyze_manga_info(book['title'], book['author'], book['publisher'])
        
        # Tạm nghỉ 1.5 giây để tránh chạm ngưỡng giới hạn (rate limit) của API Gemini
        time.sleep(1.5)
        
        if ai_info.get("is_manga"):
            original_title = ai_info.get("original_title", book['title'])
            
            # 2. Gọi AniList API
            anilist_info = search_anilist(original_title)
            # Nghỉ 0.5 giây đối với API AniList
            time.sleep(0.5)
            
            # 3. Gộp dữ liệu
            manga_entry = {
                "title_vi": book['title'],
                "author": book['author'],
                "publisher": book['publisher'],
                "registration_number": reg_num,
                "original_title": original_title,
                "synopsis": ai_info.get("synopsis", ""),
                "current_volume_vi": ai_info.get("current_volume", ""),
                "cover_url": anilist_info["cover_url"] if anilist_info else "https://via.placeholder.com/150x220?text=No+Cover",
                "total_volumes": anilist_info["total_volumes"] if anilist_info else "Không rõ",
                "status_original": anilist_info["status"] if anilist_info else "UNKNOWN",
                "anilist_url": anilist_info["anilist_url"] if anilist_info else "#"
            }
            new_manga_list.append(manga_entry)
            print(f"[+] Đã thêm Manga: {book['title']}")
        else:
            print(f"[-] Không phải Manga: {book['title']}")
            # Vẫn đánh dấu là đã xử lý (để ko check lại) nhưng không đưa vào giao diện (hoặc có thể bỏ qua lưu tùy logic)
            pass
            
        # Tạm lưu số đăng ký để không quét lại lần sau (thực tế nên lưu cả sách không phải manga vào 1 list discard)
        existing_reg_nums.add(reg_num)
        existing_data.append({**book, "is_manga": ai_info.get("is_manga", False)})

    # Lưu lại DB (JSON)
    if new_manga_list:
        with open("manga_db.json", 'a', encoding='utf-8') as f:
            for m in new_manga_list:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")
                
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)
        
    return new_manga_list

def generate_html():
    """Đọc từ manga_db.json và sinh ra HTML tĩnh"""
    mangas = []
    if os.path.exists("manga_db.json"):
        with open("manga_db.json", 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    mangas.append(json.loads(line))
                    
    # Gom nhóm theo NXB
    publishers = {}
    for m in mangas:
        pub = m['publisher']
        if pub not in publishers:
            publishers[pub] = []
        publishers[pub].append(m)
        
    # Sinh HTML
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('index.html')
    output = template.render(publishers=publishers)
    
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(output)
    print(f"Đã tạo giao diện tại {OUTPUT_HTML}")

if __name__ == "__main__":
    process_books()
    generate_html()
