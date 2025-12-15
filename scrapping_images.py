import os
import requests
import pandas as pd
from serpapi import GoogleSearch

SERP_API_KEY = os.environ.get("SERPAPI_API_KEY")
if not SERP_API_KEY:
    raise ValueError("SERP_API_KEY not found")

QUERY = "Da Nang City"
CITY = "danang"
MAX_IMAGES = 100

os.makedirs("images", exist_ok=True)

params = {
    "engine": "google_images",
    "q": QUERY,
    "api_key": SERP_API_KEY,
    "num": MAX_IMAGES
}

search = GoogleSearch(params)
results = search.get_dict()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

data = []
count = 1

for img in results.get("images_results", []):
    try:
        img_url = img.get("original")
        if not img_url:
            continue

        title = img.get("title", "")
        source = img.get("source", "")
        caption = title if title else source

        if len(caption.split()) < 5:
            continue

        img_name = f"{CITY}_{count}.jpg"

        response = requests.get(img_url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            continue

        with open(f"images/{img_name}", "wb") as f:
            f.write(response.content)

        data.append({
            "image": img_name,
            "caption": caption
        })

        count += 1
        if count > MAX_IMAGES:
            break

    except Exception as e:
        continue

df = pd.DataFrame(data)
df.to_csv("captions.csv", index=False)

print(f"DONE — downloaded {len(df)} images")
