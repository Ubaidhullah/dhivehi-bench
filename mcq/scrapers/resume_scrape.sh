#!/bin/bash
OUTPUT_DIR="mcq/data/saruna"
COLLECTIONS=(
    "Maldivian_History|d9d2049d-1a55-4f93-b99d-51739fd47437"
    "Maldivian_Art_Culture|b68c11ab-8ec6-4e74-b130-9ac682576d03"
    "Religion|148cbb2b-4b67-41f0-b261-5a1f1be2205a"
    "Poetry|ea71c0c8-2339-490e-8dbb-b92bd19d10d1"
    "Essays|2814eaf3-477c-41b0-9df9-08831845600e"
)
for entry in "${COLLECTIONS[@]}"; do
    NAME="${entry%%|*}"
    UUID="${entry#*|}"
    echo "Resuming scrape for $NAME ($UUID)..."
    python mcq/scrapers/saruna_scraper.py "$UUID" --pages 0 --output "$OUTPUT_DIR"
    sleep 2
done
