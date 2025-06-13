import os
import re
import json
import time
import random
import requests

from urllib.parse import urljoin

from .sample_image_metadata import DEFAULT_SAMPLE_IMAGES_DATA

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


# Session object for a full browser-like impression
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


def _fetch_image_url_with_regex(base_url, scraping_config):
    """
    Fetches image URL using regex patterns from scraping config.

    Args:
        base_url (str): The page URL to scrape
        scraping_config (dict): Configuration containing:
            - image_selector_regex: Pattern to find image URL in HTML
            - url_transform_regex: Optional pattern to transform found URL
            - url_transform_replacement: Optional replacement for transform

    Returns:
        str or None: The extracted/transformed image URL, or None if failed
    """
    try:
        response = session.get(base_url, timeout=15)
        response.raise_for_status()

        print(f"Info: Response status code for {base_url}: {response.status_code}")
        print(f"Info: Response headers for {base_url}: {response.headers}")

        html_content = response.text
        if not html_content:
            print(f"Warning: No content returned for {base_url}.")
            return None

        image_selector_regex = scraping_config.get('image_selector_regex')
        if not image_selector_regex:
            print(f"Warning: No image_selector_regex provided for {base_url}")
            return None

        match = re.search(image_selector_regex, html_content, re.DOTALL | re.IGNORECASE)
        if not match:
            print(f"Warning: Could not find image URL using regex pattern for {base_url}")
            return None

        found_url = match.group(1)

        if found_url.startswith('//'):
            found_url = 'https:' + found_url
        elif found_url.startswith('/'):
            found_url = urljoin(base_url, found_url)
        elif not found_url.startswith(('http://', 'https://')):
            found_url = urljoin(base_url, found_url)

        url_transform_regex = scraping_config.get('url_transform_regex')
        url_transform_replacement = scraping_config.get('url_transform_replacement')

        if url_transform_regex and url_transform_replacement:
            transformed_url = re.sub(url_transform_regex, url_transform_replacement, found_url)
            if transformed_url != found_url:
                print(f"Info: Transformed URL from {found_url} to {transformed_url}")
                found_url = transformed_url

        if found_url.startswith(('http://', 'https://')) and any(ext in found_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
            return found_url
        else:
            print(f"Warning: Extracted URL for {base_url} doesn't look like a valid image URL: {found_url}")
            return None

    except requests.RequestException as e:
        print(f"Warning: Request failed for {base_url}: {e}")
    except re.error as e:
        print(f"Warning: Regex error for {base_url}: {e}")
    except Exception as e:
        print(f"Warning: An unexpected error occurred while fetching/parsing {base_url}: {e}")

    return None


def _is_url_valid(image_url):
    """Check if an image URL is accessible and returns a valid response."""
    if not image_url:
        return False
    try:
        response = requests.head(image_url, timeout=5, allow_redirects=True)
        return response.status_code == 200
    except requests.RequestException:
        return False


def _has_scraping_config(item):
    """Check if an item has scraping configuration."""
    scraping_config = item.get('scraping')
    return (scraping_config and
            isinstance(scraping_config, dict) and
            scraping_config.get('image_selector_regex'))


def get_updated_sample_images():
    """
    Load sample images and update any that have scraping configuration 
    and invalid/missing image URLs.
    """
    sample_images = _load_data_from_json()
    updated = False

    for i, item in enumerate(sample_images):
        if _has_scraping_config(item):
            current_image_url = item.get("image_url")

            if not current_image_url or not _is_url_valid(current_image_url):
                print(
                    f"Info: Current URL for '{item['name']}' is invalid or missing. Attempting to update from base_url: {item['base_url']}")

                if i > 0:
                    time.sleep(random.uniform(1, 3))

                new_url = _fetch_image_url_with_regex(item["base_url"], item["scraping"])

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
