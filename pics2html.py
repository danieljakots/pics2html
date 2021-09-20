#!/usr/bin/env python3

# Copyright (c) 2020 Daniel Jakots
#
# Licensed under the MIT license. See the LICENSE file.

import datetime
import glob
import os

import PIL
import PIL.Image
import PIL.ExifTags

import feedgenerator
import jinja2

SMALL_IMAGE_WORD = "small"
MAX_HORIZONTAL_SIZE = 800
PAGINATION = 10
OUTPUT_DIR = "output"
PICTURES_PATH = f"{OUTPUT_DIR}/pictures/*"
SITE = {}
SITE["url"] = "https://px.chown.me"
SITE["author"] = "Daniel Jakots"
SITE["name"] = f"{SITE['author']}' photography"


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
    if ET >= 0.3:
        if str(ET)[-2:] == ".0":
            ET = int(ET)
        return f"{ET}s"
    ET = f"1/{1 / ET}s"
    return ET


def clean_aperture(FN):
    if str(FN)[-2:] == ".0":
        FN = int(FN)
    return f"f/{FN}"


def clean_focal_length(FL):
    if str(FL)[-2:] == ".0":
        FL = int(FL)
    # FL = "{:g}".format((FL))
    return f"{FL}mm"


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
    picture_path = picture_path[len(OUTPUT_DIR) + 1 :]
    exposure_time = clean_exposure_time(exif["ExposureTime"])
    aperture = clean_aperture(exif["FNumber"])
    focal_length = clean_focal_length(exif['FocalLength'])
    cleaned_exif = {}
    cleaned_exif["model"] = exif["Model"]
    cleaned_exif["lens_model"] = exif["LensModel"]
    cleaned_exif["date"] = f"{exif['DateTime']} (UTC)"
    cleaned_exif["focal_length"] = focal_length
    cleaned_exif["aperture"] = aperture
    cleaned_exif["exposure_time"] = exposure_time
    cleaned_exif["iso"] = f"ISO {exif['ISOSpeedRatings']}"
    cleaned_exif["title"] = picture_path.rpartition("/")[2][11:].partition(".")[0]
    cleaned_exif["path"] = picture_path
    cleaned_exif["small_path"] = small_picture_path(picture_path)
    cleaned_exif["html_path"] = picture_path.rpartition("/")[2]
    return cleaned_exif


def small_picture_path(picture_path):
    return f"{picture_path.rpartition('.')[0]}-{SMALL_IMAGE_WORD}.{picture_path.rpartition('.')[2]}"


def create_html_indexes(pictures):
    jinja2_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader("templates"), trim_blocks=True
    )
    for rank, pictures_in_page in enumerate(pictures):
        jinja2_template = jinja2_env.get_template("index.html.j2")
        pagination = {}
        pagination["current"] = rank + 1
        pagination["total"] = len(pictures)
        if rank > 0:
            pagination["previous"] = rank - 1
        # check if we're on the last page (i.e. last loop)
        if rank != len(pictures) - 1:
            pagination["next"] = rank + 1

        result = jinja2_template.render(
            pagination=pagination, pictures=pictures_in_page, site=SITE
        )
        if rank == 0:
            rank = ""
        else:
            rank = str(rank)
        with open(f"{OUTPUT_DIR}/index{rank}.html", "w") as f:
            f.write(result)


def create_html_picture(picture):
    jinja2_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader("templates"), trim_blocks=True
    )
    jinja2_template = jinja2_env.get_template("picture.html.j2")

    result = jinja2_template.render(picture=picture, site=SITE)
    with open(f"{OUTPUT_DIR}/{picture['html_path']}.html", "w") as f:
        f.write(result)


def create_html_all(pictures):
    jinja2_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader("templates"), trim_blocks=True
    )
    jinja2_template = jinja2_env.get_template("all.html.j2")
    result = jinja2_template.render(pictures=pictures, site=SITE)
    with open(f"{OUTPUT_DIR}/all.html", "w") as f:
        f.write(result)


def create_pagination(pictures):
    """Split the list of pictures into a list of lists of PAGINATION pictures."""
    pictures_for_page = []
    offset = 0
    for _ in range((len(pictures) // PAGINATION) + 1):
        pictures_for_page.append(pictures[offset : offset + PAGINATION])
        offset = offset + PAGINATION
    return pictures_for_page


def create_feed():
    return feedgenerator.Atom1Feed(
        title=SITE["name"],
        link=f'{SITE["url"]}/',
        feed_url=f'{SITE["url"]}/feed.xml',
        description=f"Feed for {SITE['url']}",
    )


def main():
    pictures = analyze_pictures(PICTURES_PATH)
    pictures.sort(
        reverse=True, key=lambda i: i["date"].replace(":", "").replace(" ", "")
    )
    create_html_indexes(create_pagination(pictures))
    create_html_all(pictures)
    feed = create_feed()
    for picture in pictures:
        create_html_picture(picture)
        # 2014:12:27 15:43:55 -> ('2014', '12', '27', '15', '43', '55')
        date = [int(i) for i in picture["date"][:-6].replace(" ", ":").split(":")]
        date = datetime.datetime(*date)
        feed.add_item(
            title=picture["title"],
            link=f"{SITE['url']}/{picture['html_path']}.html",
            author_name=SITE["author"],
            pubdate=date,
            description=picture["title"],
        )
    with open(f"{OUTPUT_DIR}/feed.xml", "w") as f:
        feed.write(f, "utf-8")


if __name__ == "__main__":
    main()
