# pics2html

The static site generator for pictures I wish I didn't have to write. If you
don't care about exif, this most certainly pointless for you.

## Why this?

I need to write a blog post to explain it and then I'll link it here

## Usage

Install dependencies: Pillow jinja2 rfeed.
Put all pictures in output/pictures/.
Edit global var at the top of pics2html.py.
Run `python3 pics2tohtml.py` and let the magic happen.
It will create smaller pictures if they're bigger than the threshold, so it may
take some time the first time.
It will output all the html files so you just have to ship the whole dir.
