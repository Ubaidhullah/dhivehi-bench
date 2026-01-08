import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

HTML_FILE = 'dpe.html'
DEST_ROOT = './papers'
BASE_URL = 'https://dpe.edu.mv/'  # Change if you need a different base URL

def get_paper_info(papername):
    # Identify type (SSC/HSC), year, month, specimen, marking_scheme
    type_match = re.search(r'(SSC|HSC)', papername, re.I)
    year_match = re.search(r'20\d{2}', papername)
    month_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', papername, re.I)
    specimen = 'specimen' in papername.lower()
    marking_scheme = 'marking scheme' in papername.lower()

    type_ = type_match.group(1).upper() if type_match else ''
    year = year_match.group(0) if year_match else ''
    month = month_match.group(1) if month_match else ''
    specimen_str = 'specimen' if specimen else ''
    return type_, year, month, specimen_str, marking_scheme

def build_folder_name(type_, year, month, specimen):
    parts = [p for p in [type_, year, month, specimen] if p]
    return ' '.join(parts)

def build_file_name(folder, marking_scheme):
    if marking_scheme:
        return '{} Marking Scheme.pdf'.format(folder)
    else:
        return '{}.pdf'.format(folder)

def sanitize(s):
    return re.sub(r'[\\/:"*?<>|]+', '', s).strip()

def download_file(url, path):
    print('Downloading:', url, '->', path)
    try:
        resp = requests.get(url, stream=True, timeout=20)
        if resp.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)
        else:
            print('Failed to download (status {}): {}'.format(resp.status_code, url))
    except Exception as e:
        print('Failed to download (exception):', url, e)

def main():
    with open(HTML_FILE, 'r', encoding='UTF-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # Iterate over all rows searching for Paper 2 and Marking Scheme for SSC/HSC Dhivehi
    for td in soup.find_all('td'):
        span_en = td.find('span', class_='lang-en')
        if not span_en:
            continue
        papername = span_en.get_text(strip=True)

        if not (('Dhivehi' in papername) and ('SSC' in papername or 'HSC' in papername) and ('Paper 2' in papername)):
            continue

        # Find link in the same <td>
        a = td.find('a', href=True)
        if not a:
            continue
        href = a['href']
        abs_url = urljoin(BASE_URL, href)
        # Paper info
        type_, year, month, specimen, marking_scheme = get_paper_info(papername)
        if not type_ or not year:
            continue  # insufficient info
        folder = sanitize(build_folder_name(type_, year, month, specimen))
        folder_path = os.path.join(DEST_ROOT, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        filename = sanitize(build_file_name(folder, marking_scheme))
        file_path = os.path.join(folder_path, filename)
        if os.path.exists(file_path):
            print('[SKIP] Already exists:', file_path)
            continue
        download_file(abs_url, file_path)

if __name__ == '__main__':
    main()