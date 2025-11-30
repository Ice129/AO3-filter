import requests
from bs4 import BeautifulSoup

# This script fetches the HTML content of AO3, reads all the info on all the displayed fics
# and extracts + stores the title, author, tags, kudos, word count, summary, and URL of each fic.
# then goes to the next page and repeats the process x many times.
# origional url is given by user, as the filters will be aplied before this script

def get_user_input():
    # url example: https://archiveofourown.org/works/search?work_search%5Bquery%5D=ultrakill&work_search%5Btitle%5D=&work_search%5Bcreators%5D=&work_search%5Brevised_at%5D=&work_search%5Bcomplete%5D=T&work_search%5Bcrossover%5D=&work_search%5Bsingle_chapter%5D=0&work_search%5Bword_count%5D=&work_search%5Blanguage_id%5D=&work_search%5Bfandom_names%5D=&work_search%5Brating_ids%5D=13&work_search%5Bcharacter_names%5D=&work_search%5Brelationship_names%5D=&work_search%5Bfreeform_names%5D=&work_search%5Bhits%5D=&work_search%5Bkudos_count%5D=&work_search%5Bcomments_count%5D=&work_search%5Bbookmarks_count%5D=&work_search%5Bsort_column%5D=kudos_count&work_search%5Bsort_direction%5D=desc&commit=Search
    url = str(input("Enter the AO3 URL with desired filters applied: "))
    pages = int(input("Enter the number of pages to scrape: "))
    search_param = str(input("Enter what type of works you are interested in, in natural language: "))
    return url, pages, search_param

