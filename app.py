import gradio as gr

from src.utils import process_image
from src.config import DEFAULT_IMAGE_URL, DEFAULT_CHUNK_W, DEFAULT_CHUNK_H, SAMPLE_IMAGES_DATA, COLOR_EFFECTS, DEFAULT_COLOR_EFFECT, DEFAULT_BRIGHTNESS, DEFAULT_CONTRAST

sample_image_choices = [f"{item['name']} - {item['description']}" for item in SAMPLE_IMAGES_DATA]


def run_app():
    with gr.Blocks(title="NumPy Image Shredder") as demo:
        gr.Markdown("# AIUA6 PP2 Photo Shredder")
        gr.Markdown("## Made with NumPy + Gradio.")
        gr.Markdown(
            "Real world example on a photo print using pasta maker: [Top breeder 🐕](https://youtu.be/f1fXCRtSUWU)")
        gr.Markdown("Enter an image URL and tweak the chunk sizes to shred and recombine to simulate it's content multiplication.")

        default_choice_str = set_default_choice_str()

        with gr.Column():
            sample_images_dropdown = gr.Dropdown(
                label="Sample Images",
                choices=sample_image_choices,
                value=default_choice_str
            )
            url_input = gr.Textbox(label='Image URL', value=DEFAULT_IMAGE_URL)
            with gr.Row():
                chunk_w_input = gr.Slider(4, 128, step=4, value=DEFAULT_CHUNK_W, label='Chunk Width (px)')
                chunk_h_input = gr.Slider(4, 128, step=4, value=DEFAULT_CHUNK_H, label='Chunk Height (px)')

            color_effect_input = gr.Radio(
                label="Base Color Effect",
                choices=COLOR_EFFECTS,
                value=DEFAULT_COLOR_EFFECT
            )

            with gr.Row():
                brightness_slider = gr.Slider(
                    minimum=-100, maximum=100, step=1, value=DEFAULT_BRIGHTNESS, label="Brightness Offset"
                )
                contrast_slider = gr.Slider(
                    minimum=0.1, maximum=3.0, step=0.1, value=DEFAULT_CONTRAST, label="Contrast Factor"
                )

            # TODO: add sliced part borders to display chunks in final image
            # TODO: add another shredding level (making 4x4 image), recursion?
            # FIXME: problem with padding, it creates pixel stretching artefacts on the edges.
            #        As a solution, mirror the same amount of pixes as the offset instead of repeating last pixel.

        output_image = gr.Image(type='pil', label='Result')

        with gr.Row():
            clear_button = gr.Button("Reset to defaults")

        input_fields = [url_input, chunk_w_input, chunk_h_input, color_effect_input, brightness_slider, contrast_slider]

        def update_url_from_sample(selected_choice_str):
            for item in SAMPLE_IMAGES_DATA:
                if f"{item['name']} - {item['description']}" == selected_choice_str:
                    return item["image_url"], DEFAULT_BRIGHTNESS, DEFAULT_CONTRAST
            return DEFAULT_IMAGE_URL, DEFAULT_BRIGHTNESS, DEFAULT_CONTRAST

        sample_images_dropdown.change(
            fn=update_url_from_sample,
            inputs=sample_images_dropdown,
            outputs=[url_input, brightness_slider, contrast_slider]
        )
        # Introduces race conditions as the url_input can be updated by
        # "update_url_from_sample" later, than the image processing function is called.
        # .then(
        #     fn=process_image,
        #     inputs=input_fields,
        #     outputs=output_image
        # )

        def on_any_input_change(url, cw, ch, effect, brightness, contrast):
            return process_image(url, cw, ch, effect, brightness, contrast)

        for comp in [url_input, color_effect_input, brightness_slider, contrast_slider]:
            comp.change(
                fn=on_any_input_change,
                inputs=input_fields,
                outputs=output_image
            )

        for comp_release in [chunk_w_input, chunk_h_input]:
            comp_release.release(
                fn=on_any_input_change,
                inputs=input_fields,
                outputs=output_image
            )

        def clear_inputs_outputs():
            _default_choice_str = set_default_choice_str()
            image = process_image(
                url=DEFAULT_IMAGE_URL,
                chunk_w=DEFAULT_CHUNK_W,
                chunk_h=DEFAULT_CHUNK_H,
                color_effect=DEFAULT_COLOR_EFFECT,
                brightness_offset=DEFAULT_BRIGHTNESS,
                contrast_factor=DEFAULT_CONTRAST
            )
            return (
                DEFAULT_IMAGE_URL, DEFAULT_CHUNK_W, DEFAULT_CHUNK_H,
                DEFAULT_COLOR_EFFECT, DEFAULT_BRIGHTNESS, DEFAULT_CONTRAST,
                image, _default_choice_str
            )

        clear_button.click(
            fn=clear_inputs_outputs,
            inputs=None,
            outputs=[
                url_input, chunk_w_input, chunk_h_input,
                color_effect_input, brightness_slider, contrast_slider,
                output_image, sample_images_dropdown
            ]
        )

        def load_initial_image():
            return process_image(
                url=DEFAULT_IMAGE_URL,
                chunk_w=DEFAULT_CHUNK_W,
                chunk_h=DEFAULT_CHUNK_H,
                color_effect=DEFAULT_COLOR_EFFECT,
                brightness_offset=DEFAULT_BRIGHTNESS,
                contrast_factor=DEFAULT_CONTRAST
            )

        demo.load(
            fn=load_initial_image,
            inputs=None,
            outputs=output_image
        )

    demo.launch()


def set_default_choice_str():
    _default_choice_str = ""
    for item in SAMPLE_IMAGES_DATA:
        if item["image_url"] == DEFAULT_IMAGE_URL:
            _default_choice_str = f"{item['name']} - {item['description']}"
            break
    return _default_choice_str if _default_choice_str else (sample_image_choices[0] if sample_image_choices else "")

if __name__ == '__main__':
    run_app()
