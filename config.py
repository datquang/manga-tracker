import os

# Cấu hình website cần lấy dữ liệu
TARGET_URL = "https://ppdvn.gov.vn/web/guest/ke-hoach-xuat-ban?query=&id_nxb=-1&bat_dau=&ket_thuc="

# Từ khóa nhà xuất bản thường ra Manga (Lọc bước 1)
MANGA_PUBLISHERS = [
    "Kim Đồng",
    "Trẻ",
    "IPM",
    "Thái Hà",
    "Amak",
    "Sakura",
    "Hội Nhà văn",
    "Hà Nội",
    "Thế giới",
    "Thanh Niên",
    "Dân Trí",
    "Đồng Nai"
]

# API Keys (Lấy từ biến môi trường trong GitHub Actions hoặc file .env ở local)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Cấu hình xuất file
DATA_FILE = "data.json"
OUTPUT_HTML = "index.html"
