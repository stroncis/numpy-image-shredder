import gradio as gr

from src.utils import process_image
from src.config import DEFAULT_IMAGE_URL, DEFAULT_CHUNK_W, DEFAULT_CHUNK_H


def run_app():
    with gr.Blocks(title="NumPy Image Shredder") as demo:
        gr.Markdown("# AIUA6 PP2 Photo Shredder")
        gr.Markdown("## Made with NumPy + Gradio.")
        gr.Markdown("Enter an image URL and tweak the chunk sizes to shred and recombine to simulate it's content multiplication.")

        with gr.Column():
            url_input = gr.Textbox(label='Image URL', value=DEFAULT_IMAGE_URL)
            chunk_w_input = gr.Slider(4, 128, step=4, value=DEFAULT_CHUNK_W, label='Chunk Width (px)')
            chunk_h_input = gr.Slider(4, 128, step=4, value=DEFAULT_CHUNK_H, label='Chunk Height (px)')

        output_image = gr.Image(type='pil', label='Result')

        with gr.Row():
            clear_button = gr.Button("Clear")
            submit_button = gr.Button("Submit")

        submit_button.click(
            fn=process_image,
            inputs=[url_input, chunk_w_input, chunk_h_input],
            outputs=output_image
        )

        def clear_inputs_outputs():
            return DEFAULT_IMAGE_URL, DEFAULT_CHUNK_W, DEFAULT_CHUNK_H, None

        clear_button.click(
            fn=clear_inputs_outputs,
            inputs=None,
            outputs=[url_input, chunk_w_input, chunk_h_input, output_image]
        )

    demo.launch()


if __name__ == '__main__':
    run_app()
