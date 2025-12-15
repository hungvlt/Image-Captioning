import os
import time
import shutil
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==============================
# CONFIG
# ==============================
MAX_IMAGES = 200
CLICK_DELAY = 0.25
SCROLL_DELAY = 0.35
MAX_SCROLL_TIMES = 20

LINKS_DIR = "urls_gg"
ARCHIVE_DIR = "urls_archive"
IMAGE_DIR = "images"

os.makedirs(LINKS_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0"
}

# ==============================
# FAST GOOGLE IMAGE CRAWLER
# ==============================
def get_original_images(driver, max_images):
    image_urls = set()
    last_count = 0
    scroll_times = 0

    while len(image_urls) < max_images and scroll_times < MAX_SCROLL_TIMES:
        thumbnails = driver.find_elements(By.CSS_SELECTOR, "img.rg_i, img.YQ4gaf")

        for thumb in thumbnails[last_count:]:
            if len(image_urls) >= max_images:
                break

            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", thumb)
                time.sleep(CLICK_DELAY)
                thumb.click()

                # Wait for large image
                big_img = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "img.n3VNCb"))
                )

                src = big_img.get_attribute("src")
                if src and src.startswith("http") and "encrypted" not in src:
                    image_urls.add(src)
                    print(f"[OK] {len(image_urls)}/{max_images}: {src[:120]}")

            except Exception:
                continue

        last_count = len(thumbnails)

        # scroll to load more
        driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
        time.sleep(SCROLL_DELAY)
        scroll_times += 1

    print(f"\n[DONE] Collected {len(image_urls)} images.\n")
    return image_urls


def crawl_google_images(search_query):
    print(f"\n==== Crawling: {search_query} ====\n")

    options = Options()
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)
    driver.get(f"https://www.google.com/search?q={search_query}&tbm=isch")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "img"))
    )

    urls = get_original_images(driver, MAX_IMAGES)
    driver.quit()

    txt_path = os.path.join(LINKS_DIR, f"{search_query}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(urls))

    print(f"[SAVED] {len(urls)} URLs → {txt_path}")
    return urls

# ==============================
# DOWNLOADER
# ==============================
def download_image(url, save_path):
    try:
        r = requests.get(url, headers=headers, timeout=8, stream=True)
        r.raise_for_status()

        ext = ".jpg" if "jpeg" in r.headers.get("content-type", "") else ".png"
        with open(save_path + ext, "wb") as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)

        print(f"[DOWNLOADED] {save_path+ext}")
        return True
    except:
        return False


def download_all_images():
    for file in os.listdir(LINKS_DIR):
        if not file.endswith(".txt"):
            continue

        name = file.replace(".txt", "")
        folder = os.path.join(IMAGE_DIR, name)
        os.makedirs(folder, exist_ok=True)

        urls = open(os.path.join(LINKS_DIR, file), "r").read().splitlines()
        print(f"\n==== Downloading {name}: {len(urls)} images ====")

        for idx, url in enumerate(urls):
            download_image(url, os.path.join(folder, f"img_{idx}"))

        shutil.move(os.path.join(LINKS_DIR, file), os.path.join(ARCHIVE_DIR, file))
        print(f"[MOVED] {file} → archive")

# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    keyword = input("Enter search keywords: ").strip()
    crawl_google_images(keyword)
    download_all_images()
