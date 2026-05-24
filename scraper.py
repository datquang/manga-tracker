import requests
from bs4 import BeautifulSoup
from config import TARGET_URL

# Mã NXB ở cuối số đăng ký xuất bản thường liên quan đến truyện tranh
# Ví dụ: "1931-2026/CXBIPH/68-41/KD" -> /KD là NXB Kim Đồng
MANGA_NXB_CODES = ["KD", "TRE", "DHSP"]

NXB_NAMES = {
    "KD": "NXB Kim Đồng",
    "TRE": "NXB Trẻ",
    "DHSP": "NXB Đại học Sư phạm",
    "PN": "NXB Phụ Nữ",
    "HN": "NXB Hà Nội",
    "TG": "NXB Thế Giới",
    "HNV": "NXB Hội Nhà Văn",
    "DT": "NXB Dân Trí",
    "ĐN": "NXB Đồng Nai",
    "LD": "NXB Lao Động",
    "HD": "NXB Hồng Đức",
    "GD": "NXB Giáo Dục",
}

# Tên công ty đối tác liên kết thường phát hành truyện tranh (cột 7)
MANGA_PARTNERS = [
    "IPM", "Amak", "Sakura", "Thái Hà", "Đinh Tị", "Skybooks",
    "Trầm", "Nhã Nam", "Fahasa", "Đông A", "Tiên Phong", "Winbooks",
    "Tsuki", "Kim Đồng", "Trẻ", "Phanbook"
]

def fetch_publication_data(pages=5):
    """
    Cào dữ liệu từ trang web Cục Xuất bản, tự động phân trang.
    
    Cấu trúc cột thực tế:
      0: STT
      1: Mã ISBN
      2: Tên xuất bản phẩm  <-- tên sách
      3: Tác giả hoặc người biên soạn
      4: Người dịch
      5: Số lượng in
      6: Tự xuất bản (trống hoặc "x")
      7: Đối tác liên kết   <-- tên công ty phát hành
      8: Số xác nhận đăng ký xuất bản  <-- có mã NXB ở cuối (VD: /KD, /TRE)
    """
    all_books = []

    for page in range(0, pages):
        # Liferay dùng tham số _cxbhnportlet_cur=<số trang bắt đầu từ 1>
        # nếu không có pagination, chỉ lấy trang đầu
        if page == 0:
            url = TARGET_URL
        else:
            url = TARGET_URL + f"&_cxbhnportlet_cur={page + 1}"

        print(f"Đang tải trang {page + 1}...")
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            table = soup.find('table')
            if not table:
                print(f"  -> Không tìm thấy bảng ở trang {page + 1}, dừng lại.")
                break

            rows = table.find_all('tr')
            if len(rows) <= 1:
                print(f"  -> Trang {page + 1} không có dữ liệu, dừng lại.")
                break

            page_count = 0
            for row in rows[1:]:  # Bỏ qua header
                cols = row.find_all('td')
                if len(cols) < 9:
                    continue

                book_name   = cols[2].text.strip()
                author      = cols[3].text.strip()
                translator  = cols[4].text.strip()
                partner     = cols[7].text.strip()
                reg_num     = cols[8].text.strip()

                # Trích xuất mã NXB từ số đăng ký (phần sau dấu / cuối cùng)
                # VD: "1931-2026/CXBIPH/68-41/KD" -> "KD"
                nxb_code = reg_num.split("/")[-1].strip() if reg_num else ""

                # --- Bộ lọc bước 1: NXB hoặc Đối tác liên quan đến truyện tranh ---
                is_manga_nxb     = nxb_code in MANGA_NXB_CODES
                is_manga_partner = any(p.lower() in partner.lower() for p in MANGA_PARTNERS)

                if is_manga_nxb or is_manga_partner:
                    publisher = NXB_NAMES.get(nxb_code, f"NXB {nxb_code}" if nxb_code else "Không rõ")
                    all_books.append({
                        "title":               book_name,
                        "author":              author,
                        "translator":          translator,
                        "partner":             partner,
                        "nxb_code":            nxb_code,
                        "publisher":           publisher,
                        "registration_number": reg_num,
                    })
                    page_count += 1

            print(f"  -> Tìm thấy {page_count} sách tiềm năng ở trang {page + 1}.")

        except Exception as e:
            print(f"Lỗi khi tải trang {page + 1}: {e}")
            break

    return all_books


if __name__ == "__main__":
    books = fetch_publication_data(pages=5)
    print(f"\nTổng cộng: {len(books)} đầu sách tiềm năng từ các NXB/Đối tác truyện tranh.")
    for b in books[:10]:
        print(f"  [{b['nxb_code']}] {b['title']} - {b['author']} | {b['partner']}")
