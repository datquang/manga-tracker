import google.generativeai as genai
import json
from config import GEMINI_API_KEY

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

def analyze_manga_info(title, author, publisher):
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
    Bạn là một chuyên gia về truyện tranh (Manga/Manhwa/Manhua).
    Tôi có một tựa sách sắp xuất bản tại Việt Nam:
    - Tên sách: {title}
    - Tác giả: {author}
    - Nhà xuất bản: {publisher}
    
    Hãy phân tích và trả về CHỈ MỘT chuỗi JSON hợp lệ với cấu trúc sau (không có code block ```json):
    {{
        "is_manga": (true/false) đây có phải là truyện tranh (manga/manhwa/manhua/comic) không?,
        "original_title": "Tên phổ biến tiếng Anh hoặc Romaji của truyện này để tiện tìm kiếm trên Anilist. Nếu không biết, trả về tên gốc.",
        "synopsis": "Tóm tắt nội dung cực kỳ ngắn gọn (2-3 câu bằng tiếng Việt).",
        "current_volume": "Trích xuất số tập (volume) từ 'Tên sách' (VD: 'Tập 5'). Nếu không có số tập, để chuỗi rỗng."
    }}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith('```json'):
            text = text[7:]
        if text.endswith('```'):
            text = text[:-3]
        
        return json.loads(text.strip())
    except Exception as e:
        print(f"Lỗi khi gọi Gemini API: {e}")
        return {"is_manga": False, "original_title": "", "synopsis": "", "current_volume": ""}

if __name__ == "__main__":
    # Test thử
    test = analyze_manga_info("Chú Thuật Hồi Chiến - Tập 21", "Gege Akutami", "NXB Kim Đồng")
    print(test)
