import requests
from bs4 import BeautifulSoup
from config import TARGET_URL

# Mã NXB ở cuối số đăng ký xuất bản thường liên quan đến truyện tranh
MANGA_NXB_CODES = ["KD", "TRE", "DHSP"]

# Tên công ty đối tác liên kết thường phát hành truyện tranh (cột 7)
MANGA_PARTNERS = [
    "IPM", "Amak", "Sakura", "Thái Hà", "Đinh Tị", "Skybooks",
    "Trầm", "Nhã Nam", "Fahasa", "Đông A", "Tiên Phong", "Winbooks",
    "Tsuki", "Kim Đồng", "Trẻ", "Phanbook"
]

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

def fetch_publication_data_for_page(page_num):
    """
    Cào dữ liệu từ 1 trang duy nhất của trang web Cục Xuất bản (bắt đầu từ 1).
    """
    url = TARGET_URL
    if page_num > 1:
        url = TARGET_URL + f"&p={page_num}"

    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        table = soup.find('table')
        if not table:
            return []

        rows = table.find_all('tr')
        if len(rows) <= 1:
            return []

        books = []
        for row in rows[1:]:  # Bỏ qua header
            cols = row.find_all('td')
            if len(cols) < 9:
                continue

            book_name   = cols[2].text.strip()
            author      = cols[3].text.strip()
            translator  = cols[4].text.strip()
            partner     = cols[7].text.strip()
            reg_num     = cols[8].text.strip()

            nxb_code = reg_num.split("/")[-1].strip() if reg_num else ""
            publisher = NXB_NAMES.get(nxb_code, f"NXB {nxb_code}" if nxb_code else "Không rõ")

            is_manga_nxb     = nxb_code in MANGA_NXB_CODES
            is_manga_partner = any(p.lower() in partner.lower() for p in MANGA_PARTNERS)

            # Lọc sơ bộ để lấy các sách liên quan đến truyện tranh
            if is_manga_nxb or is_manga_partner:
                books.append({
                    "title":               book_name,
                    "author":              author,
                    "translator":          translator,
                    "partner":             partner,
                    "nxb_code":            nxb_code,
                    "publisher":           publisher,
                    "registration_number": reg_num,
                })

        return books

    except Exception as e:
        print(f"Lỗi khi tải trang {page_num}: {e}")
        return []
