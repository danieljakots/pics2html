# pics2html

The static site generator for pictures I wish I didn't have to write. If you
don't care about exif, this most certainly pointless for you.

## Why this?

I need to write a blog post to explain it and then I'll link it here

## Usage

0. Install dependencies: Pillow jinja2 rfeed.
1. Put all pictures in output/pictures/.
2. Edit global var at the top of pics2html.py.
3. Run `python3 pics2tohtml.py` and let the magic happen.
4. It will create smaller pictures if they're bigger than the threshold, so it may
take some time the first time.
5. It will output all the html files so you just have to ship the whole dir.
