import gradio as gr
import numpy as np
from gradio.themes.utils import sizes as theme_sizes  # Because Gradio lookup fails

from src.utils import (
    process_image, download_image, print_event_data, set_default_choice_str,
    lock_slider_ratio, sync_height_to_width, validate_inputs
)
from src.image_updater import get_image_url_from_item
from src.config import (
    DEFAULT_IMAGE_URL, DEFAULT_CHUNK_W, DEFAULT_CHUNK_H,
    MIN_CHUNK_SIZE_PX, INITIAL_MAX_CHUNK_PX, CHUNK_STEP_PX,
    SAMPLE_IMAGES_DATA, COLOR_EFFECTS, DEFAULT_COLOR_EFFECT,
    DEFAULT_BRIGHTNESS, DEFAULT_CONTRAST, DEFAULT_SHOW_GUIDELINES,
    GUIDELINE_COLORS, DEFAULT_GUIDELINE_COLOR_NAME,
    OUTPUT_IMAGE_WIDTH_IN_PIXELS, MIN_VALID_OUTPUT_WIDTH,
    DEFAULT_ERROR_DURATION, SAMPLE_IMAGE_CHOICES
)


def run_app():
    css = """
        .load-button { background-color: #FF5733 !important; color: white !important; }
    """
    with gr.Blocks(
        title="NumPy Image Shredder",
        theme=gr.themes.Citrus(  # type: ignore
            secondary_hue="orange",
            spacing_size=theme_sizes.spacing_md,
        ).set(
            button_primary_shadow_hover="none",
            button_primary_shadow="none",
            button_primary_shadow_active="none",
            button_secondary_shadow_hover="none",
            button_secondary_shadow="none",
            button_secondary_shadow_active="none",
            input_shadow="none",
            input_shadow_focus="none",
            block_shadow="none",
            button_primary_shadow_hover_dark="none",
            button_primary_shadow_dark="none",
            button_primary_shadow_active_dark="none",
            button_secondary_shadow_hover_dark="none",
            button_secondary_shadow_dark="none",
            button_secondary_shadow_active_dark="none",
            input_shadow_dark="none",
            input_shadow_focus_dark="none",
            block_shadow_dark="none"
        ),
        css=css
    ) as image_shredder_app:
        gr.Markdown("# AIUA6 PP2 Photo Shredder")
        gr.Markdown("## Image slicer and recombinator")
        gr.Markdown(
            "Real world example on a photo print using pasta maker: [Top breeder 🐕](https://youtu.be/f1fXCRtSUWU)")
        gr.Markdown("Enter an image URL and tweak the chunk sizes to shred and recombine to simulate it's content multiplication.")

        cached_image_array_state = gr.State(None)
        cached_image_url_state = gr.State(None)
        chunk_delta_state = gr.State(0)

        # --------------------------------* UI Input Components *--------------------------------

        with gr.Column():
            input_dropdown_sample_images = gr.Dropdown(
                label="Sample Images",
                choices=SAMPLE_IMAGE_CHOICES,
                value=set_default_choice_str()
            )

            with gr.Row(equal_height=True):
                input_textbox_img_url = gr.Textbox(label='Image URL', value=DEFAULT_IMAGE_URL, scale=6)
                input_button_update_image = gr.Button(
                    "Reload image", elem_id="Reload button", scale=1, min_width=10, elem_classes=["load-button"])

            with gr.Row():
                input_slider_chunk_w = gr.Slider(
                    minimum=MIN_CHUNK_SIZE_PX,
                    maximum=INITIAL_MAX_CHUNK_PX,
                    step=CHUNK_STEP_PX,
                    value=DEFAULT_CHUNK_W,
                    label='Chunk Width (px)',
                    scale=10
                )
                input_checkbox_chunk_lock_ratio = gr.Checkbox(
                    label="🔒",
                    value=False,
                    scale=1,
                    min_width=50
                )
                input_slider_chunk_h = gr.Slider(
                    minimum=MIN_CHUNK_SIZE_PX,
                    maximum=INITIAL_MAX_CHUNK_PX,
                    step=CHUNK_STEP_PX,
                    value=DEFAULT_CHUNK_H,
                    label='Chunk Height (px)',
                    scale=10,
                    interactive=True
                )

            input_radio_color_effect = gr.Radio(
                label="Base Color Effect",
                choices=COLOR_EFFECTS,
                value=DEFAULT_COLOR_EFFECT
            )

            with gr.Row():
                input_slider_brightness = gr.Slider(
                    minimum=-100, maximum=100, step=1, value=DEFAULT_BRIGHTNESS, label="Brightness Offset"
                )
                input_slider_contrast = gr.Slider(
                    minimum=0.1, maximum=3.0, step=0.1, value=DEFAULT_CONTRAST, label="Contrast Factor"
                )

            with gr.Row():
                input_checkbox_show_guidelines = gr.Checkbox(
                    label="Show Guidelines",
                    value=DEFAULT_SHOW_GUIDELINES,
                    scale=2
                )
                input_dropdown_guideline_color = gr.Dropdown(
                    label="Guideline Color",
                    choices=list(GUIDELINE_COLORS.keys()),
                    value=DEFAULT_GUIDELINE_COLOR_NAME,
                    scale=3
                )
                input_field_output_width = gr.Number(
                    label="Output Image Width (px)",
                    value=OUTPUT_IMAGE_WIDTH_IN_PIXELS,
                    precision=0,
                    minimum=MIN_VALID_OUTPUT_WIDTH,
                    scale=3,
                    maximum=10000
                )

        output_image_component = gr.Image(type='pil', show_label=False, format='png')

        with gr.Row():
            input_button_reset_to_defaults = gr.Button("Reset to defaults", elem_id="Reset settings button")

        # --------------------------------* Event Handlers *--------------------------------

        all_input_components = [
            input_dropdown_sample_images, input_textbox_img_url, input_button_update_image,
            input_slider_chunk_w, input_checkbox_chunk_lock_ratio, input_slider_chunk_h, input_radio_color_effect,
            input_slider_brightness, input_slider_contrast, input_checkbox_show_guidelines,
            input_dropdown_guideline_color, input_field_output_width, input_button_reset_to_defaults
        ]

        for input_component in all_input_components:
            print_event_data(input_component)

        input_dropdown_sample_images.change(
            fn=fetch_and_process_image,
            inputs=[
                input_dropdown_sample_images, input_textbox_img_url,
                input_slider_chunk_w, input_slider_chunk_h, input_radio_color_effect,
                input_slider_brightness, input_slider_contrast,
                input_checkbox_show_guidelines, input_dropdown_guideline_color, input_field_output_width
            ],
            outputs=[output_image_component, input_textbox_img_url, cached_image_array_state, cached_image_url_state]
        )

        input_button_update_image.click(
            fn=fetch_and_process_image,
            inputs=[
                input_dropdown_sample_images, input_textbox_img_url,
                input_slider_chunk_w, input_slider_chunk_h, input_radio_color_effect,
                input_slider_brightness, input_slider_contrast,
                input_checkbox_show_guidelines, input_dropdown_guideline_color, input_field_output_width
            ],
            outputs=[output_image_component, input_textbox_img_url, cached_image_array_state, cached_image_url_state]
        )

        input_textbox_img_url.submit(
            fn=fetch_and_process_image,
            inputs=[
                input_dropdown_sample_images, input_textbox_img_url,
                input_slider_chunk_w, input_slider_chunk_h, input_radio_color_effect,
                input_slider_brightness, input_slider_contrast,
                input_checkbox_show_guidelines, input_dropdown_guideline_color, input_field_output_width
            ],
            outputs=[output_image_component, input_textbox_img_url, cached_image_array_state, cached_image_url_state]
        )

        for input_component in [
            input_slider_chunk_w, input_slider_chunk_h, input_radio_color_effect,
            input_slider_brightness, input_slider_contrast,
            input_checkbox_show_guidelines, input_field_output_width
        ]:
            input_component.change(
                fn=redraw_image,
                inputs=[
                    cached_image_array_state, cached_image_url_state,
                    input_slider_chunk_w, input_slider_chunk_h, input_radio_color_effect,
                    input_slider_brightness, input_slider_contrast,
                    input_checkbox_show_guidelines, input_dropdown_guideline_color, input_field_output_width
                ],
                outputs=[output_image_component, cached_image_array_state, cached_image_url_state]
            )

        input_dropdown_guideline_color.change(
            fn=redraw_if_guidelines,
            inputs=[
                input_checkbox_show_guidelines,
                cached_image_array_state, cached_image_url_state,
                input_slider_chunk_w, input_slider_chunk_h, input_radio_color_effect,
                input_slider_brightness, input_slider_contrast,
                input_checkbox_show_guidelines, input_dropdown_guideline_color, input_field_output_width
            ],
            outputs=[output_image_component, cached_image_array_state, cached_image_url_state]
        )

        input_button_reset_to_defaults.click(
            fn=reset_inputs_and_redraw,
            inputs=[],
            outputs=[
                input_dropdown_sample_images, input_textbox_img_url,
                input_slider_chunk_w, input_slider_chunk_h, input_radio_color_effect,
                input_slider_brightness, input_slider_contrast,
                input_checkbox_show_guidelines, input_dropdown_guideline_color, input_field_output_width,
                output_image_component, cached_image_array_state, cached_image_url_state
            ]
        )

        slider_sync_triggers = [input_checkbox_chunk_lock_ratio, input_slider_chunk_w]

        input_checkbox_chunk_lock_ratio.change(
            fn=lock_slider_ratio,
            inputs=[*slider_sync_triggers, input_slider_chunk_h],
            outputs=[chunk_delta_state, input_slider_chunk_h]
        )

        input_slider_chunk_w.release(
            fn=sync_height_to_width,
            inputs=[input_checkbox_chunk_lock_ratio, input_slider_chunk_w, chunk_delta_state],
            outputs=[input_slider_chunk_h]
        )

        image_shredder_app.load(
            fn=initial_load_action,
            inputs=[],
            outputs=[
                input_dropdown_sample_images, input_textbox_img_url,
                input_slider_chunk_w, input_slider_chunk_h, input_radio_color_effect,
                input_slider_brightness, input_slider_contrast,
                input_checkbox_show_guidelines, input_dropdown_guideline_color, input_field_output_width,
                output_image_component, cached_image_array_state, cached_image_url_state
            ]
        )

    image_shredder_app.launch()


