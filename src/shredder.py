import numpy as np


def shred_image(img, chunk_width, chunk_height):
    h, w, c = img.shape

    chunk_width = int(chunk_width)
    chunk_height = int(chunk_height)

    vertical_chunks = [img[:, i:i + chunk_width, :] for i in range(0, w, chunk_width)]
    stacked_vertical = np.hstack(vertical_chunks[::2] + vertical_chunks[1::2])

    horizontal_chunks = [stacked_vertical[i:i + chunk_height, :, :] for i in range(0, h, chunk_height)]
    final_image = np.vstack(horizontal_chunks[::2] + horizontal_chunks[1::2])

    return stacked_vertical, final_image
