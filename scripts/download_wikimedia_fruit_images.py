from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import time
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


FRUIT_QUERIES: dict[str, str] = {
    "apple": "apple fruit",
    "orange": "orange fruit",
    "banana": "banana fruit",
    "pineapple": "pineapple fruit",
}
FRUIT_CATEGORIES: dict[str, str] = {
    "apple": "Category:Apples",
    "orange": "Category:Oranges (fruit)",
    "banana": "Category:Bananas",
    "pineapple": "Category:Pineapples",
}
FRUIT_TITLE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "apple": ("apple", "apples", "malus"),
    "orange": ("orange", "oranges", "citrus", "mandarin", "navel"),
    "banana": ("banana", "bananas", "cavendish", "musa"),
    "pineapple": ("pineapple", "ananas", "pina", "pinapple"),
}
COMMONS_API_URL = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = (
    "RobotObjectDetectorImageBot/1.0 "
    "(https://github.com/openai/codex; codex-noreply@openai.com) "
    "Python-urllib"
)
IMAGE_SUFFIX_BY_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
TITLE_BLACKLIST = (
    "logo",
    "icon",
    "diagram",
    "drawing",
    "map",
    "juice",
    "pie",
    "cake",
    "tree",
    "flower",
    "blossom",
    "leaf",
    "market",
    "3d",
    "a for",
    "apple ii",
    "apricot",
    "batido",
    "butterfly",
    "computer",
    "fertilization",
    "garden",
    "growing",
    "illustration",
    "mango",
    "museum",
    "orchard",
    "papaja",
    "parent plant",
    "peach",
    "plant",
    "pregnant",
    "refrigerator",
    "ribbon",
    "rotting",
    "sculpture",
    "smoothie",
    "spider",
    "wine",
)


def _safe_clear_output(output_root: Path) -> None:
    output_root = output_root.resolve()
    if output_root.anchor == str(output_root):
        raise ValueError(f"refusing to clear filesystem root: {output_root}")
    if output_root.exists():
        shutil.rmtree(output_root)