def redraw_if_guidelines(show_guidelines, *args):
    if show_guidelines:
        return redraw_image(*args)
    else:
        return gr.skip(), gr.skip(), gr.skip()


def fetch_and_process_image(
    selected_sample_choice_str,
    url_from_input_field,
    chunk_w, chunk_h, color_effect,
    brightness_offset, contrast_factor,
    show_guidelines, guideline_color_name, output_image_width
):
    """
        Fetches (scrapes if needed) and processes the image.
        Returns: processed_img, new_image_url, new_cached_array, new_cached_url
    """
    try:
        validate_inputs(chunk_w, chunk_h, brightness_offset, contrast_factor, output_image_width)

        image_url = url_from_input_field
        used_sample = None

        if selected_sample_choice_str:
            for item in SAMPLE_IMAGES_DATA:
                if f"{item['name']} - {item['description']}" == selected_sample_choice_str:
                    used_sample = item
                    break

        if used_sample:
            if used_sample.get("scraping"):
                image_url = get_image_url_from_item(used_sample)
            else:
                image_url = used_sample.get("image_url") or used_sample.get("source_url")

        try:
            img_array = download_image(image_url)
        except Exception as e:
            raise gr.Error(f"Error downloading image: {str(e)}", duration=DEFAULT_ERROR_DURATION)

        guideline_color_rgb = np.array(GUIDELINE_COLORS.get(
            guideline_color_name, GUIDELINE_COLORS[DEFAULT_GUIDELINE_COLOR_NAME]), dtype=np.uint8)
        processed_img = process_image(
            base_img_array=img_array,
            chunk_w=chunk_w, chunk_h=chunk_h,
            color_effect=color_effect,
            brightness_offset=brightness_offset,
            contrast_factor=contrast_factor,
            show_guidelines=show_guidelines,
            guideline_color_rgb_array=guideline_color_rgb,
            output_image_width=output_image_width,
            image_url=image_url
        )
        return processed_img, image_url, img_array, image_url
    except gr.Error:
        raise
    except Exception as e:
        raise gr.Error(f"An unexpected error occurred: {e}", duration=DEFAULT_ERROR_DURATION)


