import os
import time
import shutil
import requests
from icrawler.builtin import BingImageCrawler, BingFeeder, BingParser
from icrawler.downloader import Downloader


# ===============================
# CONFIG
# ===============================
KEYWORDS = [
    "bird is flying over the lake",
]

MAX_LINKS = 1000

URL_SAVE_DIR = "urls_bing"
IMAGE_SAVE_DIR = "images"
ARCHIVE_DIR = "urls"

FAKE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ===============================
# CREATE FOLDERS
# ===============================
os.makedirs(URL_SAVE_DIR, exist_ok=True)
os.makedirs(IMAGE_SAVE_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)


# ===============================
# LINK COLLECTOR (NO DOWNLOAD)
# ===============================
class LinkCollectorDownloader(Downloader):
    def __init__(self, *args, **kwargs):
        self.urls = set()
        super().__init__(*args, **kwargs)

    def download(self, task, default_ext, timeout=5, **kwargs):
        url = task.get("file_url")
        if url:
            self.urls.add(url)
        return  # skip actual image download


# ===============================
# PART 1 — CRAWL URLS
# ===============================
def crawl_image_urls(keyword):
    print(f"\n🚀 Crawling Bing Images → {keyword}")

    crawler = BingImageCrawler(
        feeder_cls=BingFeeder,
        parser_cls=BingParser,
        downloader_cls=LinkCollectorDownloader,
        feeder_threads=1,
        parser_threads=2,
        downloader_threads=2,
        storage={"root_dir": "ignore"},
    )

    # Fake headers to avoid blocking
    crawler.session.headers.update(FAKE_HEADERS)

    crawler.crawl(keyword=keyword, max_num=MAX_LINKS)

    urls = crawler.downloader.urls

    print(f"👉 Found: {len(urls)} URLs")

    save_path = os.path.join(URL_SAVE_DIR, f"{keyword}.txt")
    with open(save_path, "w", encoding="utf-8") as f:
        f.write("\n".join(urls))

    print(f"💾 Saved → {save_path}")
    return save_path


# ===============================
# PART 2 — DOWNLOAD IMAGES
# ===============================
def download_images_from_txt(file_path):
    keyword = os.path.basename(file_path).replace(".txt", "")
    save_dir = os.path.join(IMAGE_SAVE_DIR, keyword)
    os.makedirs(save_dir, exist_ok=True)

    urls = open(file_path, "r", encoding="utf-8").read().splitlines()
    print(f"\n⬇️ Downloading {len(urls)} images for #{keyword}...\n")

    for idx, url in enumerate(urls):
        try:
            resp = requests.get(url, headers=FAKE_HEADERS, timeout=8)
            if resp.status_code == 200:
                ext = url.split("?")[0].split(".")[-1][:4]
                if ext.lower() not in ["jpg", "jpeg", "png", "webp"]:
                    ext = "jpg"
                file_name = f"{keyword}_{idx+1}.{ext}"
                with open(os.path.join(save_dir, file_name), "wb") as img:
                    img.write(resp.content)
            else:
                print(f"[SKIP] {url} (HTTP {resp.status_code})")

        except Exception as e:
            print(f"[ERR] Cannot download: {url}\n{e}")

    print(f"✔ DONE downloading images for {keyword}")

    # Move txt file to archive
    shutil.move(file_path, os.path.join(ARCHIVE_DIR, os.path.basename(file_path)))
    print(f"📦 Archived → {file_path}\n")


# ===============================
# MAIN EXECUTION
# ===============================
if __name__ == "__main__":
    for kw in KEYWORDS:
        txt_file = crawl_image_urls(kw)
        download_images_from_txt(txt_file)

    print("\n🎉 ALL DONE!")
