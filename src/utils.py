import datetime
from io import BytesIO

import requests
import numpy as np
import gradio as gr

from PIL import Image, UnidentifiedImageError

from src.shredder import shred_image
from .config import OUTPUT_IMAGE_DPI, OUTPUT_IMAGE_ASPECT_RATIO, OUTPUT_IMAGE_WIDTH_IN_PIXELS, MIN_VALID_OUTPUT_WIDTH, DEFAULT_TITLE_FONT_SIZE

# fmt: off
import matplotlib
# Fix for a threading issue with Matplotlib on macOS.
# It's heisenbug-like, causes crashes so randomly, that impossible to reproduce.
# Gradio runs event handlers in background threads for responsiveness, though
# Matplotlib's GUI backend on macOS requires the main thread for creating windows/figures
# and plt.subplots() call is moved to a background thread in some cases.
# Anti-Grain Geometry backend is thread-safe and designed for server/web applications
# It generates images directly to memory/files without creating GUI windows
matplotlib.use('Agg')  # Set non-interactive backend BEFORE importing pyplot
import matplotlib.pyplot as plt
# fmt: on


def get_timestamp():
    return datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]


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
    h, w, _ = img.shape
    pad_h = (chunk_height - (h % chunk_height)) % chunk_height
    pad_w = (chunk_width - (w % chunk_width)) % chunk_width
    padded_img = np.pad(img, ((0, pad_h), (0, pad_w), (0, 0)), mode='edge')
    return padded_img


def process_image(
    base_img_array,
    chunk_w,
    chunk_h,
    color_effect,
    brightness_offset,
    contrast_factor,
    show_guidelines,
    guideline_color_rgb_array,
    output_image_width,
    source=None
):
    if output_image_width is None or not isinstance(output_image_width, (int, float)) or output_image_width < MIN_VALID_OUTPUT_WIDTH:
        raise gr.Error(
            f"Output image width must be a positive number. Received: '{output_image_width}'. Please enter a valid width (e.g., >= {MIN_VALID_OUTPUT_WIDTH}px)."
        )

    if source:
        print(f"{get_timestamp()} Processing image invoked from {source}")

    padded_img = pad_image_to_fit_chunks(base_img_array, chunk_w, chunk_h)
    img_after_effects = apply_color_effect(padded_img, color_effect, brightness_offset, contrast_factor)

    vertical_shred, final_shred = shred_image(img_after_effects, chunk_w, chunk_h)

    display_vertical_shred = vertical_shred
    display_final_shred = final_shred

    if show_guidelines:
        display_vertical_shred = draw_guidelines(
            vertical_shred, chunk_w, orientation='vertical', line_color_rgb=guideline_color_rgb_array)
        display_final_shred = draw_guidelines(
            final_shred, chunk_h, orientation='horizontal', line_color_rgb=guideline_color_rgb_array)

    effects_applied_list = []
    if color_effect != "None":
        effects_applied_list.append(color_effect)
    if brightness_offset != 0:
        effects_applied_list.append(f"Bright {brightness_offset:+.0f}")
    if contrast_factor != 1.0:
        effects_applied_list.append(f"Contrast x{contrast_factor:.1f}")

    applied_effects_str = f" ({', '.join(effects_applied_list)})" if effects_applied_list else ""

    if output_image_width < MIN_VALID_OUTPUT_WIDTH:
        scaled_title_fontsize = DEFAULT_TITLE_FONT_SIZE
    else:
        reference_width = OUTPUT_IMAGE_WIDTH_IN_PIXELS if OUTPUT_IMAGE_WIDTH_IN_PIXELS > 0 else output_image_width
        if reference_width == 0:
            reference_width = 800  # Failsafe
        scaled_title_fontsize = (output_image_width / OUTPUT_IMAGE_WIDTH_IN_PIXELS) * DEFAULT_TITLE_FONT_SIZE
    scaled_title_fontsize = np.clip(scaled_title_fontsize, 7, 72)  # Clamping font size to a reasonable range

    current_dpi = OUTPUT_IMAGE_DPI
    if current_dpi == 0:
        raise gr.Error("Output Image DPI in configuration cannot be zero.")

    padded_h, padded_w, _ = padded_img.shape
    if padded_h == 0 or padded_w == 0:
        input_aspect_ratio = OUTPUT_IMAGE_ASPECT_RATIO # Fallback
    else:
        input_aspect_ratio = padded_w / padded_h

    dynamic_output_image_height_px = (output_image_width / (input_aspect_ratio * 3)) + (scaled_title_fontsize * 4)

    fig_w = output_image_width / current_dpi
    fig_h = dynamic_output_image_height_px / current_dpi

    if fig_w <= 0 or fig_h <= 0:
        raise gr.Error(
            f"Calculated figure dimensions are invalid (width: {fig_w:.2f}in, height: {fig_h:.2f}in). "
            f"Please check output width ({output_image_width}px) and aspect ratio ({OUTPUT_IMAGE_ASPECT_RATIO})."
        )

    fig, axs = plt.subplots(1, 3, figsize=(fig_w, fig_h), dpi=current_dpi)

    axs[0].imshow(padded_img)
    axs[0].set_title(f'Input Image', fontsize=scaled_title_fontsize)
    axs[0].axis('off')

    axs[1].imshow(display_vertical_shred)
    axs[1].set_title(f'Vertical Shred{applied_effects_str}', fontsize=scaled_title_fontsize)
    axs[1].axis('off')

    axs[2].imshow(display_final_shred)
    axs[2].set_title(f'Final Image{applied_effects_str}', fontsize=scaled_title_fontsize)
    axs[2].axis('off')

    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_result = Image.open(buf)
    plt.close(fig)

    return img_result


