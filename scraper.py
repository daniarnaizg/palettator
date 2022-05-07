from matplotlib import pyplot as plt
from PIL import Image
from io import BytesIO
import seaborn as sns
import requests
import os

import numpy as np
from sklearn.cluster import KMeans
from skimage import io


def rgb2hex(r, g, b):
    # return "#{:02x}{:02x}{:02x}".format(r, g, b)
    return "#{:02x}{:02x}{:02x}".format(round(r), round(g), round(b))


def get_dominant_color_sklearn(image, colours=10):
    img = image.reshape((-1, 3))

    cluster = KMeans(n_clusters=colours, n_init=3, max_iter=20, tol=0.001)
    cluster.fit(img)
    labels = cluster.labels_
    centroid = cluster.cluster_centers_

    percent = []
    _, counts = np.unique(labels, return_counts=True)
    for i in range(len(centroid)):
        j = counts[i]
        j = j/(len(labels))
        percent.append(j)

    indices = np.argsort(percent)[::-1]
    dominant = centroid[indices[0]]

    return dominant, labels, centroid


def get_dominant_color(pil_img, palette_size=16):
    img = pil_img.copy()

    # Reduce colors (uses k-means internally)
    paletted = img.convert('P', palette=Image.ADAPTIVE, colors=palette_size)

    # Find the color that occurs most often
    palette = paletted.getpalette()
    color_counts = sorted(paletted.getcolors(), reverse=True)
    palette_index = color_counts[0][1]
    dominant_color = palette[palette_index*3:palette_index*3+3]

    return dominant_color


def process_images(url_links):
    palettes = []
    for i, url in enumerate(url_links):
        r = requests.get(url, stream=True)

        if r.status_code == 200:
            # image = Image.open(BytesIO(r.content))
            # # image.thumbnail((100, 100))
            # palettes.append(get_dominant_color(image))

            image = io.imread(BytesIO(r.content))
            palettes.append(get_dominant_color_sklearn(image)[0])

            # if not os.path.exists(f"images\\{query}"):
            #     os.makedirs(f"images\\{query}")
            # image = image.save(f"images\\{query}\\{str(i)}.jpg", "JPEG")
        else:
            print("Download error: " + str(r.status_code))
    return palettes


if __name__ == "__main__":

    query = '+'.join(input("Enter the query: ").split(' '))
    n_colors = int(input("Enter the number of colors: "))

    API_KEY = "XXX"
    URL_ENDPOINT = "https://pixabay.com/api/"
    PER_PAGE = 25
    N_IMAGES = 25

    PARAMS = {'q': query, 'per_page': PER_PAGE,
              'page': 1, 'image_type': 'photo'}
    ENDPOINT = URL_ENDPOINT + "?key=" + API_KEY

    url_links = []

    req = requests.get(url=ENDPOINT, params=PARAMS)
    # print(req.url)
    data = req.json()

    num_pages = (data["totalHits"] // PER_PAGE) + 1

    for image in data["hits"]:
        url_links.append(image["previewURL"])
        # url_links.append(image["webformatURL"])

    # for page in range(2, num_pages + 1):
    #     if len(url_links) >= N_IMAGES:
    #         break
    #     time.sleep(1)
    #     PARAMS['page'] = page
    #     req = requests.get(url=ENDPOINT, params=PARAMS)
    #     data = req.json()
    #     for image in data["hits"]:
    #         url_links.append(image["webformatURL"])

    # Download images
    palettes = process_images(url_links)

    # Convert to hex
    hex_palette = []
    for palette in palettes:
        hex = rgb2hex(palette[0], palette[1], palette[2])
        hex_palette.append(hex)
    print(list(set(hex_palette))[:n_colors])

    # Plot colors with seaborn
    sns.set(style="whitegrid")
    sns.palplot(sns.color_palette(list(set(hex_palette))[:n_colors]))
    plt.show()
