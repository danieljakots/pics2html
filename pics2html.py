#!/usr/bin/env python3

import glob

import PIL.Image
import PIL.ExifTags

import jinja2


def get_exif(picture):
    img = PIL.Image.open(picture)
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


def analyze_picture(picture):
    exif = get_exif(picture)
    exposure_time = clean_exposure_time(exif["ExposureTime"])
    aperture = clean_aperture(exif['FNumber'])
    cleaned_exif = {}
    cleaned_exif["model"] = exif['Model']
    cleaned_exif["lens_model"] = exif['LensModel']
    cleaned_exif["date"] = exif['DateTime']
    cleaned_exif["focal_length"] = f"{exif['FocalLength'][0]}mm"
    cleaned_exif["aperture"] = aperture
    cleaned_exif["exposure_time"] = exposure_time
    cleaned_exif["iso"] = f"ISO {exif['ISOSpeedRatings']}"
    cleaned_exif["title"] = picture.rpartition("/")[2][11:].partition(".")[0]
    return cleaned_exif


def main():
    pictures = []
    for picture in glob.glob("pictures/*"):
        ce = analyze_picture(picture)
        picture_dict = {}
        picture_dict[picture.rpartition("/")[2]] = ce
        pictures.append(picture_dict)

    with open("index.html.j2", "r") as f:
        template = f.read()
    jinja2_template = jinja2.Template(template, trim_blocks=True)
    result = jinja2_template.render(pictures=pictures)
    with open("index.html", "w") as f:
        f.write(result)


if __name__ == "__main__":
    main()
