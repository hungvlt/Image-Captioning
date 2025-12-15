import os
import requests
import json
from configparser import ConfigParser

# Đọc cookie từ file config
config = ConfigParser(interpolation=None)
config.read('secret.ini')
COOKIE = config['INSTAGRAM']['COOKIE']

# Cấu hình
HASHTAGS = ["danangcity", "hanoi", "hochiminhcity"]
MAX_LINKS = 200
QUERY_HASH = "9b498c08113f1e09617a1703c22b2f32"
BASE_URL = "https://www.instagram.com/graphql/query/"
HEADERS = {
    'cookie': COOKIE,
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'x-ig-app-id': '936619743392459',
}

# Tạo thư mục lưu ảnh
path_folder = "urls_IG"
os.makedirs(path_folder, exist_ok=True)

for hashtag in HASHTAGS:
    print(f"\n[INFO] Đang tìm kiếm #{hashtag}")
    save_path = os.path.join(path_folder, f"{hashtag}.txt")
    img_urls, end_cursor = set(), None

    while len(img_urls) < MAX_LINKS:
        params = {
            "query_hash": QUERY_HASH,
            "variables": json.dumps({"tag_name": hashtag, "first": 50, "after": end_cursor})
        }

        response = requests.get(BASE_URL, headers={**HEADERS, 'referer': f'https://www.instagram.com/explore/tags/{hashtag}/'}, params=params)
        if response.status_code != 200:
            print(f"[ERROR] API lỗi {response.status_code}")
            break

        try:
            data = response.json()
            media = data['data']['hashtag']['edge_hashtag_to_media']
            edges, page_info = media['edges'], media['page_info']
        except (json.JSONDecodeError, KeyError):
            print("[ERROR] Không thể phân tích JSON")
            break

        if not edges:
            print("[INFO] Không còn ảnh.")
            break

        img_urls.update(edge['node']['display_url'] for edge in edges if 'display_url' in edge['node'])
        print(f"[INFO] Đã thu thập {len(img_urls)} ảnh")

        if not page_info.get('has_next_page'):
            break
        end_cursor = page_info.get('end_cursor')

    with open(save_path, 'a', encoding='utf-8') as f:
        f.write('\n'.join(img_urls) + '\n')

    print(f"[INFO] Đã lưu {len(img_urls)} ảnh vào {save_path}")
