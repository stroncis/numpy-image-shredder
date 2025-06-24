import datetime
from io import BytesIO

import requests
import numpy as np
import gradio as gr

from PIL import Image, UnidentifiedImageError

from src.shredder import shred_image
from src.config import (
    OUTPUT_IMAGE_DPI, OUTPUT_IMAGE_ASPECT_RATIO, OUTPUT_IMAGE_WIDTH_IN_PIXELS,
    MIN_VALID_OUTPUT_WIDTH, DEFAULT_TITLE_FONT_SIZE, MIN_CHUNK_SIZE_PX, INITIAL_MAX_CHUNK_PX,
    SAMPLE_IMAGES_DATA, DEFAULT_IMAGE_URL, DEFAULT_ERROR_DURATION, SAMPLE_IMAGE_CHOICES,
    CHUNK_RATIO_LOCKED_LABEL, CHUNK_RATIO_UNLOCKED_LABEL
)

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
    try:
        response = requests.get(url, headers=headers)
    except Exception as e:
        print(f"{get_timestamp()} ⚠️ Failed to download image from URL: {url}\nError: {e}")
        raise gr.Error(
            f"URL: {url}\nError: {e}",
            duration=DEFAULT_ERROR_DURATION,
            title="Image Download Error"
        )

    # response.raise_for_status()
    if response.status_code != 200:
        print(f"{get_timestamp()} ⚠️ Failed to download image. Status code {response.status_code} for URL: {url}")
        raise gr.Error(
            f"Response status code: {response.status_code} from URL: {url}",
            duration=DEFAULT_ERROR_DURATION,
            title="Image Download Error",
            # print_exception=False
        )

    content_type = response.headers.get('Content-Type', '').lower()
    if not content_type.startswith('image/'):
        print(f"{get_timestamp()} ⚠️ URL does not point to an image. Content-Type: '{content_type}'. URL: {url}")
        raise gr.Error(
            f"URL does not point to an image. Content-Type: '{content_type}'. URL: {url}",
            duration=DEFAULT_ERROR_DURATION,
            title="Image Download Error"
        )

    try:
        img = Image.open(BytesIO(response.content)).convert('RGB')
    except UnidentifiedImageError as e:
        print(f"{get_timestamp()} ⚠️ Cannot identify image file. Content-Type: '{content_type}'. URL: '{url}'")
        raise gr.Error(
            f"Cannot identify image type. URL: '{url}'\nError: {e}",
            duration=DEFAULT_ERROR_DURATION,
            title="Image Processing Error (Pillow)"
        )
    return np.array(img)


def pad_image_to_fit_chunks(img, chunk_width, chunk_height):
    img_h, img_w, _ = img.shape
    pad_h = (chunk_height - (img_h % chunk_height)) % chunk_height
    pad_w = (chunk_width - (img_w % chunk_width)) % chunk_width
    padded_img = np.pad(img, ((0, pad_h), (0, pad_w), (0, 0)), mode='edge')
    return padded_img


def validate_inputs(
    chunk_w, chunk_h, brightness_offset, contrast_factor, output_image_width
):
    """
    Validate the input parameters for the image processing function.
    Raises gr.Error with appropriate messages if validation fails.
    """
    try:
        chunk_w = int(chunk_w)
        chunk_h = int(chunk_h)
    except (TypeError, ValueError):
        raise gr.Error(
            "Chunk width and height must be valid integer numbers. Please check your input.",
            duration=DEFAULT_ERROR_DURATION,
            title="Inputs Validation"
        )

    if chunk_w < 2 or chunk_h < 2:
        raise gr.Error(
            "Chunk size too small. Minimum is 2px.",
            duration=DEFAULT_ERROR_DURATION,
            title="Inputs Validation"
        )

    try:
        brightness_offset = int(brightness_offset)
    except (TypeError, ValueError):
        raise gr.Error(
            "Brightness must be valid integer number. Please check your input.",
            duration=DEFAULT_ERROR_DURATION,
            title="Inputs Validation"
        )

    try:
        contrast_factor = float(contrast_factor)
    except (TypeError, ValueError):
        raise gr.Error(
            "Contrast must be valid float number. Please check your input.",
            duration=DEFAULT_ERROR_DURATION,
            title="Inputs Validation"
        )

    try:
        output_image_width = int(output_image_width)
    except (TypeError, ValueError):
        raise gr.Error(
            "Output image width must be a valid integer number. Please check your input.",
            duration=DEFAULT_ERROR_DURATION,
            title="Inputs Validation"
        )