def _request_json(url: str, params: dict[str, object], timeout: float) -> dict[str, Any]:
    request_url = f"{url}?{urlencode(params)}"
    request = Request(
        request_url,
        headers={
            "User-Agent": USER_AGENT,
            "Api-User-Agent": USER_AGENT,
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _download_bytes(url: str, timeout: float) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Api-User-Agent": USER_AGENT,
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def _metadata_value(extmetadata: dict[str, Any], key: str) -> str:
    raw_value = extmetadata.get(key, {})
    if isinstance(raw_value, dict):
        value = raw_value.get("value", "")
    else:
        value = raw_value
    return re.sub(r"<[^>]+>", "", str(value)).strip()


def _safe_stem(value: str) -> str:
    stem = value.removeprefix("File:")
    stem = re.sub(r"\.[A-Za-z0-9]+$", "", stem)
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", stem).strip("_").lower()
    return stem[:80] or "image"


def _safe_console_text(value: str) -> str:
    return value.encode("ascii", errors="replace").decode("ascii")


def _is_candidate_title(class_name: str, title: str) -> bool:
    lowered = title.lower()
    if any(blocked in lowered for blocked in TITLE_BLACKLIST):
        return False
    return any(keyword in lowered for keyword in FRUIT_TITLE_KEYWORDS[class_name])


def list_commons_category_images(
    category: str,
    limit: int,
    thumb_width: int,
    timeout: float,
) -> list[dict[str, Any]]:
    payload = _request_json(
        COMMONS_API_URL,
        {
            "action": "query",
            "format": "json",
            "generator": "categorymembers",
            "gcmtitle": category,
            "gcmtype": "file",
            "gcmlimit": limit,
            "prop": "imageinfo",
            "iiprop": "url|mime|size|extmetadata",
            "iiurlwidth": thumb_width,
        },
        timeout=timeout,
    )
    pages = payload.get("query", {}).get("pages", {})
    if not isinstance(pages, dict):
        return []
    return sorted(
        (page for page in pages.values() if isinstance(page, dict)),
        key=lambda page: str(page.get("title", "")),
    )


def search_commons_images(
    query: str,
    limit: int,
    thumb_width: int,
    timeout: float,
) -> list[dict[str, Any]]:
    payload = _request_json(
        COMMONS_API_URL,
        {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6,
            "gsrlimit": limit,
            "prop": "imageinfo",
            "iiprop": "url|mime|size|extmetadata",
            "iiurlwidth": thumb_width,
        },
        timeout=timeout,
    )
    pages = payload.get("query", {}).get("pages", {})
    if not isinstance(pages, dict):
        return []
    return sorted(
        (page for page in pages.values() if isinstance(page, dict)),
        key=lambda page: int(page.get("index", 0)),
    )


def collect_candidate_pages(
    class_name: str,
    search_limit: int,
    thumb_width: int,
    timeout: float,
) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    for page in (
        *list_commons_category_images(
            category=FRUIT_CATEGORIES[class_name],
            limit=search_limit,
            thumb_width=thumb_width,
            timeout=timeout,
        ),
        *search_commons_images(
            query=FRUIT_QUERIES[class_name],
            limit=search_limit,
            thumb_width=thumb_width,
            timeout=timeout,
        ),
    ):
        title = str(page.get("title", ""))
        if title in seen_titles:
            continue
        seen_titles.add(title)
        pages.append(page)
    return pages


def download_fruit_images(
    output_root: Path,
    per_class: int,
    search_limit: int,
    thumb_width: int,
    timeout: float,
    pause_seconds: float,
) -> dict[str, int]:
    output_root.mkdir(parents=True, exist_ok=True)
    metadata_path = output_root / "metadata.csv"
    counts: dict[str, int] = {class_name: 0 for class_name in FRUIT_QUERIES}

    with metadata_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "class_name",
                "output_path",
                "commons_title",
                "commons_page_url",
                "image_url",
                "mime",
                "license_short_name",
                "license_url",
                "artist",
                "credit",
            ],
        )
        writer.writeheader()

        for class_name in FRUIT_QUERIES:
            class_dir = output_root / class_name
            class_dir.mkdir(parents=True, exist_ok=True)
            pages = collect_candidate_pages(
                class_name=class_name,
                search_limit=search_limit,
                thumb_width=thumb_width,
                timeout=timeout,
            )
            for page in pages:
                if counts[class_name] >= per_class:
                    break

                title = str(page.get("title", ""))
                if not _is_candidate_title(class_name, title):
                    continue

                imageinfo = page.get("imageinfo") or []
                if not imageinfo:
                    continue
                info = imageinfo[0]
                mime = str(info.get("mime", ""))
                suffix = IMAGE_SUFFIX_BY_MIME.get(mime)
                if suffix is None:
                    continue

                image_url = str(info.get("thumburl") or info.get("url") or "")
                if not image_url:
                    continue

                output_path = (
                    class_dir
                    / f"{counts[class_name]:03d}_{_safe_stem(title)}{suffix}"
                )
                try:
                    image_bytes = _download_bytes(image_url, timeout=timeout)
                except URLError as exc:
                    print(f"skip {_safe_console_text(title)}: {exc}")
                    continue
                if not image_bytes:
                    continue
                output_path.write_bytes(image_bytes)

                extmetadata = info.get("extmetadata") or {}
                page_url = str(
                    extmetadata.get("LicenseUrl", {}).get("source", "")
                    if isinstance(extmetadata.get("LicenseUrl"), dict)
                    else ""
                )
                writer.writerow(
                    {
                        "class_name": class_name,
                        "output_path": str(output_path),
                        "commons_title": title,
                        "commons_page_url": (
                            "https://commons.wikimedia.org/wiki/"
                            f"{title.replace(' ', '_')}"
                        ),
                        "image_url": image_url,
                        "mime": mime,
                        "license_short_name": _metadata_value(
                            extmetadata,
                            "LicenseShortName",
                        ),
                        "license_url": _metadata_value(extmetadata, "LicenseUrl")
                        or page_url,
                        "artist": _metadata_value(extmetadata, "Artist"),
                        "credit": _metadata_value(extmetadata, "Credit"),
                    }
                )
                counts[class_name] += 1
                time.sleep(pause_seconds)
    return counts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Download fruit images from Wikimedia Commons for cube-fruit "
            "classifier evaluation."
        ),
    )
    parser.add_argument("--output-root", type=Path, default=Path("outputs/web_fruit_images"))
    parser.add_argument("--per-class", type=int, default=8)
    parser.add_argument("--search-limit", type=int, default=80)
    parser.add_argument("--thumb-width", type=int, default=640)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--pause-seconds", type=float, default=0.1)
    parser.add_argument("--clear", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.per_class <= 0:
        raise ValueError("--per-class must be positive")
    if args.clear:
        _safe_clear_output(args.output_root)

    counts = download_fruit_images(
        output_root=args.output_root,
        per_class=args.per_class,
        search_limit=args.search_limit,
        thumb_width=args.thumb_width,
        timeout=args.timeout,
        pause_seconds=args.pause_seconds,
    )
    for class_name, count in counts.items():
        print(f"{class_name}: {count}")
    print(f"metadata={args.output_root / 'metadata.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
