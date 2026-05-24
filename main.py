import sys
import io

# Cấu hình UTF-8 cho console để tránh lỗi mã hóa chữ Tiếng Việt
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import json
import os
import time
from scraper import fetch_publication_data_for_page, MANGA_NXB_CODES, MANGA_PARTNERS
from ai_helper import analyze_manga_info
from anilist_api import search_anilist
from config import DATA_FILE, OUTPUT_HTML
from jinja2 import Environment, FileSystemLoader

def process_books():
    print("Bắt đầu lấy dữ liệu từ website...")
    
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
    page = 1
    max_pages = 50  # Quét tối đa 50 trang để đảm bảo có thể quét sâu khi cần
    new_pages_scanned = 0
    
    while page <= max_pages:
        print(f"Đang cào dữ liệu trang {page}...")
        books_on_page = fetch_publication_data_for_page(page)
        
        if not books_on_page:
            print(f"Không có dữ liệu ở trang {page} hoặc gặp lỗi. Dừng.")
            break
            
        # Lọc ra những sách mới chưa có trong cơ sở dữ liệu
        new_books_on_page = [b for b in books_on_page if b['registration_number'] not in existing_reg_nums]
        
        if new_books_on_page:
            new_pages_scanned += 1
            print(f"Trang {page} có {len(new_books_on_page)} sách mới.")
        else:
            print(f"Trang {page} không chứa sách mới nào.")
            
        # Kiểm tra điều kiện dừng (nếu trang này không có sách mới)
        if not new_books_on_page:
            # Nếu chưa quét đủ ít nhất 20 trang chứa sách mới, ta tiếp tục quét sâu hơn
            if new_pages_scanned >= 20:
                print(f"Phát hiện trang trùng hoàn toàn và đã quét đủ {new_pages_scanned} trang có sách mới. Dừng quét.")
                break
            else:
                print(f"Trang trùng hoàn toàn nhưng chưa quét đủ 20 trang có sách mới (hiện mới quét được {new_pages_scanned} trang). Tiếp tục quét sâu...")
            
        # Xử lý các sách mới tìm thấy trên trang này
        for book in new_books_on_page:
            # Lọc sơ bộ bằng lọc cứng (nhà xuất bản hoặc đối tác liên quan đến manga)
            is_manga_nxb = book['nxb_code'] in MANGA_NXB_CODES
            is_manga_partner = any(p.lower() in book['partner'].lower() for p in MANGA_PARTNERS)
            
            if not (is_manga_nxb or is_manga_partner):
                # Không thỏa mãn lọc cứng -> Đánh dấu không phải manga và bỏ qua (không gọi AI/AniList)
                existing_reg_nums.add(book['registration_number'])
                existing_data.append({**book, "is_manga": False})
                continue
                
            print(f"Đang phân tích sách mới: {book['title']}...")
            
            # 1. Gọi AI để phân tích
            try:
                ai_info = analyze_manga_info(
                    book['title'], 
                    book['author'], 
                    book['publisher'], 
                    book['partner'], 
                    book['translator']
                )
                time.sleep(4.5)  # Tránh rate limit của Gemini (sleep 4.5s để đảm bảo < 15 RPM)
            except Exception as e:
                print(f"Thất bại hoàn toàn khi phân tích sách '{book['title']}' qua AI: {e}")
                print("Bỏ qua sách này (sẽ quét lại trong lần chạy sau).")
                continue
            
            if ai_info.get("is_manga"):
                original_title = ai_info.get("original_title", book['title'])
                
                # 2. Gọi AniList API
                anilist_info = search_anilist(original_title)
                time.sleep(0.5)  # Tránh rate limit của AniList
                
                manga_entry = {
                    "title_vi": book['title'],
                    "author": book['author'],
                    "publisher": book['publisher'],
                    "registration_number": book['registration_number'],
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
                
            # Đánh dấu đã xử lý (lưu vào database chung)
            existing_reg_nums.add(book['registration_number'])
            existing_data.append({**book, "is_manga": ai_info.get("is_manga", False)})
            
        page += 1
        time.sleep(1.0)  # Giãn cách 1 giây trước khi tải trang tiếp theo
 
    # Lưu lại DB (JSON)
    if new_manga_list:
        with open("manga_db.json", 'a', encoding='utf-8') as f:
            for m in new_manga_list:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")
                
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)
        
    return new_manga_list

def clean_and_sync_databases():
    """
    Dọn dẹp manga_db.json:
    - Loại bỏ bất kỳ truyện nào bị đánh dấu 'is_manga': False trong data.json.
    - Loại bỏ các dòng bị trùng lặp registration_number.
    Ghi đè lại manga_db.json với dữ liệu sạch.
    """
    print("Đang đồng bộ và dọn dẹp cơ sở dữ liệu manga_db.json...")
    
    # 1. Đọc data.json để biết những sách nào có is_manga == False
    non_manga_reg_nums = set()
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                for b in data:
                    if b.get("is_manga") is False:
                        non_manga_reg_nums.add(b.get("registration_number"))
            except Exception as e:
                print(f"Lỗi đọc data.json khi dọn dẹp: {e}")
                
    # 2. Đọc manga_db.json và lọc
    cleaned_manga = []
    seen_reg_nums = set()
    
    if os.path.exists("manga_db.json"):
        with open("manga_db.json", 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        m = json.loads(line)
                        reg_num = m.get("registration_number")
                        if reg_num in non_manga_reg_nums:
                            print(f"[-] Loại bỏ sách chữ khỏi manga_db.json: {m.get('title_vi')} ({reg_num})")
                            continue
                        if reg_num in seen_reg_nums:
                            continue
                        seen_reg_nums.add(reg_num)
                        cleaned_manga.append(m)
                    except Exception:
                        pass
                        
    # 3. Ghi đè lại manga_db.json sạch sẽ
    with open("manga_db.json", 'w', encoding='utf-8') as f:
        for m in cleaned_manga:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")
            
    print(f"Đã hoàn thành dọn dẹp. Còn lại {len(cleaned_manga)} Manga hợp lệ.")

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
    clean_and_sync_databases()
    generate_html()