def process_image(
    base_img_array,
    chunk_w,
    chunk_h,
    color_effects,
    brightness_offset,
    contrast_factor,
    show_guidelines,
    guideline_color_rgb_array,
    output_image_width,
    image_url=None,
    caller=None
):
    """
        Process the input image by applying shredding and color effects.
        Returns the processed image as a PIL Image object.
        Raises gr.Error with appropriate messages if validation fails or processing errors occur.
    """
    try:
        validate_inputs(chunk_w, chunk_h, brightness_offset, contrast_factor, output_image_width)
    except gr.Error as e:
        raise e
    if base_img_array is None or not isinstance(base_img_array, np.ndarray):
        raise gr.Error("No image loaded or invalid image data.", duration=DEFAULT_ERROR_DURATION)

    if output_image_width is None or not isinstance(output_image_width, (int, float)) or output_image_width < MIN_VALID_OUTPUT_WIDTH:
        raise gr.Error(
            f"Output image width must be a positive number. Received: '{output_image_width}'. Please enter a valid width (e.g., >= {MIN_VALID_OUTPUT_WIDTH}px).",
            duration=DEFAULT_ERROR_DURATION
        )

    # When chunk sliders locked, non interactive chunk height returns 'str' instead of 'int'
    chunk_w = int(chunk_w)
    chunk_h = int(chunk_h)

    # if caller:
    #     print(f"{get_timestamp()} Processing image invoked from {caller} with URL: {image_url}")

    padded_img = pad_image_to_fit_chunks(base_img_array, chunk_w, chunk_h)
    img_after_effects = apply_color_effect(padded_img, color_effects, brightness_offset, contrast_factor)

    vertical_shred, final_shred = shred_image(img_after_effects, chunk_w, chunk_h)

    display_vertical_shred = vertical_shred
    display_final_shred = final_shred

    if show_guidelines:
        display_vertical_shred = draw_guidelines(
            vertical_shred, chunk_w, orientation='vertical', line_color_rgb=guideline_color_rgb_array)
        display_final_shred = draw_guidelines(
            final_shred, chunk_h, orientation='horizontal', line_color_rgb=guideline_color_rgb_array)

    effects_applied_list = []
    if color_effects:
        effects_applied_list.extend(color_effects)
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
        raise gr.Error("Output Image DPI in configuration cannot be zero.", duration=DEFAULT_ERROR_DURATION)

    padded_h, padded_w, _ = padded_img.shape
    if padded_h == 0 or padded_w == 0:
        input_aspect_ratio = OUTPUT_IMAGE_ASPECT_RATIO  # Fallback
    else:
        input_aspect_ratio = padded_w / padded_h

    dynamic_output_image_height_px = (output_image_width / (input_aspect_ratio * 3)) + (scaled_title_fontsize * 4)

    fig_w = output_image_width / current_dpi
    fig_h = dynamic_output_image_height_px / current_dpi

    if fig_w <= 0 or fig_h <= 0:
        raise gr.Error(
            f"Calculated figure dimensions are invalid (width: {fig_w:.2f}in, height: {fig_h:.2f}in). "
            f"Please check output width ({output_image_width}px) and aspect ratio ({OUTPUT_IMAGE_ASPECT_RATIO}).",
            duration=DEFAULT_ERROR_DURATION
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

    fig.text(
        0.5,
        0.01,
        str(image_url) if image_url else "",
        ha='center',
        va='bottom',
        fontsize=scaled_title_fontsize,
        color='#888888',
        wrap=True
    )

    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_result = Image.open(buf)
    plt.close(fig)

    return img_result


def apply_color_effect(img, effects_list, brightness_offset, contrast_factor):
    img_temp_float = img.astype(np.float32)

    if not effects_list:
        effects_list = []

    for effect in effects_list:
        if effect == "Invert Colors":
            img_temp_float = 255 - img_temp_float
        elif effect == "Swap R/G Channels":
            if img_temp_float.ndim < 3 or img_temp_float.shape[2] < 3:
                print(f"Warning: '{effect}' effect skipped as image does not have 3 channels.")
                continue
            temp_swap = img_temp_float.copy()
            temp_swap[..., 0], temp_swap[..., 1] = temp_swap[..., 1].copy(), temp_swap[..., 0].copy()
            img_temp_float = temp_swap
        elif effect == "Red Channel Only":
            if img_temp_float.ndim < 3 or img_temp_float.shape[2] < 3:
                print(f"Warning: '{effect}' effect skipped as image does not have 3 channels.")
                continue
            temp_red = img_temp_float.copy()
            temp_red[..., 1:] = 0
            img_temp_float = temp_red
        elif effect == "Grayscale":
            if img_temp_float.ndim < 3:
                print(f"Warning: '{effect}' effect skipped as image does not have color channels.")
                continue
            gray_img_single_channel = np.mean(img_temp_float, axis=2, keepdims=True)
            img_temp_float = np.repeat(gray_img_single_channel, 3, axis=2)
        elif effect == "Grayscale 1 Channel":
            if img_temp_float.ndim < 3:
                print(f"Warning: '{effect}' effect skipped as image does not have color channels.")
                continue
            img_temp_float = np.mean(img_temp_float, axis=2, keepdims=True)
        elif effect == "Sepia":
            if img_temp_float.ndim < 3 or img_temp_float.shape[2] < 3:
                print(f"Warning: '{effect}' effect skipped as image does not have 3 channels.")
                continue
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

    if brightness_offset != 0:
        img_temp_float = img_temp_float + brightness_offset

    if contrast_factor != 1.0:
        img_temp_float = 128 + contrast_factor * (img_temp_float - 128)

    return np.clip(img_temp_float, 0, 255).astype(np.uint8)


def ensure_three_channels(img):
    if img.ndim == 2:
        # (H, W) -> (H, W, 3)
        return np.repeat(img[:, :, np.newaxis], 3, axis=2)
    elif img.ndim == 3 and img.shape[2] == 1:
        # (H, W, 1) -> (H, W, 3)
        return np.repeat(img, 3, axis=2)
    return img


def draw_guidelines(image_array, chunk_size, orientation='vertical', line_thickness=1, line_color_rgb=np.array([255, 0, 0], dtype=np.uint8)):
    """Draws guidelines on an image array."""
    img_with_lines = image_array.copy()
    # Check if the image is 1 channel or RGB
    if img_with_lines.ndim == 2 or (img_with_lines.ndim == 3 and img_with_lines.shape[2] == 1):
        # Grayscale image
        h, w = img_with_lines.shape[:2]
        line_value = 255 if np.mean(line_color_rgb) > 128 else 0
        if orientation == 'vertical':
            for i in range(1, w // chunk_size):
                x = i * chunk_size
                start_x = max(0, x - line_thickness // 2)
                end_x = min(w, x + (line_thickness + 1) // 2)
                if start_x < end_x:
                    if img_with_lines.ndim == 2:
                        img_with_lines[:, start_x:end_x] = line_value
                    else:
                        img_with_lines[:, start_x:end_x, 0] = line_value
        elif orientation == 'horizontal':
            for i in range(1, h // chunk_size):
                y = i * chunk_size
                start_y = max(0, y - line_thickness // 2)
                end_y = min(h, y + (line_thickness + 1) // 2)
                if start_y < end_y:
                    if img_with_lines.ndim == 2:
                        img_with_lines[start_y:end_y, :] = line_value
                    else:
                        img_with_lines[start_y:end_y, :, 0] = line_value
    else:
        # RGB image processing
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


def set_default_choice_str():
    """
        Set the default choice string based on the sample images data.
        If no matching image URL is found, return the first choice or an empty string.
    """
    _default_choice_str = ""
    for item in SAMPLE_IMAGES_DATA:
        if item.get("image_url") == DEFAULT_IMAGE_URL:
            _default_choice_str = f"{item['name']} - {item['description']}"
            break
    return _default_choice_str if _default_choice_str else (SAMPLE_IMAGE_CHOICES[0] if SAMPLE_IMAGE_CHOICES else "")


def lock_slider_ratio(is_locked, width_val, height_val):
    if is_locked:
        delta = height_val - width_val
        return delta, gr.update(interactive=False), gr.update(label=CHUNK_RATIO_LOCKED_LABEL)
    else:
        return 0, gr.update(interactive=True), gr.update(label=CHUNK_RATIO_UNLOCKED_LABEL)


def sync_height_to_width(is_locked, width_val, delta):
    if is_locked:
        new_height = width_val + delta
        # Clamping values
        new_height = np.clip(new_height, MIN_CHUNK_SIZE_PX, INITIAL_MAX_CHUNK_PX)
        return gr.update(value=new_height)
    else:
        return gr.skip()


def print_event_data(input_component):
    def print_event_string(label, comp_type, event_type, value):
        print(f"{get_timestamp()} 🛎️  {event_type} from {comp_type} '{label}' event value: {value}")

    if isinstance(input_component, gr.Button):
        input_component.click(
            fn=print_event_string,
            inputs=[
                gr.State(input_component.elem_id or "Unknown Id"),
                gr.State(type(input_component).__name__),
                gr.State("click"),
                input_component
            ],
            outputs=None
        )
    elif isinstance(input_component, gr.Textbox):
        input_component.submit(
            fn=print_event_string,
            inputs=[
                gr.State(input_component.label or "Unknown Label"),
                gr.State(type(input_component).__name__),
                gr.State("submit"),
                input_component
            ],
            outputs=None
        )
    elif isinstance(input_component, gr.Slider):
        input_component.release(
            fn=print_event_string,
            inputs=[
                gr.State(input_component.label or "Unknown Label"),
                gr.State(type(input_component).__name__),
                gr.State("release"),
                input_component
            ],
            outputs=None
        )
    else:
        input_component.change(
            fn=print_event_string,
            inputs=[
                gr.State(input_component.label or "Unknown Label"),
                gr.State(type(input_component).__name__),
                gr.State("change"),
                input_component
            ],
            outputs=None
        )
    return
