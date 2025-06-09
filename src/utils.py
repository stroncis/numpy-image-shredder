from io import BytesIO

import numpy as np
import requests
import matplotlib.pyplot as plt
import gradio as gr

from PIL import Image, UnidentifiedImageError

from src.shredder import shred_image


def download_image(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise ValueError(f"Failed to download image. Status code: {response.status_code} from URL: {url}")

    content_type = response.headers.get('Content-Type', '').lower()
    if not content_type.startswith('image/'):
        print(f"Warning: Content-Type is '{content_type}', which might not be an image. URL: {url}")

    try:
        img = Image.open(BytesIO(response.content)).convert('RGB')
    except UnidentifiedImageError:
        raise UnidentifiedImageError(
            f"Cannot identify image file from URL: {url}. "
            f"Content-Type: {content_type}. "
            "Please ensure the URL points directly to an image file (e.g., .jpg, .png)."
        )
    return np.array(img)


def pad_image_to_fit_chunks(img, chunk_width, chunk_height):
    h, w, c = img.shape
    pad_h = (chunk_height - (h % chunk_height)) % chunk_height
    pad_w = (chunk_width - (w % chunk_width)) % chunk_width
    padded_img = np.pad(img, ((0, pad_h), (0, pad_w), (0, 0)), mode='edge')
    return padded_img


def process_image(url, chunk_w, chunk_h):
    try:
        img_array = download_image(url)
    except (ValueError, UnidentifiedImageError) as e:
        raise gr.Error(str(e))

    padded_img = pad_image_to_fit_chunks(img_array, chunk_w, chunk_h)
    vertical_shred, final_shred = shred_image(padded_img, chunk_w, chunk_h)

    fig, axs = plt.subplots(1, 3, figsize=(18, 6))
    axs[0].imshow(padded_img)
    axs[0].set_title('Original')
    axs[0].axis('off')

    axs[1].imshow(vertical_shred)
    axs[1].set_title('After Vertical Shred')
    axs[1].axis('off')

    axs[2].imshow(final_shred)
    axs[2].set_title('Final Image')
    axs[2].axis('off')

    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_result = Image.open(buf)
    plt.close(fig)

    return img_result
