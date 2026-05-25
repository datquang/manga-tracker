import google.generativeai as genai
import json
import time
from config import GEMINI_API_KEY

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    model = None

def analyze_manga_info(title, author, publisher, partner="", translator=""):
    """
    Sử dụng Gemini để xác định xem sách có phải là Manga và lấy tên gốc.
    Trả về định dạng JSON:
    {
        "is_manga": true/false,
        "original_title": "Tên gốc (Romaji/Anh)",
        "synopsis": "Tóm tắt ngắn (tiếng Việt)",
        "current_volume": "Tập 15" (hoặc rỗng nếu không xác định)
    }
    """
    if not model:
        print("Cảnh báo: Chưa cấu hình GEMINI_API_KEY. Bỏ qua phân tích AI.")
        return {"is_manga": True, "original_title": title, "synopsis": "", "current_volume": ""}
        
    prompt = f"""
    Bạn là một chuyên gia phân loại sách và truyện tranh (Manga/Manhwa/Manhua/Comic).
    Tôi có một tựa sách đăng ký xuất bản tại Việt Nam:
    - Tên sách: {title}
    - Tác giả: {author}
    - Dịch giả: {translator}
    - Đối tác liên kết (Công ty phát hành): {partner}
    - Nhà xuất bản: {publisher}
    
    Hãy phân tích kỹ xem tựa sách này có phải là TRUYỆN TRANH (manga, manhwa, manhua, comic, graphic novel) hay không.
    
    LƯU Ý QUAN TRỌNG:
    - Nếu tựa sách này là TIỂU THUYẾT (Novel), LIGHT NOVEL (Truyện chữ có minh họa), SÁCH CHỮ, SÁCH THƠ, SÁCH KỸ NĂNG, TỰ LỰC (Self-help), hoặc các loại SÁCH CHỮ THÔNG THƯỜNG khác, bạn BẮT BUỘC phải đặt "is_manga" là false.
    - Chỉ đặt "is_manga" là true nếu đây CHẮC CHẮN là một tác phẩm TRUYỆN TRANH (comic/manga/manhwa/manhua). Ví dụ: "Chú Thuật Hồi Chiến", "Thám Tử Lừng Danh Conan", v.v. là truyện tranh (is_manga: true). Còn các tác phẩm như tiểu thuyết "Romain Kalbris", tiểu thuyết light novel "Overlord", sách chữ "Thời gian và tôi đều đang tiến về phía trước" là truyện chữ (is_manga: false).
    - Tên sách có thể đã dịch sang tiếng Việt (ví dụ: "Mỹ vị hầm ngục" chính là manga "Dungeon Meshi", "Chú Thuật Hồi Chiến" chính là "Jujutsu Kaisen"). Hãy sử dụng kiến thức rộng lớn của bạn và đối chiếu với tên Tác giả (ví dụ: Kui Ryoko, Gege Akutami) và Đối tác phát hành (ví dụ: IPM, Kim Đồng, Trẻ) để nhận diện chính xác.
    
    Hãy trả về CHỈ MỘT chuỗi JSON hợp lệ với cấu trúc sau (không có code block ```json):
    {{
        "is_manga": (true hoặc false),
        "original_title": "Tên phổ biến tiếng Anh hoặc Romaji của truyện này để tiện tìm kiếm trên AniList. Nếu không biết, trả về tên gốc.",
        "synopsis": "Tóm tắt nội dung cực kỳ ngắn gọn (2-3 câu bằng tiếng Việt).",
        "current_volume": "Trích xuất số tập (volume) từ 'Tên sách' (VD: 'Tập 5'). Nếu không có số tập, để chuỗi rỗng."
    }}
    """
    max_retries = 3
    retry_delay = 60
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.endswith('```'):
                text = text[:-3]
            
            return json.loads(text.strip())
        except Exception as e:
            err_msg = str(e).lower()
            if "429" in err_msg or "exhausted" in err_msg or "quota" in err_msg:
                print(f"Cảnh báo: Đạt giới hạn rate limit (429). Thử lại sau {retry_delay} giây... (Lần thử {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise e
            else:
                print(f"Lỗi khi gọi Gemini API (Lần thử {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                else:
                    raise e

if __name__ == "__main__":
    # Test thử
    test = analyze_manga_info("Chú Thuật Hồi Chiến - Tập 21", "Gege Akutami", "NXB Kim Đồng")
    print(test)
