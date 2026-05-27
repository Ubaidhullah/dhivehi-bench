#!/bin/bash
# Bulk scrape script for Saruna collections

OUTPUT_DIR="mcq/data/saruna"
mkdir -p "$OUTPUT_DIR"

# Collection List: [Name] [UUID]
COLLECTIONS=(
    "Dhivehi_Language_Studies|ffb9e093-5a2b-42fa-a584-2aa19d7d5e7d"
    "Maldivian_History|d9d2049d-1a55-4f93-b99d-51739fd47437"
    "Maldivian_Art_Culture|b68c11ab-8ec6-4e74-b130-9ac682576d03"
    "Religion|148cbb2b-4b67-41f0-b261-5a1f1be2205a"
    "Poetry|ea71c0c8-2339-490e-8dbb-b92bd19d10d1"
    "Essays|2814eaf3-477c-41b0-9df9-08831845600e"
    "Science|ee514b51-56a9-4194-a46e-d738472bbf3e"
)

for entry in "${COLLECTIONS[@]}"; do
    NAME="${entry%%|*}"
    UUID="${entry#*|}"
    echo "Starting scrape for $NAME ($UUID)..."
    # Note: saruna_scraper.py will skip existing files, effectively "resuming"
    python mcq/scrapers/saruna_scraper.py "$UUID" --pages 0 --output "$OUTPUT_DIR" --collection-name "$NAME"
    echo "Finished $NAME."
    sleep 5
done

echo "Bulk scrape complete."
