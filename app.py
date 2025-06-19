import gradio as gr
import numpy as np
from gradio.themes.utils import sizes as theme_sizes  # Because Gradio lookup fails

from src.utils import (
    process_image, get_timestamp, download_image, print_event_data, lock_slider_ratio,
    sync_height_to_width, set_default_choice_str
)
from src.image_updater import get_image_url_from_item
from src.config import (
    DEFAULT_IMAGE_URL, DEFAULT_CHUNK_W, DEFAULT_CHUNK_H,
    MIN_CHUNK_SIZE_PX, INITIAL_MAX_CHUNK_PX, CHUNK_STEP_PX,
    SAMPLE_IMAGES_DATA, COLOR_EFFECTS, DEFAULT_COLOR_EFFECT,
    DEFAULT_BRIGHTNESS, DEFAULT_CONTRAST, DEFAULT_SHOW_GUIDELINES,
    GUIDELINE_COLORS, DEFAULT_GUIDELINE_COLOR_NAME,
    OUTPUT_IMAGE_WIDTH_IN_PIXELS, MIN_VALID_OUTPUT_WIDTH,
    sample_image_choices
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
        is_batch_updating_state = gr.State(value=False)
        chunk_delta_state = gr.State(0)

        # --------------------------------* UI Input Components *--------------------------------

        with gr.Column():
            input_dropdown_sample_images = gr.Dropdown(
                label="Sample Images",
                choices=sample_image_choices,
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
                    label="Show Chunk Guidelines", value=DEFAULT_SHOW_GUIDELINES, scale=1)
                input_radio_guideline_color = gr.Radio(
                    label="Guideline Color",
                    choices=list(GUIDELINE_COLORS.keys()),
                    value=DEFAULT_GUIDELINE_COLOR_NAME,
                    scale=3
                )
                input_field_output_width = gr.Number(
                    label="Output Image Width (px)",
                    value=OUTPUT_IMAGE_WIDTH_IN_PIXELS,
                    precision=0,
                    minimum=MIN_VALID_OUTPUT_WIDTH
                )

        output_image_component = gr.Image(type='pil', show_label=False, format='png')

        with gr.Row():
            input_button_reset_to_defaults = gr.Button("Reset to defaults", elem_id="Reset settings button")

        # --------------------------------* Event Handlers *--------------------------------

        all_input_components = [
            input_dropdown_sample_images, input_textbox_img_url, input_button_update_image,
            input_slider_chunk_w, input_checkbox_chunk_lock_ratio, input_slider_chunk_h, input_radio_color_effect,
            input_slider_brightness, input_slider_contrast, input_checkbox_show_guidelines,
            input_radio_guideline_color, input_field_output_width, input_button_reset_to_defaults
        ]

        for input_component in all_input_components:
            print_event_data(input_component)

        inputs_for_processing_parameters = [
            input_slider_chunk_w, input_slider_chunk_h, input_radio_color_effect,
            input_slider_brightness, input_slider_contrast, input_checkbox_show_guidelines,
            input_radio_guideline_color, input_field_output_width
        ]

        param_change_event_inputs = [
            input_dropdown_sample_images,
            cached_image_url_state, cached_image_array_state,
            *inputs_for_processing_parameters,
            is_batch_updating_state
        ]

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

        input_slider_chunk_h.release(
            fn=on_param_change_handler,
            inputs=param_change_event_inputs,
            outputs=[output_image_component, cached_image_array_state, cached_image_url_state]
        )

        input_button_update_image.click(
            fn=_load_or_use_cached_and_process,
            inputs=[
                input_dropdown_sample_images,
                input_textbox_img_url, cached_image_url_state, cached_image_array_state,
                *inputs_for_processing_parameters,
                gr.State(True), is_batch_updating_state,  # force_download=True, batch_active
                gr.State("Update Button")
            ],
            outputs=[output_image_component, cached_image_array_state, cached_image_url_state]
        )

        # Registering non-sliders change events
        for input_component in [
            input_radio_color_effect, input_checkbox_show_guidelines,
            input_radio_guideline_color, input_field_output_width
        ]:
            input_component.change(
                fn=on_param_change_handler,
                inputs=param_change_event_inputs,
                outputs=[output_image_component, cached_image_array_state, cached_image_url_state]
            )

        # Registering slider release events
        for input_component_slider in [
            input_slider_chunk_w, input_slider_chunk_h,
            input_slider_brightness, input_slider_contrast
        ]:
            input_component_slider.release(
                fn=on_param_change_handler,
                inputs=param_change_event_inputs,
                outputs=[output_image_component, cached_image_array_state, cached_image_url_state]
            )

        input_dropdown_sample_images.change(
            fn=handle_sample_image_selection_and_load,
            inputs=[
                input_dropdown_sample_images,
                # Pass current values of params that are NOT reset by sample selection
                input_slider_chunk_w, input_slider_chunk_h, input_radio_color_effect,
                input_checkbox_show_guidelines, input_radio_guideline_color, input_field_output_width,
                is_batch_updating_state
            ],
            outputs=[
                input_textbox_img_url, input_slider_brightness, input_slider_contrast,
                input_checkbox_show_guidelines, input_radio_guideline_color,
                output_image_component,
                cached_image_array_state, cached_image_url_state
            ]
        ).then(
            fn=lambda: True, outputs=[is_batch_updating_state]
        ).then(
            fn=lambda: False, outputs=[is_batch_updating_state], queue=False
        )

        input_button_reset_to_defaults.click(
            fn=clear_all_and_reload_default_action,
            inputs=[is_batch_updating_state],
            outputs=[
                input_textbox_img_url, input_slider_chunk_w, input_slider_chunk_h,
                input_radio_color_effect, input_slider_brightness, input_slider_contrast,
                input_checkbox_show_guidelines, input_radio_guideline_color, input_field_output_width,
                input_dropdown_sample_images,
                output_image_component,
                cached_image_array_state, cached_image_url_state
            ]
        ).then(
            fn=lambda: True, outputs=[is_batch_updating_state]
        ).then(
            fn=lambda: False, outputs=[is_batch_updating_state], queue=False
        )

        image_shredder_app.load(
            fn=initial_load_action,
            inputs=None,
            outputs=[output_image_component, cached_image_array_state, cached_image_url_state]
        )

    image_shredder_app.launch()


def update_url_from_sample(selected_choice_str):
    for item in SAMPLE_IMAGES_DATA:
        if f"{item['name']} - {item['description']}" == selected_choice_str:
            return item["image_url"], DEFAULT_BRIGHTNESS, DEFAULT_CONTRAST, DEFAULT_SHOW_GUIDELINES, DEFAULT_GUIDELINE_COLOR_NAME
    return DEFAULT_IMAGE_URL, DEFAULT_BRIGHTNESS, DEFAULT_CONTRAST, DEFAULT_SHOW_GUIDELINES, DEFAULT_GUIDELINE_COLOR_NAME


def _get_processing_params(cw, ch, effect, bright, contr, guidelines, guide_color_name, out_width):
    """On input change, gather current processing parameters."""
    guideline_color_rgb = np.array(GUIDELINE_COLORS.get(
        guide_color_name, GUIDELINE_COLORS[DEFAULT_GUIDELINE_COLOR_NAME]), dtype=np.uint8)
    return {
        "chunk_w": int(cw), "chunk_h": int(ch), "color_effect": effect,
        "brightness_offset": bright, "contrast_factor": contr,
        "show_guidelines": guidelines, "guideline_color_rgb_array": guideline_color_rgb,
        "output_image_width": out_width
    }


def _load_or_use_cached_and_process(
    selected_sample_choice_str, url_from_input_field,
    current_cached_url, current_cached_array,
    cw, ch, effect, bright, contr, guidelines, guide_color_name, out_width,
    force_download, batch_update_active,
    source_log_msg="Processing"
):
    """
    Load an image from URL or use cached version, process it, and return the processed image.
    If batch_update_active is True, skip processing and return skips.
    """
    if batch_update_active:
        print(f"{get_timestamp()} Skipping _load_or_use_cached_and_process due to batch update.")
        return (gr.skip(),) * 3  # No changes

    image_array_to_process = None
    new_cached_url = current_cached_url
    new_cached_array = current_cached_array

    final_url_to_process = url_from_input_field
    print(f"{get_timestamp()} force_download {force_download}, source_log_msg {source_log_msg}, Processing image from URL: {url_from_input_field}")

    if force_download:
        item_definition_to_refresh = None

        if source_log_msg == "Update Button":
            selected_item_from_dropdown = None

            if selected_sample_choice_str:
                for item_def in SAMPLE_IMAGES_DATA:
                    if f"{item_def['name']} - {item_def['description']}" == selected_sample_choice_str:
                        selected_item_from_dropdown = item_def
                        break

            if selected_item_from_dropdown:
                is_input_url_canonical_for_dropdown_item = \
                    (url_from_input_field == selected_item_from_dropdown.get("source_url")) or \
                    (selected_item_from_dropdown.get("image_url") and url_from_input_field ==
                     selected_item_from_dropdown.get("image_url"))

                if is_input_url_canonical_for_dropdown_item:
                    # Intent: Refresh the currently selected dropdown item
                    item_definition_to_refresh = selected_item_from_dropdown
                    # print(f"{get_timestamp()} 'Update Button': Refreshing selected sample '{selected_item_from_dropdown['name']}'.")
                else:
                    # Intent: Load the (potentially custom) URL from the input field.
                    # Does this custom URL happen to be a source_url/image_url of *any* (possibly different) sample?
                    for item_def in SAMPLE_IMAGES_DATA:
                        if item_def.get("source_url") == url_from_input_field or \
                           (item_def.get("image_url") and item_def.get("image_url") == url_from_input_field):
                            item_definition_to_refresh = item_def
                            # print(f"{get_timestamp()} 'Update Button': URL in input field ('{url_from_input_field}') matches sample definition '{item_def['name']}'.")
                            break
                    # if not item_definition_to_refresh:
                    #     print(f"{get_timestamp()} 'Update Button': URL in input field ('{url_from_input_field}') is custom, no matching sample definition.")
            else:
                # No dropdown selection, or "Update Button" but dropdown is blank (should not happen with a default)
                # Fallback: check if url_from_input_field matches any sample's base/image_url
                for item_def in SAMPLE_IMAGES_DATA:
                    if item_def.get("source_url") == url_from_input_field or \
                       (item_def.get("image_url") and item_def.get("image_url") == url_from_input_field):
                        item_definition_to_refresh = item_def
                        # print(f"{get_timestamp()} 'Update Button' (no dropdown context or mismatch): Input field URL matches sample '{item_def['name']}'.")
                        break

        elif source_log_msg in ["Initial Load", "Reset Button", "Sample Image Change"]:
            if selected_sample_choice_str:
                for item_def in SAMPLE_IMAGES_DATA:
                    if f"{item_def['name']} - {item_def['description']}" == selected_sample_choice_str:
                        if url_from_input_field == item_def.get("source_url") or \
                           url_from_input_field == item_def.get("image_url"):
                            item_definition_to_refresh = item_def
                            # print(f"{get_timestamp()} '{source_log_msg}': Identified item '{item_def['name']}' from dropdown and matching input URL.")
                        else:
                            # print(f"{get_timestamp()} WARNING '{source_log_msg}': Mismatch between dropdown ('{selected_sample_choice_str}') and input URL ('{url_from_input_field}'). Attempting to find item by input URL.")
                            for fallback_item_def in SAMPLE_IMAGES_DATA:
                                if fallback_item_def.get("source_url") == url_from_input_field or \
                                   (fallback_item_def.get("image_url") and fallback_item_def.get("image_url") == url_from_input_field):
                                    item_definition_to_refresh = fallback_item_def
                                    # print(f"{get_timestamp()} '{source_log_msg}': Fallback found item '{fallback_item_def['name']}' by input URL.")
                                    break
                        break

        if item_definition_to_refresh:
            needs_fresh_url = bool(item_definition_to_refresh.get('scraping')) or \
                item_definition_to_refresh.get('force_url_update', False)

            if needs_fresh_url:
                # print(f"{get_timestamp()} Getting fresh URL for '{item_definition_to_refresh['name']}'. Has scraping: {bool(item_definition_to_refresh.get('scraping'))}, Has force_update: {item_definition_to_refresh.get('force_url_update', False)}")
                fresh_url = get_image_url_from_item(item_definition_to_refresh)  # Uses item's source_url for scraping
                if fresh_url:
                    final_url_to_process = fresh_url
                    # print(f"{get_timestamp()} Using fresh URL: {final_url_to_process}")
        #     else:
        #         print(f"{get_timestamp()} Item '{item_definition_to_refresh['name']}' does not require fresh URL fetching for this operation.")
        # else:
        #     print(f"{get_timestamp()} No specific sample item definition applies. Using URL from input field directly: {final_url_to_process}")

    if force_download or final_url_to_process != current_cached_url or current_cached_array is None:
        print(f"{get_timestamp()} Downloading image from URL: {final_url_to_process}")  # Use final_url_to_process
        try:
            image_array_to_process = download_image(final_url_to_process)  # Use final_url_to_process
            new_cached_array = image_array_to_process
            new_cached_url = final_url_to_process  # Cache the final URL that was actually used
        except Exception as e:
            gr.Error(f"Error downloading image: {str(e)}")
            if final_url_to_process == current_cached_url and current_cached_array is not None:
                print(f"{get_timestamp()} Download failed, using previously cached image for {final_url_to_process}")
                image_array_to_process = current_cached_array
            else:
                return None, current_cached_array, current_cached_url
    else:
        print(f"{get_timestamp()} Using cached image for URL: {final_url_to_process}")
        image_array_to_process = current_cached_array

    if image_array_to_process is None:
        gr.Warning("No image available to process.")
        return None, new_cached_array, new_cached_url  # Removing image, updating cache

    params = _get_processing_params(cw, ch, effect, bright, contr, guidelines, guide_color_name, out_width)
    processed_img = process_image(base_img_array=image_array_to_process, **params,
                                  image_url=final_url_to_process, source=source_log_msg)
    return processed_img, new_cached_array, new_cached_url


def on_param_change_handler(
    selected_sample_choice_str,
    current_cached_url, current_cached_array,
    cw, ch, effect, bright, contr, guidelines, guide_color_name, out_width,
    batch_update_active,
    is_locked=None,
    event_source=None
):
    """
    Handle changes to any UI parameters (sliders, radios, etc.) and process the image.
    If batch_update_active is True, skip processing and return skips.
    """
    if is_locked and event_source == "width":
        return (gr.skip(),) * 3

    if current_cached_array is None:
        gr.Warning("Please load an image first using the URL field and 'Update Image' button.")
        return (gr.skip(),) * 3

    return _load_or_use_cached_and_process(
        selected_sample_choice_str,
        current_cached_url,  # url_from_input_field is the current_cached_url for param changes
        current_cached_url, current_cached_array,
        cw, ch, effect, bright, contr, guidelines, guide_color_name, out_width,
        False, batch_update_active,
        "Param Change"
    )


def handle_sample_image_selection_and_load(
    selected_choice_str,
    cw, ch, effect, _guidelines, _guide_color_name, out_width,
    batch_update_active_flag
):
    """
    Handle selection of a sample image from the dropdown and load it.
    If batch_update_active_flag is True, skip processing and return skips.
    """
    if batch_update_active_flag:
        print(f"{get_timestamp()} Skipping sample selection due to batch update.")
        return (gr.skip(),) * 8

    selected_item = None
    for item in SAMPLE_IMAGES_DATA:
        if f"{item['name']} - {item['description']}" == selected_choice_str:
            selected_item = item
            break

    if not selected_item:
        gr.Warning(f"Could not find sample image: {selected_choice_str}")
        return (gr.skip(),) * 8

    image_url = get_image_url_from_item(selected_item)
    if not image_url:
        gr.Error(f"Could not get image URL for '{selected_item['name']}'")
        return (gr.skip(),) * 8

    new_url = image_url
    new_brightness = DEFAULT_BRIGHTNESS
    new_contrast = DEFAULT_CONTRAST
    new_show_guidelines = DEFAULT_SHOW_GUIDELINES
    new_guideline_color = DEFAULT_GUIDELINE_COLOR_NAME

    processed_img, final_cached_array, final_cached_url = _load_or_use_cached_and_process(
        selected_choice_str,
        new_url,
        gr.State(None), gr.State(None),  # Clearing cache states to force download
        cw, ch, effect, new_brightness, new_contrast,
        new_show_guidelines, new_guideline_color, out_width,
        True, False,  # force_download=True, batch_active=False
        "Sample Image Change"
    )
    return (
        new_url, new_brightness, new_contrast, new_show_guidelines, new_guideline_color,
        processed_img, final_cached_array, final_cached_url
    )


def clear_all_and_reload_default_action(batch_update_active_flag):
    """
    Reset all parameters to their defaults and reload the default image.
    If batch_update_active_flag is True, skip processing and return skips.
    """
    if batch_update_active_flag:
        print(f"{get_timestamp()} Skipping reset due to batch update.")
        return (gr.skip(),) * 13

    print(f"{get_timestamp()} Resetting to defaults and reloading image.")

    default_choice_str = set_default_choice_str()
    processed_img, final_cached_array, final_cached_url = _load_or_use_cached_and_process(
        default_choice_str,
        DEFAULT_IMAGE_URL, gr.State(None), gr.State(None),
        DEFAULT_CHUNK_W, DEFAULT_CHUNK_H, DEFAULT_COLOR_EFFECT,
        DEFAULT_BRIGHTNESS, DEFAULT_CONTRAST, DEFAULT_SHOW_GUIDELINES,
        DEFAULT_GUIDELINE_COLOR_NAME, OUTPUT_IMAGE_WIDTH_IN_PIXELS,
        True, False,  # force_download=True, batch_active=False
        "Reset Button"
    )

    return (
        final_cached_url, DEFAULT_CHUNK_W, DEFAULT_CHUNK_H,
        DEFAULT_COLOR_EFFECT, DEFAULT_BRIGHTNESS, DEFAULT_CONTRAST,
        DEFAULT_SHOW_GUIDELINES, DEFAULT_GUIDELINE_COLOR_NAME, OUTPUT_IMAGE_WIDTH_IN_PIXELS,
        default_choice_str,
        processed_img,
        final_cached_array, final_cached_url
    )


def initial_load_action():
    """
    Load the initial image when the app starts.
    This is called when the app is first loaded.
    """
    print(f"{get_timestamp()} Initial image load.")

    default_choice_str = set_default_choice_str()
    processed_img, initial_cached_array, initial_cached_url = _load_or_use_cached_and_process(
        default_choice_str,
        DEFAULT_IMAGE_URL,
        None, None,  # current_cached_url, current_cached_array
        DEFAULT_CHUNK_W, DEFAULT_CHUNK_H, DEFAULT_COLOR_EFFECT,
        DEFAULT_BRIGHTNESS, DEFAULT_CONTRAST, DEFAULT_SHOW_GUIDELINES,
        DEFAULT_GUIDELINE_COLOR_NAME, OUTPUT_IMAGE_WIDTH_IN_PIXELS,
        True, False,  # force_download=True, batch_active=False
        "Initial Load"
    )
    return processed_img, initial_cached_array, initial_cached_url


if __name__ == '__main__':
    run_app()
