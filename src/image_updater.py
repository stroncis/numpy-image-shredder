import os
import re
import json
import time
import random
import requests

# Redundant, but default data in case the JSON file doesn't exist or is corrupted
DEFAULT_SAMPLE_IMAGES_DATA = [
    {
        "name": "Vibrant Flower Collection",
        "description": "blossom boxes multiplied",
        "base_url": "https://stockcake.com/i/vibrant-flower-collection_1061865_1157624",
        "image_url": "https://images.stockcake.com/public/2/8/c/28cbee0c-98af-4fd4-98f8-8870ba7b532c/vibrant-flower-collection-stockcake.jpg",
        "license": "Public domain (Stockcake)"
    },
    {
        "name": "Stefan Sagmeister's book cover",
        "description": "Apply 'Swap R/G Channels' or 'Red Channel Only' for the best effect",
        "base_url": "https://www.leboncoin.fr/ad/livres/2856453141",
        "image_url": "https://img.leboncoin.fr/api/v1/lbcpb1/images/25/04/85/25048572a1c62486c5f84c01a3386c59b2b23c61.jpg?rule=ad-large",
        "license": "Unknown"
    },
    {
        "name": "This Person Does Not Exist",
        "description": "There's no escape!",
        "base_url": "https://thispersondoesnotexist.com/",
        "image_url": "https://thispersondoesnotexist.com/",
        "license": "Unknown"
    },
    {
        "name": "Botanical Leaf Tapestry",
        "description": "seamless tapestry",
        "base_url": "https://stockcake.com/i/botanical-leaf-tapestry_2190014_1262920",
        "image_url": "https://images.stockcake.com/public/5/f/1/5f13c92a-353f-435d-b179-b839134d3dfe/botanical-leaf-tapestry-stockcake.jpg",
        "license": "Public domain (Stockcake)"
    },
    {
        "name": "Yellow Flower Matrix",
        "description": "great multiplication effect",
        "base_url": "https://commons.wikimedia.org/wiki/File:Yellow_flowers_a.jpg",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Yellow_flowers_a.jpg/960px-Yellow_flowers_a.jpg",
        "license": "CC BY-SA 3.0 (Wikimedia)"
    },
    {
        "name": "Prismatic Color Burst",
        "description": "good for color manipulation",
        "base_url": "https://stockcake.com/i/prismatic-color-burst_1781331_1235280",
        "image_url": "https://images.stockcake.com/public/8/1/b/81bc82ea-a52f-42c4-8f70-7f4fbd519d1a/prismatic-color-burst-stockcake.jpg",
        "license": "Public domain (Stockcake)"
    },
    {
        "name": "Bubbling Color Symphony",
        "description": "circles to squares effect",
        "base_url": "https://stockcake.com/i/bubbling-color-symphony_1567759_1189604",
        "image_url": "https://images.stockcake.com/public/7/3/d/73d7cc7e-b051-4ab4-82c9-ab6d125d0964/bubbling-color-symphony-stockcake.jpg",
        "license": "Public domain (Stockcake)"
    }
]

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
JSON_FILE_PATH = os.path.join(DATA_DIR, 'sample_images_data.json')


def _load_data_from_json():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(JSON_FILE_PATH):
        try:
            with open(JSON_FILE_PATH, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Error decoding JSON from {JSON_FILE_PATH}. Using default data.")
            return DEFAULT_SAMPLE_IMAGES_DATA
    return DEFAULT_SAMPLE_IMAGES_DATA


def _save_data_to_json(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(JSON_FILE_PATH, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError:
        print(f"Warning: Could not write to {JSON_FILE_PATH}.")


# Session object to persist headers and cookies
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'DNT': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',  # For initial request; could be 'same-origin' or 'cross-site' for subsequent ones if needed
    'Sec-Fetch-User': '?1',
    'TE': 'trailers'
})


def _fetch_stockcake_full_res_url(base_url):
    try:
        response = session.get(base_url, timeout=15)
        response.raise_for_status()

        print(f"Info: Response status code for {base_url}: {response.status_code}")
        print(f"Info: Response headers for {base_url}: {response.headers}")

        html_content = response.text
        if not html_content:
            print(f"Warning: No content returned for {base_url}.")
            return None

        # --- Debugging ---
        # print(f"Info: First 500 chars of content from {base_url}:\n{html_content[:500]}")

        # safe_filename_part = re.sub(r'[^a-zA-Z0-9_-]', '_', base_url.split('/')[-1])
        # dump_filename = os.path.join(DATA_DIR, f"dump_{safe_filename_part}.html")
        # os.makedirs(DATA_DIR, exist_ok=True)
        # try:
        #     with open(dump_filename, 'w', encoding='utf-8', errors='replace') as f_dump:
        #         f_dump.write(html_content)
        #     print(f"Info: Saved content dump to {dump_filename}")
        # except Exception as e_dump:
        #     print(f"Error: Could not save dump file {dump_filename}: {e_dump}")
        # --- End Debugging ---

        # Very brittle!
        match = re.search(
            r'<picture\s+id="mainImageContainer">.*?<img.*?src="([^"]+)".*?</picture>',
            html_content,
            re.DOTALL | re.IGNORECASE
        )
        if match:
            low_res_url = match.group(1)
            full_res_url = re.sub(r'_large(/[^/]+?stockcake\.jpg)', r'\1', low_res_url)
            if full_res_url == low_res_url:
                full_res_url = low_res_url.replace("_large.", ".")

            if full_res_url.startswith("https") and "stockcake.jpg" in full_res_url:
                return full_res_url
            else:
                print(f"Warning: Extracted URL for {base_url} doesn't look right: {full_res_url}")
        else:
            print(f"Warning: Could not find mainImageContainer or img src for {base_url}")
    except requests.RequestException as e:
        print(f"Warning: Request failed for {base_url}: {e}")
    except Exception as e:
        print(f"Warning: An unexpected error occurred while fetching/parsing {base_url}: {e}")
    return None


def _is_url_valid(image_url):
    try:
        response = requests.head(image_url, timeout=5, allow_redirects=True)
        return response.status_code == 200
    except requests.RequestException:
        return False


def get_updated_sample_images():
    sample_images = _load_data_from_json()
    updated = False
    for i, item in enumerate(sample_images):
        if "stockcake.com" in item.get("base_url", ""):
            current_image_url = item.get("image_url")
            if not current_image_url or not _is_url_valid(current_image_url):
                print(
                    f"Info: Current URL for '{item['name']}' is invalid or missing. Attempting to update from base_url: {item['base_url']}")

                if i > 0:
                    time.sleep(random.uniform(1, 3))

                new_url = _fetch_stockcake_full_res_url(item["base_url"])
                if new_url and new_url != current_image_url:
                    print(f"Info: Updated URL for '{item['name']}' to: {new_url}")
                    item["image_url"] = new_url
                    updated = True
                elif not new_url:
                    print(
                        f"Warning: Failed to fetch new URL for '{item['name']}'. Keeping old one if exists: {current_image_url}")

    if updated or not os.path.exists(JSON_FILE_PATH):
        _save_data_to_json(sample_images)
    return sample_images


if __name__ == '__main__':
    print("Testing directly invoked image updater...")
    updated_data = get_updated_sample_images()
    print("\nFinal data after update attempt:")
    for item_data in updated_data:
        print(f"  {item_data['name']}: {item_data['image_url']}")
    print(f"\nData saved to/read from: {JSON_FILE_PATH}")