def scrape_AO3_page(base_url):
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    works = soup.find_all('li', id=lambda x: x and x.startswith('work_'))
    fics = []
    for work in works:
        # Extract work ID
        work_id = work.get('id', '').replace('work_', '') if work.get('id') else 'N/A'
        
        # Extract title and URL
        title_tag = work.find('h4', class_='heading')
        title_link = title_tag.find('a') if title_tag else None
        title = title_link.get_text(strip=True) if title_link else 'N/A'
        url = f"https://archiveofourown.org{title_link['href']}" if title_link and title_link.get('href') else 'N/A'
        
        # Extract author
        author_tag = work.find('a', rel='author')
        author = author_tag.get_text(strip=True) if author_tag else 'Anonymous'
        author_url = f"https://archiveofourown.org{author_tag['href']}" if author_tag and author_tag.get('href') else 'N/A'
        
        # Extract fandoms
        fandom_heading = work.find('h5', class_='fandoms')
        fandoms = [fandom.get_text(strip=True) for fandom in fandom_heading.find_all('a', class_='tag')] if fandom_heading else []
        
        # Extract required tags (rating, warnings, category, completion status)
        required_tags = work.find('ul', class_='required-tags')
        rating = 'N/A'
        warnings = 'N/A'
        category = 'N/A'
        is_complete = False
        
        if required_tags:
            rating_tag = required_tags.find('span', class_=lambda x: x and 'rating' in x)
            rating = rating_tag.get('title', 'N/A') if rating_tag else 'N/A'
            
            warning_tag = required_tags.find('span', class_=lambda x: x and 'warning' in x)
            warnings = warning_tag.get('title', 'N/A') if warning_tag else 'N/A'
            
            category_tag = required_tags.find('span', class_=lambda x: x and 'category' in x)
            category = category_tag.get('title', 'N/A') if category_tag else 'N/A'
            
            complete_tag = required_tags.find('span', class_='complete-yes')
            is_complete = complete_tag is not None
        
        # Extract publish date
        date_tag = work.find('p', class_='datetime')
        publish_date = date_tag.get_text(strip=True) if date_tag else 'N/A'
        
        # Extract all tags by category
        tags_section = work.find('ul', class_='tags')
        warnings_tags = []
        relationships = []
        characters = []
        freeform_tags = []
        
        if tags_section:
            warnings_tags = [tag.get_text(strip=True) for tag in tags_section.find_all('li', class_='warnings')]
            relationships = [tag.get_text(strip=True) for tag in tags_section.find_all('li', class_='relationships')]
            characters = [tag.get_text(strip=True) for tag in tags_section.find_all('li', class_='characters')]
            freeform_tags = [tag.get_text(strip=True) for tag in tags_section.find_all('li', class_='freeforms')]
        
        # Extract summary
        summary_tag = work.find('blockquote', class_='summary')
        summary = summary_tag.get_text(separator=' ', strip=True) if summary_tag else 'N/A'
        
        # Extract stats
        stats = work.find('dl', class_='stats')
        
        language = 'N/A'
        word_count = 0
        chapters = 'N/A'
        chapters_complete = False
        comments = 0
        kudos = 0
        bookmarks = 0
        hits = 0
        
        if stats:
            language_tag = stats.find('dd', class_='language')
            language = language_tag.get_text(strip=True) if language_tag else 'N/A'
            
            words_tag = stats.find('dd', class_='words')
            if words_tag:
                try:
                    word_count = int(words_tag.get_text(strip=True).replace(',', ''))
                except ValueError:
                    word_count = 0
            
            chapters_tag = stats.find('dd', class_='chapters')
            if chapters_tag:
                chapters = chapters_tag.get_text(strip=True)
                # Check if chapters are complete (e.g., "5/5" vs "3/5")
                if '/' in chapters:
                    parts = chapters.split('/')
                    if parts[0] == parts[1]:
                        chapters_complete = True
            
            comments_tag = stats.find('dd', class_='comments')
            if comments_tag:
                comments_link = comments_tag.find('a')
                try:
                    comments = int(comments_link.get_text(strip=True).replace(',', '')) if comments_link else 0
                except ValueError:
                    comments = 0
            
            kudos_tag = stats.find('dd', class_='kudos')
            if kudos_tag:
                kudos_link = kudos_tag.find('a')
                try:
                    kudos = int(kudos_link.get_text(strip=True).replace(',', '')) if kudos_link else 0
                except ValueError:
                    kudos = 0
            
            bookmarks_tag = stats.find('dd', class_='bookmarks')
            if bookmarks_tag:
                bookmarks_link = bookmarks_tag.find('a')
                try:
                    bookmarks = int(bookmarks_link.get_text(strip=True).replace(',', '')) if bookmarks_link else 0
                except ValueError:
                    bookmarks = 0
            
            hits_tag = stats.find('dd', class_='hits')
            if hits_tag:
                try:
                    hits = int(hits_tag.get_text(strip=True).replace(',', ''))
                except ValueError:
                    hits = 0
        
        fic_info = {
            'work_id': work_id,
            'title': title,
            'author': author,
            'author_url': author_url,
            'url': url,
            'fandoms': fandoms,
            'rating': rating,
            'warnings': warnings,
            'category': category,
            'is_complete': is_complete,
            'publish_date': publish_date,
            'warnings_tags': warnings_tags,
            'relationships': relationships,
            'characters': characters,
            'freeform_tags': freeform_tags,
            'summary': summary,
            'language': language,
            'word_count': word_count,
            'chapters': chapters,
            'chapters_complete': chapters_complete,
            'comments': comments,
            'kudos': kudos,
            'bookmarks': bookmarks,
            'hits': hits
        }
        fics.append(fic_info)
    return fics

def get_pages(url, pages):
    fics = []
    for x in range(pages):
        current_url = f"{url}&page={x+1}"
        print(f"Scraping page {x+1}...")
        fics.extend(scrape_AO3_page(current_url))
    
    print(f"\n{'='*80}")
    print(f"Successfully scraped {len(fics)} works from {pages} page(s)")
    print(f"{'='*80}\n")
    
    # Print first work as example
    if fics:
        print("Example of first work scraped:")
        print(f"{'='*80}")
        for key, value in fics[0].items():
            if isinstance(value, list):
                print(f"{key}: {', '.join(value) if value else 'N/A'}")
            else:
                print(f"{key}: {value}")
        print(f"{'='*80}\n")
    
    # at this point, fics should contain all the scraped fanfics
    # next part of the program filters and sorts with a local LLM based on user input
    # this part is not to be implemented until page scraping is working correctly
    
    return fics

def LLM_filter_and_sort(fics, search_param):
    # placeholder function for future LLM filtering and sorting
    return "LLM response placeholder", fics

def main():
    url, pages, search_param = get_user_input()
    fics = get_pages(url, pages)
    LLM_response, ordered_fics = LLM_filter_and_sort(fics, search_param)

if __name__ == "__main__":
    main()