import os

from .sample_image_metadata import DEFAULT_SAMPLE_IMAGES_DATA  # from .image_updater import get_updated_sample_images

# Output image width in pixels
OUTPUT_IMAGE_WIDTH_IN_PIXELS = 1800
MIN_VALID_OUTPUT_WIDTH = 800

# Output image size in inches
OUTPUT_IMAGE_DPI = 100
OUTPUT_IMAGE_ASPECT_RATIO = 18 / 6.75
OUTPUT_IMAGE_WIDTH = OUTPUT_IMAGE_WIDTH_IN_PIXELS / OUTPUT_IMAGE_DPI
OUTPUT_IMAGE_HEIGHT = OUTPUT_IMAGE_WIDTH * 0.375

# Matlibplot settings
DEFAULT_TITLE_FONT_SIZE = 12

DEFAULT_CHUNK_W = 16
DEFAULT_CHUNK_H = 16
MIN_CHUNK_SIZE_PX = 4
INITIAL_MAX_CHUNK_PX = 256
CHUNK_STEP_PX = 4

DEFAULT_SHOW_GUIDELINES = False
GUIDELINE_COLORS = {
    "Red": [255, 128, 0],
    "Green": [0, 255, 0],
    "Blue": [0, 128, 255],
    "Yellow": [255, 255, 0],
    "Cyan": [0, 255, 255],
    "Magenta": [255, 0, 255],
    "White": [255, 255, 255],
    "Black": [0, 0, 0],
}
DEFAULT_GUIDELINE_COLOR_NAME = "Red"

SAMPLE_IMAGES_DATA = DEFAULT_SAMPLE_IMAGES_DATA  # get_updated_sample_images()
sample_image_choices = [f"{item['name']} - {item['description']}" for item in SAMPLE_IMAGES_DATA]

if SAMPLE_IMAGES_DATA:
    first_item = SAMPLE_IMAGES_DATA[0]
    DEFAULT_IMAGE_URL = first_item.get("image_url") or first_item.get("source_url")
else:
    DEFAULT_IMAGE_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Yellow_flowers_a.jpg/960px-Yellow_flowers_a.jpg"

# Effects for Radio buttons
COLOR_EFFECTS = [
    "None", "Invert Colors", "Swap R/G Channels", "Red Channel Only",
    "Grayscale", "Grayscale 1 Channel", "Sepia", "Solarize"
]
DEFAULT_COLOR_EFFECT = "None"

# Defaults for sliders
DEFAULT_BRIGHTNESS = 0
DEFAULT_CONTRAST = 1.0  # Factor 1.0 means no change
