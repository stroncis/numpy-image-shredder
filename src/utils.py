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


def process_image(url, chunk_w, chunk_h, color_effect):
    try:
        img_array = download_image(url)
    except (ValueError, UnidentifiedImageError) as e:
        raise gr.Error(str(e))

    padded_img = pad_image_to_fit_chunks(img_array, chunk_w, chunk_h)
    padded_img_fx = apply_color_effect(padded_img, color_effect)

    vertical_shred, final_shred = shred_image(padded_img_fx, chunk_w, chunk_h)
    color_effect_str = f" ({color_effect})" if color_effect != "None" else ""

    fig, axs = plt.subplots(1, 3, figsize=(18, 6.75), dpi=100)
    axs[0].imshow(padded_img)
    axs[0].set_title(f'Input Image')
    axs[0].axis('off')

    axs[1].imshow(vertical_shred)
    axs[1].set_title(f'After Vertical Shred{color_effect_str}')
    axs[1].axis('off')

    axs[2].imshow(final_shred)
    axs[2].set_title(f'Final Image{color_effect_str}')
    axs[2].axis('off')

    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_result = Image.open(buf)
    plt.close(fig)

    return img_result


def apply_color_effect(img, effect):
    img_copy = img.astype(np.float32)

    if effect == "None":
        return img
    elif effect == "Invert Colors":
        return 255 - img
    elif effect == "Swap R/G Channels":
        swapped_img = img.copy()
        swapped_img[..., 0], swapped_img[..., 1] = swapped_img[..., 1].copy(), swapped_img[..., 0].copy()
        return swapped_img
    elif effect == "Red Channel Only":
        red_only_img = img.copy()
        red_only_img[..., 1:] = 0
        return red_only_img
    elif effect == "Grayscale":
        gray_img_single_channel = np.mean(img_copy, axis=2, keepdims=True)
        gray_img_rgb = np.repeat(gray_img_single_channel, 3, axis=2)  # Convert to RGB to prevent colormapping
        return np.clip(gray_img_rgb, 0, 255).astype(np.uint8)
    elif effect == "Sepia":
        if img_copy.shape[2] < 3:
            # Sepia requires all channels
            return img  # This will be colormapped by Matplotlib
        sepia_matrix = np.array([
            [0.393, 0.769, 0.189],
            [0.349, 0.686, 0.168],
            [0.272, 0.534, 0.131]
        ])
        r, g, b = img_copy[..., 0], img_copy[..., 1], img_copy[..., 2]
        img_copy[..., 0] = r * sepia_matrix[0, 0] + g * sepia_matrix[0, 1] + b * sepia_matrix[0, 2]
        img_copy[..., 1] = r * sepia_matrix[1, 0] + g * sepia_matrix[1, 1] + b * sepia_matrix[1, 2]
        img_copy[..., 2] = r * sepia_matrix[2, 0] + g * sepia_matrix[2, 1] + b * sepia_matrix[2, 2]
        return np.clip(img_copy, 0, 255).astype(np.uint8)
    elif effect == "Brightness Up":
        return np.clip(img_copy + 30, 0, 255).astype(np.uint8)
    elif effect == "Brightness Down":
        return np.clip(img_copy - 30, 0, 255).astype(np.uint8)
    elif effect == "Contrast Up":
        factor = 1.5
        return np.clip(128 + factor * (img_copy - 128), 0, 255).astype(np.uint8)
    elif effect == "Contrast Down":
        factor = 0.7
        return np.clip(128 + factor * (img_copy - 128), 0, 255).astype(np.uint8)
    elif effect == "Solarize":
        threshold = 128 + 64 + 16
        solarized_img = img.copy()
        solarized_img[solarized_img >= threshold] = 255 - solarized_img[solarized_img >= threshold]
        return solarized_img
    else:
        return img
