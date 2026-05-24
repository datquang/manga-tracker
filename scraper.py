import requests
from bs4 import BeautifulSoup
import re
from config import TARGET_URL, MANGA_PUBLISHERS

def fetch_publication_data(pages=1):
    """
    Cào dữ liệu từ trang web Cục Xuất bản
    """
    all_books = []
    
    for page in range(1, pages + 1):
        url = TARGET_URL
        if page > 1:
            # Thông thường Liferay dùng tham số cur=... hoặc trang=...
            # Ở đây ta giả định url có tham số chuyển trang, nếu không cần xử lý động
            pass
            
        print(f"Đang tải trang {page}...")
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Tìm bảng dữ liệu chính (thường là table có class hoặc nằm trong nội dung chính)
            table = soup.find('table')
            if not table:
                continue
                
            rows = table.find_all('tr')
            for row in rows[1:]:  # Bỏ qua header
                cols = row.find_all('td')
                if len(cols) >= 5:
                    book_name = cols[1].text.strip()
                    author = cols[2].text.strip()
                    publisher = cols[3].text.strip()
                    reg_num = cols[4].text.strip()
                    partner = cols[5].text.strip() if len(cols) > 5 else ""
                    
                    # Lọc bước 1: NXB
                    is_potential_manga = any(pub in publisher for pub in MANGA_PUBLISHERS)
                    
                    if is_potential_manga:
                        all_books.append({
                            "title": book_name,
                            "author": author,
                            "publisher": publisher,
                            "partner": partner,
                            "registration_number": reg_num
                        })
                        
        except Exception as e:
            print(f"Lỗi khi tải trang {page}: {e}")
            
    return all_books

if __name__ == "__main__":
    books = fetch_publication_data(1)
    print(f"Tìm thấy {len(books)} đầu sách tiềm năng từ các NXB.")
    for b in books[:5]:
        print(b)
