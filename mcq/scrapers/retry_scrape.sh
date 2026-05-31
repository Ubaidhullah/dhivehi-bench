#!/bin/bash
# Retry and Expansion scrape script for Saruna collections

OUTPUT_DIR="mcq/data/saruna"
mkdir -p "$OUTPUT_DIR"

# Collection List: [Name] [UUID]
COLLECTIONS=(
    "Maldivian_Art_Culture|b68c11ab-8ec6-4e74-b130-9ac682576d03"
    "Science|ee514b51-56a9-4194-a46e-d738472bbf3e"
    "Shariah_Law|ec4a0da3-58ba-4786-9118-f17a8dfa3059"
    "Political_Science|5dadad10-8281-44de-90db-b8c37907ffd8"
    "Education|563fa052-a2eb-4372-88e7-f31d58fc289d"
    "Customs_Traditions|9fa2ce3a-3cc4-4b48-a9e0-c8de07501be7"
)

for entry in "${COLLECTIONS[@]}"; do
    NAME="${entry%%|*}"
    UUID="${entry#*|}"
    echo "Starting/Resuming scrape for $NAME ($UUID)..."
    # Note: saruna_scraper.py will skip existing files
    python mcq/scrapers/saruna_scraper.py "$UUID" --pages 0 --output "$OUTPUT_DIR" --collection-name "$NAME"
    echo "Finished $NAME."
    sleep 10 # Increased sleep to be gentler on the API
done

echo "Retry and Expansion scrape complete."
