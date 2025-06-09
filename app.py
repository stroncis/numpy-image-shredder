import gradio as gr

from src.utils import process_image


# This is default UI, which can render layout in a row, so images are too small.
# def run_app():
#     iface = gr.Interface(
#         fn=process_image,
#         inputs=[
#             gr.Textbox(label='Image URL'),
#             gr.Slider(4, 128, step=4, value=16, label='Chunk Width (px)'),
#             gr.Slider(4, 128, step=4, value=16, label='Chunk Height (px)')
#         ],
#         outputs=gr.Image(type='pil', label='Result'),
#         title='Photo Shredder Illusion (Numpy Simulation)',
#         description='Enter an image URL and tweak the chunk sizes to shred and recombine it. Made with NumPy + Gradio.'
#     )
#     iface.launch()

def run_app():
    with gr.Blocks() as demo:
        gr.Markdown("# AIUA6 PP2 Photo Shredder")
        gr.Markdown("## Made with NumPy + Gradio.")
        gr.Markdown("Enter an image URL and tweak the chunk sizes to shred and recombine it.")

        with gr.Column():
            url_input = gr.Textbox(label='Image URL')
            chunk_w_input = gr.Slider(4, 128, step=4, value=16, label='Chunk Width (px)')
            chunk_h_input = gr.Slider(4, 128, step=4, value=16, label='Chunk Height (px)')

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
            return "", 16, 16, None

        clear_button.click(
            fn=clear_inputs_outputs,
            inputs=None,
            outputs=[url_input, chunk_w_input, chunk_h_input, output_image]
        )

    demo.launch()


if __name__ == '__main__':
    run_app()
