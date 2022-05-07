from fastapi.middleware.cors import CORSMiddleware
from matplotlib import pyplot as plt
from sklearn.cluster import KMeans
from fastapi import FastAPI
from typing import List
from io import BytesIO
from skimage import io
import seaborn as sns
import numpy as np
import requests
import colorsys
import sys


def clustering(colour_list, colours):
    cluster = KMeans(n_clusters=colours, n_init=3, max_iter=20, tol=0.001)
    try:
        cluster.fit(colour_list)
    except ValueError:
        print("Error: Not sufficient images to cluster. Exiting...")
        sys.exit()
    labels = cluster.labels_
    return cluster.cluster_centers_, labels


def fast_dominant_colour(image, colours=10):
    '''
    Faster method for web use that speeds up the sklearn variant.
    '''
    image = image.reshape((-1, 3))
    colors, _ = clustering(image, colours)
    return colors


def clamp(x):
    '''
    Utility function to return ints from 0-255
    '''
    return int(max(0, min(x, 255)))


def rgb_to_hex(r, g, b):
    return "#{0:02x}{1:02x}{2:02x}".format(r, g, b)


def get_rgb_hex(image):
    '''
    Method to print hex sting and return an rgb tuple of the
    dominant colour in an image
    '''
    dominant_colours = fast_dominant_colour(image)
    rgb_colours = []
    hex_colours = []
    for c in dominant_colours:
        r = clamp(c[0])
        g = clamp(c[1])
        b = clamp(c[2])
        hex_str = rgb_to_hex(r, g, b)
        hex_colours.append(hex_str)
        rgb_colour = [r, g, b]
        rgb_colours.append(rgb_colour)
    return rgb_colours, hex_colours


def get_links(url, params=None):
    url_links = []
    req = requests.get(url=url, params=params)
    print(req.url)
    data = req.json()
    for image in data["hits"]:
        # url_links.append(image["webformatURL"])
        url_links.append(image["previewURL"])
    print(f"Found {len(url_links)} images")
    return url_links


def process_images(url_links):
    rgb_list = []
    hex_list = []
    for i, url in enumerate(url_links):
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            image = io.imread(BytesIO(r.content))
            rgb_palette, hex_palette = get_rgb_hex(image)
            rgb_list.append(rgb_palette)
            hex_list.append(hex_palette)
            # if not os.path.exists(f"images\\{query}"):
            #     os.makedirs(f"images\\{query}")
            # image = image.save(f"images\\{query}\\{str(i)}.jpg", "JPEG")
        else:
            print("Download error: " + str(r.status_code))
    return rgb_list, hex_list


app = FastAPI()
# uvicorn main:app  --reload --host 0.0.0.0 --port 8000


origins = [
    "https://localhost",
    "http://localhost",
    "http://localhost:8000",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/getpalette/{q}")
def read_item(q: str, numColors: int, numImages: int, page: int = 1, image_type: str = "photo", colorList = None):

    query = '+'.join(q.split(' '))
    n_colors = numColors

    API_KEY = "16613842-8af8174d8d15db485862bd8f0"
    URL_ENDPOINT = "https://pixabay.com/api/"
    ENDPOINT = URL_ENDPOINT + "?key=" + API_KEY
    COLORS = colorList.split(',')
    COLORS.append('transparent')
    PARAMS = {'q': query, 'per_page': numImages,
              'page': 1, 'image_type': 'photo', 'color': COLORS}       

    url_links = get_links(ENDPOINT, PARAMS)
    rgb_list, hex_list = process_images(url_links)
    rgb_list = np.asarray(rgb_list)

    colors, labels = clustering(rgb_list.reshape((-1, 3)), n_colors)

    palette = []

    for i, c in enumerate(colors):
        r = clamp(c[0])
        g = clamp(c[1])
        b = clamp(c[2])
        hex_str = rgb_to_hex(r, g, b)
        palette.append(hex_str)

    return {q: palette}
