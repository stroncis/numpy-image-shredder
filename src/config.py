import os

from .image_updater import get_updated_sample_images

DEFAULT_CHUNK_W = 16
DEFAULT_CHUNK_H = 16

SAMPLE_IMAGES_DATA = get_updated_sample_images()

if SAMPLE_IMAGES_DATA:
    DEFAULT_IMAGE_URL = SAMPLE_IMAGES_DATA[0]["image_url"]
else:
    DEFAULT_IMAGE_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Yellow_flowers_a.jpg/960px-Yellow_flowers_a.jpg"

# Effects for Radio buttons
COLOR_EFFECTS = [
    "None", "Invert Colors", "Swap R/G Channels", "Red Channel Only", "Grayscale",
    "Sepia", "Solarize"
]
DEFAULT_COLOR_EFFECT = "None"

# Defaults for sliders
DEFAULT_BRIGHTNESS = 0
DEFAULT_CONTRAST = 1.0  # Factor 1.0 means no change
