import os
import requests
import pandas as pd
from serpapi import GoogleSearch
import configparser

# Read API key from secret.ini
config = configparser.ConfigParser()
config.read("secret.ini")
SERP_API_KEY = config.get("SERPAPI", "API_KEY", fallback="").strip()

if not SERP_API_KEY:
    raise ValueError("SERP_API_KEY not found in secret.ini")

QUERY = "eagle perched on a tree branch"
ANIMAL = "eagle"
MAX_IMAGES = 100

folder_name = f"images/{ANIMAL}"
os.makedirs(folder_name, exist_ok=True)

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

# Check existing images to continue numbering
existing_images = [f for f in os.listdir(folder_name) if f.startswith(f"{ANIMAL}_") and f.endswith(".jpg")]
if existing_images:
    # Extract numbers from filenames like "eagle_1.jpg"
    numbers = [int(f.replace(f"{ANIMAL}_", "").replace(".jpg", "")) for f in existing_images]
    count = max(numbers) + 1
else:
    count = 1

data = []
downloaded = 0  # Track images downloaded in this run

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

        img_name = f"{ANIMAL}_{count}.jpg"

        response = requests.get(img_url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            continue

        with open(f"{folder_name}/{img_name}", "wb") as f:
            f.write(response.content)

        data.append({
            "image": img_name,
            "caption": caption
        })

        count += 1
        downloaded += 1
        if downloaded >= MAX_IMAGES:
            break

    except Exception as e:
        continue

df = pd.DataFrame(data)

# Append to existing CSV or create new one
if os.path.exists("captions.csv"):
    df.to_csv("captions.csv", mode='a', header=False, index=False)
else:
    df.to_csv("captions.csv", index=False)

print(f"DONE — downloaded {len(df)} images")
