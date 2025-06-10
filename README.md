# NumPy Image Shredder

AIUA6 Practical project 2: A Python application that simulates a photo shredder effect using Numpy. It takes an image URL, divides the image into chunks, rearranges them, and displays the original, vertically shredded, and final "shredded" results.

Optionally added some extra features, numpy processing for color channels.

## Features

*   **Web-Based UI**: Interactive interface built with Gradio.
*   **Image Input via URL**: Users can provide any direct image URL.
*   **Customizable Shredding**:
    *   Adjustable chunk width and height using sliders.
    *   Supports square or rectangular chunks, leading to varied visual effects.
*   **Image Padding**: Input images are automatically padded (using edge pixels) to ensure dimensions are perfectly divisible by the chosen chunk sizes.
*   **Two-Step Shredding Proces (as per requirement)**:
    1.  **Vertical Shredding**: Image is sliced into vertical strips, which are then reordered (even-indexed strips followed by odd-indexed strips).
    2.  **Horizontal Shredding**: The result of vertical shredding is then sliced into horizontal strips, which are similarly reordered.
*   **Visual Output**: Displays three stages of the image:
    1.  Original (Padded) Image
    2.  Image After Vertical Shredding
    3.  Final Recombined (Shredded) Image
*   **Error Handling**: Handles and displays errors in the UI.
*   **Batteries included**: Comes with pre-set default values for the image URL and chunk dimensions for quick testing.
*   **More Functionality**:
    *   Reset inputs to their default values.
    *   Image re-processing automatically on any input change (chunk size changes update results only on release).

## How It Works

1.  **Image Download**: The application fetches an image from the provided URL using the `requests` library. A `User-Agent` header is used to mimic a browser request.
2.  **Image Preparation**:
    *   The downloaded image is converted to a PIL Image object and then to a NumPy array.
    *   The NumPy array is padded using `np.pad` with `mode='edge'` so that its width and height are exact multiples of the user-defined `chunk_width` and `chunk_height`.
3.  **Shredding (`shredder.py`)**:
    *   **Vertical Shredding**: The padded image is sliced into vertical chunks. These chunks are then reassembled by first taking all even-indexed chunks and then all odd-indexed chunks, stacking them horizontally.
    *   **Horizontal Shredding**: The vertically shredded image is then sliced into horizontal chunks. These are reassembled similarly (even-indexed followed by odd-indexed), stacking them vertically to produce the final image.
4.  **Display**:
    *   `matplotlib` is used to create a figure with three subplots showing the original (padded) image, the image after vertical shredding, and the final shredded image.
    *   This figure is saved to an in-memory buffer and converted to a PIL Image, which is then displayed in the Gradio UI.

## Technologies Used

*   **Python 3**
*   **Gradio**: For creating the interactive web UI.
*   **NumPy**: For numerical operations, primarily image manipulation as arrays (slicing, padding, stacking).
*   **Requests**: For downloading images from URLs.
*   **Matplotlib**: For generating and displaying the image outputs (original, intermediate, final).
*   **Pillow (PIL)**: For image file operations (opening, converting).

## Setup and Usage

1.  **Clone the repository (if applicable) or ensure you have all project files.**
2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run the application:**
    ```bash
    python app.py
    ```
5.  Open your web browser and navigate to the URL provided by Gradio (usually `http://127.0.0.1:7860`).

Enter an image URL, adjust the chunk sliders, and click "Submit" to see the shredded image.
