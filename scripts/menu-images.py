#!/usr/bin/env python3
"""Download, apply, and verify the reviewed Lamiz menu image mappings."""

import argparse
import json
from pathlib import Path
import subprocess
from urllib.parse import quote, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "src/data/menu-image-sources.json"
MENU = ROOT / "src/data/menu.json"


def variant_path(local_path, size):
    path = Path(local_path)
    return str(path.with_name(f"{path.stem}-{size}.webp"))


def verify_webp(path):
    data = path.read_bytes()
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise ValueError(f"Not a WebP image: {path}")
    if int.from_bytes(data[4:8], "little") + 8 != len(data):
        raise ValueError(f"Incomplete WebP image: {path}")
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Download missing images using curl")
    parser.add_argument("--apply", action="store_true", help="Apply image paths to menu.json after checking files")
    parser.add_argument("--optimize", action="store_true", help="Generate 1x and 2x WebP variants; requires Pillow")
    parser.add_argument("--dist", action="store_true", help="Also check images and rendered markup in dist/")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    entries = manifest["items"]
    mappings = {entry["menu_title"]: entry for entry in entries}
    menu = json.loads(MENU.read_text())
    titles = [item["title_fa"] for category in menu for item in category["items"]]
    if len(mappings) != len(entries) or set(titles) != set(mappings):
        raise ValueError("Menu titles and image mappings differ; review the manifest first")

    assets = {}
    for entry in entries:
        if entry["local_path"]:
            previous = assets.setdefault(entry["local_path"], entry["source_url"])
            if previous != entry["source_url"]:
                raise ValueError("Conflicting source URLs for one local image")
    for local_path, source in assets.items():
        if not local_path.startswith("/images/menu/") or ".." in local_path:
            raise ValueError(f"Invalid asset path: {local_path}")
        target = ROOT / "public" / local_path.lstrip("/")
        if args.download and not target.exists():
            parts = urlsplit(source)
            if parts.scheme != "https" or parts.netloc != "lamizcoffee.com":
                raise ValueError(f"Unexpected source host: {source}")
            url = urlunsplit(parts._replace(path=quote(parts.path, safe="/%")))
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix(".webp.part")
            subprocess.run([
                "curl", "--fail", "--location", "--silent", "--show-error",
                "--retry", "2", "--max-time", "45", "--output", str(temporary), url,
            ], check=True)
            verify_webp(temporary)
            temporary.replace(target)
            print(f"Downloaded {local_path}")
        verify_webp(target)

    variants = {}
    for local_path in assets:
        for size in (96, 192):
            variants[variant_path(local_path, size)] = (local_path, size)
    for local_path in manifest["category_images"].values():
        for size in (64, 128):
            variants[variant_path(local_path, size)] = (local_path, size)

    if args.optimize:
        from PIL import Image

        for local_path, (original_path, size) in variants.items():
            target = ROOT / "public" / local_path.lstrip("/")
            with Image.open(ROOT / "public" / original_path.lstrip("/")) as original:
                # These menu photographs are square; preserve the full drink and its background.
                if original.width != original.height:
                    raise ValueError(f"Expected a square menu image: {original_path}")
                resized = original.resize((size, size), Image.Resampling.LANCZOS)
                resized.save(target, format="WEBP", quality=82, method=6)
        print(f"Generated {len(variants)} WebP variants")

    for local_path in variants:
        verify_webp(ROOT / "public" / local_path.lstrip("/"))

    if args.apply:
        for category in menu:
            category["image"] = manifest["category_images"][str(category["id"])]
            for item in category["items"]:
                item["image"] = mappings[item["title_fa"]]["local_path"] or ""
        MENU.write_text(json.dumps(menu, ensure_ascii=False, indent=2) + "\n")

    for category in menu:
        if category["image"] != manifest["category_images"][str(category["id"])]:
            raise ValueError(f"Category image not applied: {category['title']}")
        for item in category["items"]:
            expected = mappings[item["title_fa"]]["local_path"] or ""
            if item["image"] != expected:
                raise ValueError(f"Item image not applied: {item['title_fa']}")

    if args.dist:
        from html.parser import HTMLParser
        from collections import Counter

        class Images(HTMLParser):
            def __init__(self):
                super().__init__()
                self.images = []

            def handle_starttag(self, tag, attrs):
                if tag == "img":
                    attrs = dict(attrs)
                    if not attrs.get("src") or "alt" not in attrs:
                        raise ValueError("Rendered image is missing src or alt")
                    self.images.append((
                        attrs["src"], attrs.get("srcset"), attrs.get("width"),
                        attrs.get("height"), attrs.get("loading", "eager"),
                    ))

        images = Images()
        images.feed((ROOT / "dist/index.html").read_text())
        expected = [(c["image"], 64, "eager") for c in menu] + [
            (i["image"], 96, "lazy") for c in menu for i in c["items"] if i["image"]
        ]
        expected_images = [(
            variant_path(path, size),
            f"{variant_path(path, size)} 1x, {variant_path(path, size * 2)} 2x",
            str(size), str(size), loading,
        ) for path, size, loading in expected]
        if Counter(images.images) != Counter(expected_images):
            raise ValueError("Rendered responsive images do not match the menu")
        from PIL import Image

        for local_path in [*assets, *variants]:
            original = verify_webp(ROOT / "public" / local_path.lstrip("/"))
            built = verify_webp(ROOT / "dist" / local_path.lstrip("/"))
            if original != built:
                raise ValueError(f"Built image differs from downloaded asset: {local_path}")
            with Image.open(ROOT / "dist" / local_path.lstrip("/")) as image:
                image.load()
                if local_path in variants:
                    size = variants[local_path][1]
                    if image.size != (size, size):
                        raise ValueError(f"Wrong image dimensions: {local_path}")
        original_bytes = sum((ROOT / "public" / path.lstrip("/")).stat().st_size for path in assets)
        print(f"Verified {len(expected)} responsive images and {len(variants)} deployed variants")
        for density in (1, 2):
            selected_paths = {variant_path(path, size * density) for path, size, _ in expected}
            total_bytes = sum((ROOT / "dist" / path.lstrip("/")).stat().st_size for path in selected_paths)
            print(f"All menu images at {density}x: {total_bytes:,} bytes; {100 * (1 - total_bytes / original_bytes):.1f}% smaller than originals")

    unmatched = [e["menu_title"] for e in entries if e["match"] == "unmatched"]
    print(f"Verified {len(entries)} menu mappings and {len(assets)} local WebP files")
    print("Unmatched: " + ", ".join(unmatched))


if __name__ == "__main__":
    main()