def redraw_image(
    img_array, image_url,
    chunk_w, chunk_h, color_effect,
    brightness_offset, contrast_factor,
    show_guidelines, guideline_color_name, output_image_width
):
    """
    Processes the already-fetched image with new parameters.
    """
    try:
        validate_inputs(chunk_w, chunk_h, brightness_offset, contrast_factor, output_image_width)
        if img_array is None:
            raise gr.Error("No image loaded. Please fetch an image first.", duration=DEFAULT_ERROR_DURATION)

        guideline_color_rgb = np.array(GUIDELINE_COLORS.get(
            guideline_color_name, GUIDELINE_COLORS[DEFAULT_GUIDELINE_COLOR_NAME]), dtype=np.uint8)
        processed_img = process_image(
            base_img_array=img_array,
            chunk_w=chunk_w, chunk_h=chunk_h,
            color_effect=color_effect,
            brightness_offset=brightness_offset,
            contrast_factor=contrast_factor,
            show_guidelines=show_guidelines,
            guideline_color_rgb_array=guideline_color_rgb,
            output_image_width=output_image_width,
            image_url=image_url
        )
        return processed_img, img_array, image_url
    except gr.Error:
        raise
    except Exception as e:
        raise gr.Error(f"An unexpected error occurred: {e}", duration=DEFAULT_ERROR_DURATION)


def initial_load_action():
    return reset_inputs_and_redraw()


def reset_inputs_and_redraw():
    default_choice_str = set_default_choice_str()
    default_url = DEFAULT_IMAGE_URL
    default_chunk_w = DEFAULT_CHUNK_W
    default_chunk_h = DEFAULT_CHUNK_H
    default_color_effect = DEFAULT_COLOR_EFFECT
    default_brightness = DEFAULT_BRIGHTNESS
    default_contrast = DEFAULT_CONTRAST
    default_show_guidelines = DEFAULT_SHOW_GUIDELINES
    default_guideline_color = DEFAULT_GUIDELINE_COLOR_NAME
    default_output_width = OUTPUT_IMAGE_WIDTH_IN_PIXELS

    processed_img, image_url, img_array, cached_url = fetch_and_process_image(
        default_choice_str, default_url,
        default_chunk_w, default_chunk_h, default_color_effect,
        default_brightness, default_contrast,
        default_show_guidelines, default_guideline_color, default_output_width
    )

    return (
        default_choice_str, image_url, default_chunk_w, default_chunk_h,
        default_color_effect, default_brightness, default_contrast,
        default_show_guidelines, default_guideline_color, default_output_width,
        processed_img, img_array, cached_url
    )


if __name__ == '__main__':
    run_app()
