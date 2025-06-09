from io import BytesIO

import numpy as np
import requests
import matplotlib.pyplot as plt

from PIL import Image

from src.shredder import shred_image

def download_image(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content)).convert('RGB')
    return np.array(img)


def pad_image_to_fit_chunks(img, chunk_width, chunk_height):
    h, w, c = img.shape
    pad_h = (chunk_height - (h % chunk_height)) % chunk_height
    pad_w = (chunk_width - (w % chunk_width)) % chunk_width
    padded_img = np.pad(img, ((0, pad_h), (0, pad_w), (0, 0)), mode='edge')
    return padded_img

def process_image(url, chunk_w, chunk_h):
    img = download_image(url)
    img = pad_image_to_fit_chunks(img, chunk_w, chunk_h)
    vertical, final = shred_image(img, chunk_w, chunk_h)

    fig, axs = plt.subplots(1, 3, figsize=(18, 6))
    axs[0].imshow(img)
    axs[0].set_title('Original')
    axs[0].axis('off')

    axs[1].imshow(vertical)
    axs[1].set_title('After Vertical Shred')
    axs[1].axis('off')

    axs[2].imshow(final)
    axs[2].set_title('Final Image')
    axs[2].axis('off')

    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_result = Image.open(buf)
    plt.close(fig)

    return img_result
