import tagui as t
import csv, os, argparse, datetime
import urllib.parse
from collections import Counter

# --- Setup output dirs ---
os.makedirs('outputs/tags', exist_ok=True)
os.makedirs('outputs/screenshots', exist_ok=True)

# --- Argument Parsing ---
parser = argparse.ArgumentParser()
parser.add_argument('--headless', action='store_true', help='Run in headless mode')
args = parser.parse_args()

# --- Start Automation ---
t.init(visual_automation=True, chrome_browser=True)

# --- LOGIN ---
t.url('https://quotes.toscrape.com/login')
t.type('input[name="username"]', 'admin')
t.type('input[name="password"]', 'admin')
t.click('input[type="submit"]')
t.wait(2)

# --- MAIN QUOTE SCRAPE ---
all_quotes = []
author_details = {}
seen_quotes = set()
seen_authors = set()

page = 1
while True:
    print(f'--- Scraping Main Page {page} ---')
    quote_count = int(t.dom("document.querySelectorAll('.quote').length") or 0)

    for i in range(quote_count):
        quote_selector = f"document.querySelectorAll('.quote')[{i}].querySelector('.text')"
        author_selector = f"document.querySelectorAll('.quote')[{i}].querySelector('small')"
        link_selector = f"document.querySelectorAll('.quote')[{i}].querySelector('a')"

        quote = t.dom(f"{quote_selector}?.innerText")
        author = t.dom(f"{author_selector}?.innerText")
        author_link = t.dom(f"{link_selector}?.getAttribute('href')")

        if quote and author:
            quote = quote.strip()
            author = author.strip()

            if quote not in seen_quotes:
                print(f'✔ Quote: {quote[:60]}... | Author: {author}')
                seen_quotes.add(quote)
                all_quotes.append((quote, author))

                # Author scraping
                if author not in seen_authors and author_link:
                    seen_authors.add(author)
                    t.url('https://quotes.toscrape.com' + author_link)
                    t.wait(1.5)

                    name = t.dom("document.querySelector('h3.author-title')?.innerText") or ''
                    birth = t.dom("document.querySelector('.author-born-date')?.innerText") or ''
                    location = t.dom("document.querySelector('.author-born-location')?.innerText") or ''
                    desc = t.dom("document.querySelector('.author-description')?.innerText") or ''
                    author_details[author] = (name.strip(), birth.strip(), location.strip(), desc.strip())

                    t.keyboard('[cmd][left]')  # browser back on macOS
                    t.wait(1.5)

    t.snap('page', f'outputs/screenshots/main_page{page}.png')

    if t.present('li.next a'):
        t.click('li.next a')
        t.wait(2)
        page += 1
    else:
        break

# --- SAVE QUOTES ---
with open('outputs/all_quotes.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Quote', 'Author'])
    writer.writerows(all_quotes)

# --- SAVE AUTHORS ---
with open('outputs/authors.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Author', 'Birth Date', 'Location', 'Description'])
    for author, (name, birth, loc, desc) in author_details.items():
        writer.writerow([name, birth, loc, desc])

# --- TAG SCRAPING ---
t.url('https://quotes.toscrape.com/')
t.wait(3)
t.hover('footer')
t.wait(1)

# Use fallback list due to tag rendering issues
tags = [
    "love", "inspirational", "life", "humor", "books", "reading",
    "friendship", "truth", "simile", "deep-thoughts", "abilities", "change"
]
print(f'\n🟢 Using fallback tag list: {tags}')

for tag in tags:
    print(f'\n--- Scraping tag: {tag} ---')
    t.url(f'https://quotes.toscrape.com/tag/{urllib.parse.quote(tag)}/page/1/')
    t.wait(2)

    tag_quotes = []
    tag_page = 1
    while True:
        quote_count = int(t.dom("document.querySelectorAll('.quote').length") or 0)
        for i in range(quote_count):
            quote = t.dom(f"document.querySelectorAll('.quote')[{i}].querySelector('.text')?.innerText").strip()
            author = t.dom(f"document.querySelectorAll('.quote')[{i}].querySelector('small')?.innerText").strip()
            if quote and author:
                tag_quotes.append((quote, author))

        t.snap('page', f'outputs/screenshots/{tag}_page{tag_page}.png')

        if t.present('li.next a'):
            t.click('li.next a')
            t.wait(2)
            tag_page += 1
        else:
            break

    with open(f'outputs/tags/{tag}.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Quote', 'Author'])
        writer.writerows(tag_quotes)

# --- REPORT ---
combined_quotes = all_quotes[:]
for tag in tags:
    tag_file = f'outputs/tags/{tag}.csv'
    if os.path.exists(tag_file):
        with open(tag_file, encoding='utf-8') as f:
            lines = f.readlines()[1:]  # skip header
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    combined_quotes.append((parts[0].strip('"'), parts[1]))

author_counts = Counter(author for _, author in combined_quotes)

with open('outputs/report.txt', 'w', encoding='utf-8') as f:
    f.write(f"Scraped on: {datetime.datetime.now()}\n")
    f.write(f"Total Quotes: {len(combined_quotes)}\n")
    f.write(f"Unique Authors: {len(author_counts)}\n\n")
    f.write("Top 5 Authors:\n")
    for author, count in author_counts.most_common(5):
        f.write(f"{author}: {count} quotes\n")

print(f'\n✅ Finished scraping. See "outputs/" folder.')
t.close()