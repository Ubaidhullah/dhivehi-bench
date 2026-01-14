"""
Saruna Collection Scraper - Downloads PDFs from saruna.mnu.edu.mv collections.

Usage:
    python saruna_scraper.py <collection_id> --pages N [--output DIR]
"""

import argparse
import csv
import os
import time
import requests
from tqdm import tqdm

API = "https://saruna.mnu.edu.mv/server/api"
PAGE_SIZE = 20
DELAY = 0.3


def fetch(endpoint, params=None):
    r = requests.get(f"{API}{endpoint}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def download(url, path):
    if os.path.exists(path):
        return True
    r = requests.get(url, stream=True, timeout=120)
    r.raise_for_status()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
    return True


def sanitize(text):
    """Remove invalid filename characters."""
    result = ""
    for c in text:
        if c.isalnum() or c in "._- ":
            result += c
    return result.strip()


def find_bundle(bundles, name):
    """Find a bundle by name."""
    for bundle in bundles:
        if bundle["name"] == name:
            return bundle
    return None


def find_pdf(bitstreams):
    """Find the first PDF bitstream."""
    for bitstream in bitstreams:
        if bitstream["name"].lower().endswith(".pdf"):
            return bitstream
    return None


def get_title(obj):
    """Extract title from item metadata."""
    titles = obj["metadata"].get("dc.title", [])
    if titles:
        return titles[0].get("value", "Unknown")
    return "Unknown"


def main():
    parser = argparse.ArgumentParser(description="Download PDFs from a Saruna collection")
    parser.add_argument("collection_id", help="Collection UUID")
    parser.add_argument("--pages", type=int, required=True, help="Pages to download (0=all)")
    parser.add_argument("--output", default="./raw_data", help="Output directory")
    args = parser.parse_args()

    # Get collection info
    info = fetch(f"/core/collections/{args.collection_id}")
    name = info.get("name", args.collection_id)
    print(f"Collection: {name}")

    # Get total pages
    data = fetch("/discover/search/objects", {"scope": args.collection_id, "size": PAGE_SIZE, "page": 0})
    page_info = data["_embedded"]["searchResult"]["page"]
    total_pages = page_info["totalPages"]

    if args.pages == 0:
        max_pages = total_pages
    else:
        max_pages = min(args.pages, total_pages)

    print(f"Items: {page_info['totalElements']} | Pages: {max_pages}/{total_pages}\n")

    # Setup output
    safe_name = sanitize(name)[:50]
    out_dir = os.path.join(args.output, safe_name)
    os.makedirs(out_dir, exist_ok=True)

    downloaded = []
    skipped = []

    for page in tqdm(range(max_pages), desc="Pages"):
        if page > 0:
            data = fetch("/discover/search/objects", {"scope": args.collection_id, "size": PAGE_SIZE, "page": page})
            time.sleep(DELAY)

        items = data["_embedded"]["searchResult"]["_embedded"]["objects"]

        for item in items:
            obj = item["_embedded"]["indexableObject"]
            uuid = obj["uuid"]
            title = get_title(obj)

            try:
                # Get ORIGINAL bundle
                bundles_data = fetch(f"/core/items/{uuid}/bundles")
                bundles = bundles_data["_embedded"]["bundles"]
                time.sleep(DELAY)

                original = find_bundle(bundles, "ORIGINAL")
                if not original:
                    skipped.append((title, "No ORIGINAL bundle"))
                    continue

                # Get PDF bitstream
                bitstreams_data = fetch(f"/core/bundles/{original['uuid']}/bitstreams")
                bitstreams = bitstreams_data["_embedded"]["bitstreams"]
                time.sleep(DELAY)

                pdf = find_pdf(bitstreams)
                if not pdf:
                    skipped.append((title, "No PDF"))
                    continue

                # Download
                filename = sanitize(pdf["name"])
                path = os.path.join(out_dir, f"{uuid}_{filename}")
                download(f"{API}/core/bitstreams/{pdf['uuid']}/content", path)
                downloaded.append((title, filename, pdf.get("sizeBytes", 0)))
                time.sleep(DELAY)

            except Exception as e:
                skipped.append((title, str(e)))

    # Write log
    log_path = os.path.join(args.output, f"{safe_name}_downloads.csv")
    with open(log_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["title", "filename", "size_kb", "status"])
        for title, filename, size in downloaded:
            writer.writerow([title, filename, size // 1024, "downloaded"])
        for title, reason in skipped:
            writer.writerow([title, "", 0, f"skipped:{reason}"])

    print(f"\nDone: {len(downloaded)} downloaded, {len(skipped)} skipped")
    print(f"Output: {out_dir}")
    print(f"Log: {log_path}")


if __name__ == "__main__":
    main()

# python scrapers/saruna_scraper.py ffb9e093-5a2b-42fa-a584-2aa19d7d5e7d --pages 10