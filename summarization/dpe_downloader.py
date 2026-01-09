import os
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

HTML_FILE = 'dpe.html'
DEST_ROOT = './papers'
MISSING_MS_ROOT = './papers_missing_ms'
BASE_URL = 'https://dpe.edu.mv/'

def sanitize(s):
    return re.sub(r'[\\/:"*?<>|]+', '', s).strip()

def get_header_year(header_text):
    # Extract Year from header only (e.g. "2019", "1999")
    year_match = re.search(r'(19|20)\d{2}', header_text)
    return year_match.group(0) if year_match else ''

def get_paper_details(paper_name):
    # Month
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month = ''
    for m in months:
        if m.lower() in paper_name.lower():
            month_match = re.search(r'\b' + m + r'[a-z]*', paper_name, re.IGNORECASE)
            if month_match:
                candidate = month_match.group(0).title()
                if 'Marking' in candidate:
                    continue
                month = candidate
            break
            
    # Specimen
    specimen = 'Specimen' if 'specimen' in paper_name.lower() else ''
    
    return month, specimen

def download_file(url, path):
    if os.path.exists(path):
        # print(f'[SKIP] Already exists: {path}')
        return

    print(f'Downloading: {url} -> {path}')
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        resp = requests.get(url, stream=True, timeout=60)
        if resp.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)
        else:
            print(f'Failed to download (status {resp.status_code}): {url}')
    except Exception as e:
        print(f'Failed to download (exception): {url} {e}')

def main():
    if not os.path.exists(HTML_FILE):
        print(f'Error: {HTML_FILE} not found.')
        return

    with open(HTML_FILE, 'r', encoding='UTF-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    accordions = soup.find_all('div', class_='section-heading')
    
    # Collection containers
    valid_pairs = []
    unmatched_papers = []
    
    # Track years for reporting
    years_data = {} # year -> {'HSC': count, 'SSC': count}

    for accordion in accordions:
        # 1. Find Year in Accordion Heading
        span_en = accordion.find('span', class_='lang-en')
        if not span_en: continue
        
        header_text = span_en.get_text(strip=True)
        year = get_header_year(header_text)
        if not year: continue
        
        if year not in years_data:
            years_data[year] = {'HSC': 0, 'SSC': 0}

        # 2. Get Body
        a_tag = accordion.find('a', attrs={'data-target': True})
        if not a_tag: continue
        target_id = a_tag['data-target'].replace('#', '')
        collapse_div = soup.find('div', id=target_id)
        if not collapse_div: continue
        
        # 3. Collect Papers in this Body
        rows = collapse_div.find_all('tr')
        
        # Local matched items for this year/section
        # We need to separate QPs and MSs first
        section_qps = []
        section_mss = []
        
        for tr in rows:
            name_td = tr.find('td')
            if not name_td: continue
            span_name = name_td.find('span', class_='lang-en')
            if not span_name: continue
            
            paper_name = span_name.get_text(strip=True)
            
            # Filter: Dhivehi AND Paper 2
            if 'Dhivehi' not in paper_name: continue
            
            # Check for Paper 2/II
            lower_name = paper_name.lower()
            is_paper_2 = ('paper 2' in lower_name or 'paper ii' in lower_name)
            if not is_paper_2: continue
            
            # Get URL
            link_td = tr.find_all('td')[-1]
            a_link = link_td.find('a', href=True)
            if not a_link: continue
            abs_url = urljoin(BASE_URL, a_link['href'])
            
            # Level
            level = ''
            if 'SSC' in paper_name: level = 'SSC'
            elif 'HSC' in paper_name: level = 'HSC'
            else: continue
            
            # Attributes
            month, specimen = get_paper_details(paper_name)
            is_ms = ('Marking Scheme' in paper_name or 'marking scheme' in paper_name or 'Marking scheme' in paper_name)
            
            item = {
                'level': level,
                'year': year,
                'month': month,
                'specimen': specimen,
                'url': abs_url,
                'original_name': paper_name,
                'is_ms': is_ms
            }
            
            if is_ms:
                section_mss.append(item)
            else:
                section_qps.append(item)
        
        # 4. Pair QPs with MSs for this Year
        # We look for a matching MS for each QP
        
        for qp in section_qps:
            found_ms = None
            
            # Strategy 1: Specific Match (Month & Specimen match)
            for ms in section_mss:
                if ms['level'] == qp['level'] and ms['month'] == qp['month'] and ms['specimen'] == qp['specimen']:
                    found_ms = ms
                    break
            
            # Strategy 2: Generic fallback (Matches Level, but MS has no Month/Specimen details)
            if not found_ms:
                for ms in section_mss:
                    if ms['level'] == qp['level'] and ms['month'] == '' and ms['specimen'] == '':
                        found_ms = ms
                        break
                        
            if found_ms:
                # Construct Name properly
                # Format: [Level] [Year] [Month] [Specimen]
                parts = [qp['level'], qp['year'], qp['month'], qp['specimen']]
                name = ' '.join([p for p in parts if p])
                
                # Check Uniqueness (though logic shouldn't duplicate unless same paper listed twice)
                # But we append to valid_pairs
                
                valid_pairs.append({
                    "name": name,
                    "paper_url": qp['url'],
                    "marking_scheme_url": found_ms['url']
                })
                
                # Update stats
                years_data[year][qp['level']] += 1
                
            else:
                unmatched_papers.append(qp)

    # 5. Output Results
    # Print unmatched
    print("--- Papers without Matching Marking Scheme ---")
    if unmatched_papers:
        for p in unmatched_papers:
            print(f"{p['year']} {p['original_name']}")
    else:
        print("None")
        
    # Print Missing Years (Years without at least 1 HSC and 1 SSC)
    print("\n--- Years with Invalid Data (Missing HSC or SSC pair) ---")
    missing_data_years = []
    for year, counts in sorted(years_data.items()):
        if counts['HSC'] < 1 or counts['SSC'] < 1:
            missing_data_years.append(f"{year} (HSC: {counts['HSC']}, SSC: {counts['SSC']})")
            
    if missing_data_years:
        for y in missing_data_years:
            print(y)
    else:
        print("None")
        
    print(f"\nTotal Valid Pairs to Download: {len(valid_pairs)}")
    
    # 6. Download
    for pair in valid_pairs:
        name = pair['name']
        
        # Folders
        folder_path = os.path.join(DEST_ROOT, name)
        
        # Files
        paper_path = os.path.join(folder_path, sanitize(f"{name}.pdf"))
        ms_path = os.path.join(folder_path, sanitize(f"{name} Marking Scheme.pdf"))
        
        download_file(pair['paper_url'], paper_path)
        download_file(pair['marking_scheme_url'], ms_path)

    # 7. Download Unmatched Papers (Missing MS)
    if unmatched_papers:
        print(f"\nDownloading {len(unmatched_papers)} papers with missing marking schemes to {MISSING_MS_ROOT}...")
        for qp in unmatched_papers:
            # Construct name: [Level] [Year] [Month] [Specimen]
            parts = [qp['level'], qp['year'], qp['month'], qp['specimen']]
            name = ' '.join([p for p in parts if p])
            
            # File
            file_name = sanitize(f"{name}.pdf")
            path = os.path.join(MISSING_MS_ROOT, file_name)
            
            download_file(qp['url'], path)

if __name__ == '__main__':
    main()
