#!/usr/bin/env python3

# Copyright (c) 2020 Daniel Jakots
#
# Licensed under the MIT license. See the LICENSE file.

import glob
import os

import PIL
import PIL.Image
import PIL.ExifTags

import jinja2

SMALL_IMAGE_WORD = "small"
MAX_HORIZONTAL_SIZE = 800
PAGINATION = 6
OUTPUT_DIR = "output"
PICTURES_PATH = f"{OUTPUT_DIR}/pictures/*"


def get_exif(picture_path):
    img = PIL.Image.open(picture_path)
    exif = {
        PIL.ExifTags.TAGS[k]: v
        for k, v in img._getexif().items()
        if k in PIL.ExifTags.TAGS
    }
    return {
        "Model": exif["Model"],
        "LensModel": exif["LensModel"],
        "DateTime": exif["DateTime"],
        "ExposureTime": exif["ExposureTime"],
        "FNumber": exif["FNumber"],
        "ISOSpeedRatings": exif["ISOSpeedRatings"],
        "FocalLength": exif["FocalLength"],
    }


def reduce_image(picture_path, new_picture_path):
    image = PIL.Image.open(picture_path)
    if image.size[0] < MAX_HORIZONTAL_SIZE:
        return
    new_size = calculate_reduced_size(image.size)
    image = image.resize(new_size, PIL.Image.ANTIALIAS)
    image.save(new_picture_path, optimize=True, quality=85)


def calculate_reduced_size(size):
    horizontal_ratio = size[0] / MAX_HORIZONTAL_SIZE
    new_size = (int(size[0] / horizontal_ratio), int(size[1] / horizontal_ratio))
    return new_size


def clean_exposure_time(ET):
    # (1, 1) -> 1s
    if ET[0] == 1 and ET[1] == 1:
        return "1s"
    # (1, 60) -> 1/60s
    elif ET[0] == 1 and ET[1] != 1:
        return f"{ET[0]}/{ET[1]}s"
    # (25, 10) -> 2.5s
    elif ET[0] != 1 and ET[1] != 1:
        return f"{float(ET[0] / ET[1])}s"
    # (8, 1) -> 8s
    elif ET[0] != 1 and ET[1] == 1:
        return f"{ET[0]}s"


def clean_aperture(FL):
    FL = FL[0] / FL[1]
    # strip .0 if needed
    FL = "{:g}".format(FL)
    return f"f/{FL}"


def analyze_pictures(pictures_path):
    pictures = []
    for picture_path in glob.glob(pictures_path):
        if SMALL_IMAGE_WORD in picture_path:
            continue
        ce = analyze_picture(picture_path)
        pictures.append(ce)

        if not os.path.isfile(small_picture_path(picture_path)):
            reduce_image(picture_path, small_picture_path(picture_path))
    return pictures


def analyze_picture(picture_path):
    exif = get_exif(picture_path)
    picture_path = picture_path[len(OUTPUT_DIR) + 1:]
    exposure_time = clean_exposure_time(exif["ExposureTime"])
    aperture = clean_aperture(exif["FNumber"])
    cleaned_exif = {}
    cleaned_exif["model"] = exif["Model"]
    cleaned_exif["lens_model"] = exif["LensModel"]
    cleaned_exif["date"] = exif["DateTime"]
    cleaned_exif["focal_length"] = f"{exif['FocalLength'][0]}mm"
    cleaned_exif["aperture"] = aperture
    cleaned_exif["exposure_time"] = exposure_time
    cleaned_exif["iso"] = f"ISO {exif['ISOSpeedRatings']}"
    cleaned_exif["title"] = picture_path.rpartition("/")[2][11:].partition(".")[0]
    cleaned_exif["path"] = picture_path
    cleaned_exif["small_path"] = small_picture_path(picture_path)
    return cleaned_exif


def small_picture_path(picture_path):
    return f"{picture_path.rpartition('.')[0]}-{SMALL_IMAGE_WORD}.{picture_path.rpartition('.')[2]}"


def create_html_indexes(pictures_per_page):
    for rank, page in enumerate(pictures_per_page):
        with open("index.html.j2", "r") as f:
            template = f.read()
        jinja2_template = jinja2.Template(template, trim_blocks=True)
        pagination = {}
        pagination["current"] = rank + 1
        pagination["total"] = len(pictures_per_page)
        if rank > 0:
            pagination["previous"] = rank - 1
        # check if we're on the last page (i.e. last loop)
        if rank != len(pictures_per_page) - 1:
            pagination["next"] = rank + 1

        result = jinja2_template.render(pagination=pagination, pictures=page)
        if rank == 0:
            rank = ""
        else:
            rank = str(rank)
        with open(f"{OUTPUT_DIR}/index{rank}.html", "w") as f:
            f.write(result)


def create_pagination(pictures):
    pictures_per_page = []
    offset = 0
    for _ in range((len(pictures) // PAGINATION) + 1):
        pictures_per_page.append(pictures[offset : offset + PAGINATION])
        offset = offset + PAGINATION
    return pictures_per_page


def main():
    pictures = analyze_pictures(PICTURES_PATH)
    pictures.sort(
        reverse=True, key=lambda i: i["date"].replace(":", "").replace(" ", "")
    )
    create_html_indexes(create_pagination(pictures))


if __name__ == "__main__":
    main()
