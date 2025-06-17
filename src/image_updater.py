import os
import re
import requests

from urllib.parse import urljoin

from .sample_image_metadata import DEFAULT_SAMPLE_IMAGES_DATA

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
JSON_FILE_PATH = os.path.join(DATA_DIR, 'sample_images_data.json')


# Session object for a full browser-like impression (Cloudflare bot checks bypass)
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


def get_image_url_from_item(item):
    """
    Get the final image URL for an item.
    If item has scraping config, scrape fresh URL from source_url.
    Otherwise, return the static image_url.

    Returns:
        str: The image URL to download, or None if failed
    """
    scraping_config = item.get('scraping')
    has_scraping = (scraping_config and
                    isinstance(scraping_config, dict) and
                    scraping_config.get('image_selector_regex'))

    if has_scraping:
        print(f"Info: Scraping fresh URL for '{item['name']}' from {item['source_url']}")
        return _fetch_image_url_with_regex(item['source_url'], scraping_config)
    else:
        image_url = item.get('image_url')
        if image_url:
            print(f"Info: Using static URL for '{item['name']}': {image_url}")
            return image_url
        else:
            print(f"Warning: No image_url or scraping config for '{item['name']}'")
            return None


def _fetch_image_url_with_regex(source_url, scraping_config):
    """
    Fetches image URL using regex patterns from scraping config.

    Args:
        source_url (str): The page URL to scrape
        scraping_config (dict): Configuration containing:
            - image_selector_regex: Pattern to find image URL in HTML
            - url_transform_regex: Optional pattern to transform found URL
            - url_transform_replacement: Optional replacement for transform

    Returns:
        str or None: The extracted/transformed image URL, or None if failed
    """
    try:
        response = session.get(source_url, timeout=15)
        response.raise_for_status()

        print(f"Info: Response status code for {source_url}: {response.status_code}")
        # print(f"Info: Response headers for {source_url}: {response.headers}")

        html_content = response.text
        if not html_content:
            print(f"Warning: No content returned for {source_url}.")
            return None

        # Uncomment HTML content writer for debugging
        # os.makedirs(DATA_DIR, exist_ok=True)
        # with open(os.path.join(DATA_DIR, 'debug_html_content.html'), 'w', encoding='utf-8') as f:
        #     f.write(html_content)

        image_selector_regex = scraping_config.get('image_selector_regex')
        if not image_selector_regex:
            print(f"Warning: No image_selector_regex provided for {source_url}")
            return None

        match = re.search(image_selector_regex, html_content, re.DOTALL | re.IGNORECASE)
        if not match:
            print(f"Warning: Could not find image URL using regex pattern for {source_url}")
            return None

        found_url = match.group(1)
        print(f"Info: Raw extracted URL: {found_url}")

        # URL transformations if transformer regex is provided
        url_transform_regex = scraping_config.get('url_transform_regex')
        url_transform_replacement = scraping_config.get('url_transform_replacement')

        if url_transform_regex and url_transform_replacement:
            transformed_url = re.sub(url_transform_regex, url_transform_replacement, found_url)
            if transformed_url != found_url:
                print(f"Info: Transformed URL from {found_url} to {transformed_url}")
                found_url = transformed_url

        # URL normalization
        if found_url.startswith('//'):
            found_url = 'https:' + found_url
        elif found_url.startswith('/'):
            found_url = urljoin(source_url, found_url)
        elif not found_url.startswith(('http://', 'https://')):
            found_url = urljoin(source_url, found_url)

        if found_url.startswith(('http://', 'https://')) and any(ext in found_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
            return found_url
        else:
            print(f"Warning: Extracted URL for {source_url} doesn't look like a valid image URL: {found_url}")
            return None

    except requests.RequestException as e:
        print(f"Warning: Request failed for {source_url}: {e}")
    except re.error as e:
        print(f"Warning: Regex error for {source_url}: {e}")
    except Exception as e:
        print(f"Warning: An unexpected error occurred while fetching/parsing {source_url}: {e}")

    return None


if __name__ == '__main__':
    print("Testing directly invoked image updater...")
    updated_data = DEFAULT_SAMPLE_IMAGES_DATA
    print("\nFinal data after update attempt:")
    for item_data in updated_data:
        print(f"  {item_data['name']}: {item_data['image_url']}")
