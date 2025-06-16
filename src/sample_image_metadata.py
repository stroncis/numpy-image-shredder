# Default data for JSON file, which could be corrupted on url update.
# Scraping metadata is intended to be used for SSR only, though could be easily applied to CSR capable libs.
# Some image URLs require parsing or transformation before usage, parsing regex instructions also included.
DEFAULT_SAMPLE_IMAGES_DATA = [
    {
        "name": "🔄\u2003Let's breed smarties",
        "description": "Good boy/girl alert!",
        "base_url": "https://dog.ceo/api/breeds/image/random",
        "license": "Public domain (Dog CEO)",
        "force_url_update": True,
        "scraping": {
            "image_selector_regex": "\"message\":\"([^\"]+)\"",  # This API returns JSON with an image URL
            "url_transform_regex": "\\\\/",  # Wipe escapes
            "url_transform_replacement": "/"
        }
    },
    {
        "name": "1️⃣\u2003Stefan Sagmeister's book cover",
        "description": "Apply 'Swap R/G Channels' or 'Red Channel Only' for the best effect",
        "base_url": "https://www.leboncoin.fr/ad/livres/2856453141",
        "image_url": "https://img.leboncoin.fr/api/v1/lbcpb1/images/25/04/85/25048572a1c62486c5f84c01a3386c59b2b23c61.jpg?rule=ad-large",
        "license": "Unknown"
    },
    {
        "name": "🔄\u2003This Person Does Not Exist",
        "description": "There's no escape, they swarm!",
        "base_url": "https://thispersondoesnotexist.com/",
        "image_url": "https://thispersondoesnotexist.com/",
        "license": "Unknown"
    },
    {
        "name": "🔄\u2003Lorem Picsum",
        "description": "Random photo from Picsum",
        "base_url": "https://picsum.photos/",
        "image_url": "https://picsum.photos/1024",
        "license": "Public domain (Picsum)"
    },
    {
        "name": "1️⃣\u2003Botanical Leaf Tapestry",
        "description": "seamless tapestry",
        "base_url": "https://stockcake.com/i/botanical-leaf-tapestry_2190014_1262920",
        "license": "Public domain (Stockcake)",
        "scraping": {
            "image_selector_regex": "<picture\\s+id=\"mainImageContainer\">.*?<img.*?src=\"([^\"]+)\".*?</picture>",
            "url_transform_regex": "_large(/[^/]+?stockcake\\.jpg)",
            "url_transform_replacement": "\\1"
        }
    },
    {
        "name": "1️⃣\u2003Checkerboard",
        "description": "playing with chunk sizes can create interesting patterns",
        "base_url": "https://dinopixel.com/checker-board-pixel-art-9080",
        "image_url": "https://dinopixel.com/preload/1221/checker-board.png",
        "license": "Unknown (DinoPixel)",
    },
    {
        "name": "1️⃣\u2003Vibrant Flower Collection",
        "description": "multiply blossom boxes",
        "base_url": "https://stockcake.com/i/vibrant-flower-collection_1061865_1157624",
        "license": "Public domain (Stockcake)",
        "scraping": {
            "image_selector_regex": "<picture\\s+id=\"mainImageContainer\">.*?<img.*?src=\"([^\"]+)\".*?</picture>",
            "url_transform_regex": "_large(/[^/]+?stockcake\\.jpg)",
            "url_transform_replacement": "\\1"
        }
    },
    {
        "name": "1️⃣\u2003Yellow Flower Matrix",
        "description": "great multiplication effect",
        "base_url": "https://commons.wikimedia.org/wiki/File:Yellow_flowers_a.jpg",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Yellow_flowers_a.jpg/960px-Yellow_flowers_a.jpg",
        "license": "CC BY-SA 3.0 (Wikimedia)"
    },
    {
        "name": "🔄\u2003Pepe Bigotes Random Image",
        "description": "random photos",
        "base_url": "https://random-image-pepebigotes.vercel.app/",
        "image_url": "https://random-image-pepebigotes.vercel.app/api/random-image",
        "license": "Public domain (Pepe Bigotes)"
    }
]
