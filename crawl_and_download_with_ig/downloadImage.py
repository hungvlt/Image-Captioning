import os
import requests
import shutil

# Đặt thư mục chứa các file txt
LINKS_FOLDER = 'urls_IG'  # thư mục hiện tại (có thể thay bằng đường dẫn khác)
SAVE_ROOT = 'images'  # Thư mục gốc chứa ảnh đã tải

ARCHIVE_FOLDER='urls'
os.makedirs(LINKS_FOLDER, exist_ok=True)
os.makedirs(SAVE_ROOT, exist_ok=True)
os.makedirs(ARCHIVE_FOLDER, exist_ok=True)

# Lặp qua các file .txt trong thư mục
for file in os.listdir(LINKS_FOLDER):
    if file.endswith('.txt'):
        hashtag = file.replace('.txt', '')
        save_dir = os.path.join(SAVE_ROOT, hashtag)
        os.makedirs(save_dir, exist_ok=True)
        txt_path = os.path.join(LINKS_FOLDER, file)
        with open(os.path.join(LINKS_FOLDER, file), 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]

        print(f"\n[INFO] Đang tải {len(urls)} ảnh từ #{hashtag}...")

        for idx, url in enumerate(urls):
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    ext = url.split('?')[0].split('.')[-1]
                    filename = f"{hashtag}_{idx+1}.{ext}"
                    filepath = os.path.join(save_dir, filename)
                    with open(filepath, 'wb') as img_file:
                        img_file.write(response.content)
                else:
                    print(f"[WARN] Không tải được ảnh {idx+1}, mã lỗi: {response.status_code}")
            except Exception as e:
                print(f"[ERROR] Lỗi khi tải ảnh {idx+1}: {e}")
        print(f"[DONE] Đã tải xong ảnh cho #{hashtag}")

        shutil.move(txt_path, os.path.join(ARCHIVE_FOLDER, file))
        print(f"[INFO] Đã chuyển {file} vào {ARCHIVE_FOLDER}/")