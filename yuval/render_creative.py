#!/usr/bin/env python3
"""יובל — רינדור הקריאייטיב לגדלים שונים.

בונה את הקריאייטיב מחדש ב-HTML (טקסט חי, לא צרוב) ומרנדר אותו
ב-Chromium ברזולוציה מדויקת. מייצר PNG + קובץ .txt נלווה עם מפרט הבנייה.

    python3 yuval/render_creative.py --photo yuval/assets/photo.jpg
"""
import argparse, datetime, json, pathlib, shutil, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent
TPL, FONTS, OUT = ROOT / "templates", ROOT / "assets" / "fonts", ROOT / "outputs"

FORMATS = {
    "1080x1350": ("layout_45.html", 1080, 1350, "feed"),
    "1080x1920": ("layout_916.html", 1080, 1920, "story"),
}
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"


def build_html(layout: str, photo_uri: str, copy: dict) -> str:
    shell = (TPL / "creative.html").read_text(encoding="utf-8")
    body = (TPL / layout).read_text(encoding="utf-8")
    for token, value in {
        "__PHOTO__": photo_uri,
        "__H1__": copy["headline_1"],
        "__H2__": copy["headline_2"],
        "__H3__": copy["headline_3"],
        "__SUB__": copy["sub"],
        "__STICKY__": copy["sticky"],
        "__BODY__": copy["body"],
        "__CTA__": copy["cta"],
    }.items():
        body = body.replace(token, value)
    return shell.replace("__FONTS__", FONTS.as_uri()).replace("__BODY__", body)


def resolve_photo(src: str) -> pathlib.Path:
    if src.startswith(("http://", "https://")):
        dest = ROOT / "assets" / ("photo" + pathlib.Path(src.split("?")[0]).suffix or ".jpg")
        dest.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
            shutil.copyfileobj(r, f)
        print(f"downloaded photo -> {dest} ({dest.stat().st_size} bytes)")
        return dest
    p = pathlib.Path(src)
    if not p.is_absolute():
        p = REPO / p
    if not p.is_file():
        sys.exit(f"photo not found: {p}")
    return p


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo", required=True, help="path or URL to the clean photo")
    ap.add_argument("--slug", default="hachlatot-mehabeten")
    ap.add_argument("--only", choices=sorted(FORMATS), help="render a single format")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    photo = resolve_photo(args.photo)
    copy = json.loads((ROOT / "copy.json").read_text(encoding="utf-8"))
    date = datetime.date.today().isoformat()
    OUT.mkdir(parents=True, exist_ok=True)
    targets = {args.only: FORMATS[args.only]} if args.only else FORMATS

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME)
        for name, (layout, w, h, label) in targets.items():
            html = build_html(layout, photo.as_uri(), copy)
            debug = OUT / f"{date}-{args.slug}-{name}.html"
            debug.write_text(html, encoding="utf-8")

            page = browser.new_page(viewport={"width": w, "height": h},
                                    device_scale_factor=1)
            page.goto(debug.as_uri(), wait_until="load")
            page.wait_for_timeout(400)
            png = OUT / f"{date}-{args.slug}-{name}.png"
            page.screenshot(path=str(png), clip={"x": 0, "y": 0, "width": w, "height": h})
            page.close()

            (png.with_suffix(".txt")).write_text(
                f"creative : {args.slug}\nformat   : {name} ({label})\n"
                f"built    : HTML + Chromium render (live text, not baked)\n"
                f"photo    : {photo.name}\nlayout   : {layout}\ncopy     : yuval/copy.json\n"
                f"date     : {date}\n", encoding="utf-8")
            print(f"OK {png.name}  {png.stat().st_size} bytes")
        browser.close()


if __name__ == "__main__":
    main()
