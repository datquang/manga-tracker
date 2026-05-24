import requests

def search_anilist(title):
    """
    Tìm kiếm thông tin Manga trên AniList GraphQL API bằng tên (tiếng Anh/Romaji).
    Trả về cover image, total volumes, status.
    """
    if not title:
        return None

    query = '''
    query ($search: String) {
      Media (search: $search, type: MANGA) {
        id
        title {
          romaji
          english
          native
        }
        status
        volumes
        chapters
        coverImage {
          large
        }
        siteUrl
      }
    }
    '''
    
    variables = {
        'search': title
    }
    
    url = 'https://graphql.anilist.co'
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.post(url, json={'query': query, 'variables': variables}, headers=headers)
        if response.status_code == 404:
            # Không tìm thấy thông tin trên AniList (ví dụ sách không phải manga)
            return None
        response.raise_for_status()
        data = response.json()
        
        media = data.get('data', {}).get('Media')
        if media:
            return {
                "cover_url": media.get('coverImage', {}).get('large', ''),
                "total_volumes": media.get('volumes') or 'Đang ra',
                "status": media.get('status', 'UNKNOWN'),
                "anilist_url": media.get('siteUrl', '')
            }
        return None
    except Exception as e:
        print(f"Lỗi khi gọi AniList API cho '{title}': {e}")
        return None

if __name__ == "__main__":
    # Test thử
    res = search_anilist("Jujutsu Kaisen")
    print(res)
