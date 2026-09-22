#!/bin/bash
# Science
python mcq/scrapers/saruna_scraper.py 5d3d75e2-e1c2-457d-b763-1df2bcce37f6 --pages 0 --output mcq/data/saruna/Science
python mcq/scrapers/saruna_scraper.py 9231b768-4068-4a48-bc02-b271e15ce66b --pages 0 --output mcq/data/saruna/Science
python mcq/scrapers/saruna_scraper.py ee514b51-56a9-4194-a46e-d738472bbf3e --pages 0 --output mcq/data/saruna/Science

# Education
python mcq/scrapers/saruna_scraper.py 0ae0a86a-6742-4a60-9665-525bc9cc2316 --pages 0 --output mcq/data/saruna/Education
python mcq/scrapers/saruna_scraper.py 563fa052-a2eb-4372-88e7-f31d58fc289d --pages 0 --output mcq/data/saruna/Education
python mcq/scrapers/saruna_scraper.py 6e801e1c-9d09-480a-9219-7b3bb37a4ec6 --pages 0 --output mcq/data/saruna/Education

# Art and Culture
python mcq/scrapers/saruna_scraper.py b68c11ab-8ec6-4e74-b130-9ac682576d03 --pages 0 --output mcq/data/saruna/Maldivian_Art_Culture
python mcq/scrapers/saruna_scraper.py 4c294380-9d80-4f28-a7d6-8aacd4d7491d --pages 0 --output mcq/data/saruna/Maldivian_Art_Culture
python mcq/scrapers/saruna_scraper.py 3ce32e2f-5667-4f33-9527-81e7104be6a5 --pages 0 --output mcq/data/saruna/Maldivian_Art_Culture

echo "Download complete!"
