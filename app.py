import gradio as gr
import numpy as np

from src.utils import process_image
from src.config import (
    DEFAULT_IMAGE_URL, DEFAULT_CHUNK_W, DEFAULT_CHUNK_H,
    SAMPLE_IMAGES_DATA, COLOR_EFFECTS, DEFAULT_COLOR_EFFECT,
    DEFAULT_BRIGHTNESS, DEFAULT_CONTRAST, DEFAULT_SHOW_GUIDELINES,
    GUIDELINE_COLORS, DEFAULT_GUIDELINE_COLOR_NAME
)

sample_image_choices = [f"{item['name']} - {item['description']}" for item in SAMPLE_IMAGES_DATA]

# TODO: add another shredding level (making 4x4 image), recursion?
# TODO: padding does not look good, it creates pixel stretching artefacts on the edges.
#       As a solution, mirror the same amount of pixes as the offset instead of repeating last pixel.


def run_app():
    with gr.Blocks(title="NumPy Image Shredder") as demo:
        gr.Markdown("# AIUA6 PP2 Photo Shredder")
        gr.Markdown("## Image slicer and recombinator")
        gr.Markdown(
            "Real world example on a photo print using pasta maker: [Top breeder 🐕](https://youtu.be/f1fXCRtSUWU)")
        gr.Markdown("Enter an image URL and tweak the chunk sizes to shred and recombine to simulate it's content multiplication.")

        # --------------------------------* UI Input Components *--------------------------------

        with gr.Column():
            input_dropdown_sample_images = gr.Dropdown(
                label="Sample Images",
                choices=sample_image_choices,
                value=set_default_choice_str()
            )
            input_field_url = gr.Textbox(label='Image URL', value=DEFAULT_IMAGE_URL)
            with gr.Row():
                input_slider_chunk_w = gr.Slider(4, 128, step=4, value=DEFAULT_CHUNK_W, label='Chunk Width (px)')
                input_slider_chunk_h = gr.Slider(4, 128, step=4, value=DEFAULT_CHUNK_H, label='Chunk Height (px)')

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
                    label="Show Chunk Guidelines", value=DEFAULT_SHOW_GUIDELINES, scale=1)
                input_radio_guideline_color = gr.Radio(
                    label="Guideline Color",
                    choices=list(GUIDELINE_COLORS.keys()),
                    value=DEFAULT_GUIDELINE_COLOR_NAME,
                    scale=3
                )

        output_image_component = gr.Image(type='pil', label='Result', format='png')

        with gr.Row():
            input_button_reset_to_defaults = gr.Button("Reset to defaults")

        # --------------------------------* Event Handlers *--------------------------------

        input_dropdown_sample_images.change(
            fn=update_url_from_sample,
            inputs=input_dropdown_sample_images,
            outputs=[input_field_url, input_slider_brightness, input_slider_contrast,
                     input_checkbox_show_guidelines, input_radio_guideline_color]
        )

        input_fields = [
            input_field_url, input_slider_chunk_w, input_slider_chunk_h,
            input_radio_color_effect, input_slider_brightness, input_slider_contrast,
            input_checkbox_show_guidelines, input_radio_guideline_color
        ]

        # Registering change events
        for input_component in [
            input_field_url, input_radio_color_effect,
            input_checkbox_show_guidelines, input_radio_guideline_color
        ]:
            input_component.change(
                fn=on_any_input_change,
                inputs=input_fields,
                outputs=output_image_component
            )

        # Registering slider release events (to avoid update hoarding)
        for input_component_slider in [
            input_slider_chunk_w, input_slider_chunk_h,
            input_slider_brightness, input_slider_contrast
        ]:
            input_component_slider.release(
                fn=on_any_input_change,
                inputs=input_fields,
                outputs=output_image_component
            )

        input_button_reset_to_defaults.click(
            fn=clear_inputs_outputs,
            inputs=None,
            outputs=[
                input_field_url, input_slider_chunk_w, input_slider_chunk_h,
                input_radio_color_effect, input_slider_brightness, input_slider_contrast,
                input_checkbox_show_guidelines, input_radio_guideline_color,
                output_image_component, input_dropdown_sample_images
            ]
        )

        demo.load(
            fn=load_initial_image,
            inputs=None,
            outputs=output_image_component
        )

    demo.launch()


def load_initial_image():
    _guideline_color_rgb = np.array(GUIDELINE_COLORS[DEFAULT_GUIDELINE_COLOR_NAME], dtype=np.uint8)
    return process_image(
        url=DEFAULT_IMAGE_URL,
        chunk_w=DEFAULT_CHUNK_W,
        chunk_h=DEFAULT_CHUNK_H,
        color_effect=DEFAULT_COLOR_EFFECT,
        brightness_offset=DEFAULT_BRIGHTNESS,
        contrast_factor=DEFAULT_CONTRAST,
        show_guidelines=DEFAULT_SHOW_GUIDELINES,
        guideline_color_rgb_array=_guideline_color_rgb,
        source='Initial Load'
    )


def clear_inputs_outputs():
    _default_choice_str = set_default_choice_str()
    guideline_color_rgb = np.array(GUIDELINE_COLORS[DEFAULT_GUIDELINE_COLOR_NAME], dtype=np.uint8)
    image = process_image(
        url=DEFAULT_IMAGE_URL,
        chunk_w=DEFAULT_CHUNK_W,
        chunk_h=DEFAULT_CHUNK_H,
        color_effect=DEFAULT_COLOR_EFFECT,
        brightness_offset=DEFAULT_BRIGHTNESS,
        contrast_factor=DEFAULT_CONTRAST,
        show_guidelines=DEFAULT_SHOW_GUIDELINES,
        guideline_color_rgb_array=guideline_color_rgb,
        source='Clear Button'
    )
    return (
        DEFAULT_IMAGE_URL, DEFAULT_CHUNK_W, DEFAULT_CHUNK_H,
        DEFAULT_COLOR_EFFECT, DEFAULT_BRIGHTNESS, DEFAULT_CONTRAST,
        DEFAULT_SHOW_GUIDELINES, DEFAULT_GUIDELINE_COLOR_NAME,
        image, _default_choice_str
    )


def update_url_from_sample(selected_choice_str):
    for item in SAMPLE_IMAGES_DATA:
        if f"{item['name']} - {item['description']}" == selected_choice_str:
            return item["image_url"], DEFAULT_BRIGHTNESS, DEFAULT_CONTRAST, DEFAULT_SHOW_GUIDELINES, DEFAULT_GUIDELINE_COLOR_NAME
    return DEFAULT_IMAGE_URL, DEFAULT_BRIGHTNESS, DEFAULT_CONTRAST, DEFAULT_SHOW_GUIDELINES, DEFAULT_GUIDELINE_COLOR_NAME


def on_any_input_change(url, cw, ch, effect, brightness, contrast, guidelines, guideline_color_name):
    guideline_color_rgb = np.array(GUIDELINE_COLORS.get(
        guideline_color_name, GUIDELINE_COLORS[DEFAULT_GUIDELINE_COLOR_NAME]), dtype=np.uint8)
    return process_image(url, cw, ch, effect, brightness, contrast, guidelines, guideline_color_rgb, source='User Input')


def set_default_choice_str():
    _default_choice_str = ""
    for item in SAMPLE_IMAGES_DATA:
        if item["image_url"] == DEFAULT_IMAGE_URL:
            _default_choice_str = f"{item['name']} - {item['description']}"
            break
    return _default_choice_str if _default_choice_str else (sample_image_choices[0] if sample_image_choices else "")


if __name__ == '__main__':
    run_app()