def apply_color_effect(img, effect, brightness_offset, contrast_factor):
    img_temp_float = img.astype(np.float32)

    # 1. Apply the base color effect
    if effect == "Invert Colors":
        img_temp_float = 255 - img_temp_float
    elif effect == "Swap R/G Channels":
        temp_swap = img_temp_float.copy()
        temp_swap[..., 0], temp_swap[..., 1] = temp_swap[..., 1].copy(), temp_swap[..., 0].copy()
        img_temp_float = temp_swap
    elif effect == "Red Channel Only":
        temp_red = img_temp_float.copy()
        temp_red[..., 1:] = 0
        img_temp_float = temp_red
    elif effect == "Grayscale":
        gray_img_single_channel = np.mean(img_temp_float, axis=2, keepdims=True)
        img_temp_float = np.repeat(gray_img_single_channel, 3, axis=2)
    elif effect == "Sepia":
        if img_temp_float.shape[2] < 3:
            # Sepia requires all channels
            return img  # This will be colormapped by Matplotlib
        sepia_matrix = np.array([
            [0.393, 0.769, 0.189],
            [0.349, 0.686, 0.168],
            [0.272, 0.534, 0.131]
        ])
        r, g, b = img_temp_float[..., 0].copy(), img_temp_float[..., 1].copy(), img_temp_float[..., 2].copy()
        img_temp_float[..., 0] = r * sepia_matrix[0, 0] + g * sepia_matrix[0, 1] + b * sepia_matrix[0, 2]
        img_temp_float[..., 1] = r * sepia_matrix[1, 0] + g * sepia_matrix[1, 1] + b * sepia_matrix[1, 2]
        img_temp_float[..., 2] = r * sepia_matrix[2, 0] + g * sepia_matrix[2, 1] + b * sepia_matrix[2, 2]
    elif effect == "Solarize":
        threshold = 128 + 64 + 16
        condition = img_temp_float >= threshold
        img_temp_float[condition] = 255 - img_temp_float[condition]

    # 2. Apply Brightness
    if brightness_offset != 0:
        img_temp_float = img_temp_float + brightness_offset

    # 3. Apply Contrast
    if contrast_factor != 1.0:
        img_temp_float = 128 + contrast_factor * (img_temp_float - 128)

    return np.clip(img_temp_float, 0, 255).astype(np.uint8)


def draw_guidelines(image_array, chunk_size, orientation='vertical', line_thickness=1, line_color_rgb=np.array([255, 0, 0], dtype=np.uint8)):
    """Draws guidelines on an image array."""
    img_with_lines = image_array.copy()
    h, w, _ = img_with_lines.shape

    if orientation == 'vertical':
        for i in range(1, w // chunk_size):
            x = i * chunk_size
            start_x = max(0, x - line_thickness // 2)
            end_x = min(w, x + (line_thickness + 1) // 2)
            if start_x < end_x:
                img_with_lines[:, start_x:end_x, :] = line_color_rgb
    elif orientation == 'horizontal':
        for i in range(1, h // chunk_size):
            y = i * chunk_size
            start_y = max(0, y - line_thickness // 2)
            end_y = min(h, y + (line_thickness + 1) // 2)
            if start_y < end_y:
                img_with_lines[start_y:end_y, :, :] = line_color_rgb
    return img_with_lines
