#!/usr/bin/env python3
# tools/make_brand_icons.py
# Erzeugt aus EINEM Quellbild die Home-Assistant-Brand-Dateien für MedienStop:
#   icon.png (256x256), icon@2x.png (512x512), logo.png (256), logo@2x.png (512)
# Optional mit kreisrundem Zuschnitt (transparente Ecken).
#
#   python3 make_brand_icons.py /pfad/zum/baer.png --out ../brand --circle
#
# Voraussetzung: pip install pillow

import argparse, os
from PIL import Image, ImageDraw


def circular(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    w, h = im.size
    s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, s, s), fill=255)
    out = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    return out


def square(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    w, h = im.size
    s = min(w, h)
    return im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--out", default="brand")
    ap.add_argument("--circle", action="store_true", help="runde Ecken transparent")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    im = Image.open(args.src)
    base = circular(im) if args.circle else square(im)
    for name, size in [("icon.png", 256), ("icon@2x.png", 512),
                       ("logo.png", 256), ("logo@2x.png", 512)]:
        base.resize((size, size), Image.LANCZOS).save(os.path.join(args.out, name))
        print("geschrieben:", os.path.join(args.out, name))


if __name__ == "__main__":
    main()
