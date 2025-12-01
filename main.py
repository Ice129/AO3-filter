import math
import random
import time
import asyncio
import aiohttp

from bs4 import BeautifulSoup

from OllamaAI import OllamaAI

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_user_input():
    """Get user input for scraping parameters."""
    url = input("Enter the AO3 URL with desired filters applied: ")
    pages = int(input("Enter the number of pages to scrape: "))
    search_param = input("Enter what type of works you are interested in, in natural language: ")
    return url, pages, search_param

def fetch_page_with_selenium(url):
    """
    Fetch AO3 page content using Selenium.
    
    Args:
        url: The URL to fetch
    
    Returns:
        HTML content as string, or None if it fails
    """
    try:
        
        print("\n" + "="*80)
        print("Fetching page with Selenium...")
        print("="*80 + "\n")
        
        # Set up Chrome options for headless browsing
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36')
        
        print("Initializing Chrome browser...")
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            print(f"Navigating to: {url}")
            driver.get(url)
            
            print("Waiting for page to load...")
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)
            
            html_content = driver.page_source
            print(f"✓ Successfully fetched page ({len(html_content)} bytes)\n")
            print("="*80 + "\n")
            
            return html_content
            
        finally:
            driver.quit()
            
    except ImportError:
        print("Error: Selenium not installed. Install with: pip install selenium")
        return None
    except Exception as e:
        print(f"Error fetching page with Selenium: {str(e)}")
        return None


def extract_stat_value(stats, class_name):
    """
    Extract integer stat value from AO3 stats section.
    
    Args:
        stats: BeautifulSoup stats element
        class_name: CSS class name to search for
    
    Returns:
        Integer value or 0 if not found
    """
    tag = stats.find('dd', class_=class_name)
    if not tag:
        return 0
    
    link = tag.find('a')
    text = link.get_text(strip=True) if link else tag.get_text(strip=True)
    
    try:
        return int(text.replace(',', ''))
    except ValueError:
        return 0


def parse_ao3_html(html_content):
    """
    Parse AO3 HTML content and extract fic information.
    
    Args:
        html_content: HTML string to parse
    
    Returns:
        List of fic dictionaries
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    works = soup.find_all('li', id=lambda x: x and x.startswith('work_'))
    fics = []
    
    for work in works:
        # Extract title and URL
        title_tag = work.find('h4', class_='heading')
        title_link = title_tag.find('a') if title_tag else None
        title = title_link.get_text(strip=True) if title_link else 'N/A'
        url = f"https://archiveofourown.org{title_link['href']}" if title_link and title_link.get('href') else 'N/A'
        
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
        word_count = 0
        chapters = 'N/A'
        chapters_complete = False
        comments = 0
        kudos = 0
        
        if stats:
            word_count = extract_stat_value(stats, 'words')
            
            chapters_tag = stats.find('dd', class_='chapters')
            if chapters_tag:
                chapters = chapters_tag.get_text(strip=True)
                if '/' in chapters:
                    parts = chapters.split('/')
                    if parts[0] == parts[1]:
                        chapters_complete = True
            
            comments = extract_stat_value(stats, 'comments')
            kudos = extract_stat_value(stats, 'kudos')
        
        fic_info = {
            'title': title,
            'url': url,
            'fandoms': fandoms,
            'rating': rating,
            'warnings': warnings,
            'category': category,
            'is_complete': is_complete,
            'warnings_tags': warnings_tags,
            'relationships': relationships,
            'characters': characters,
            'freeform_tags': freeform_tags,
            'summary': summary,
            'word_count': word_count,
            'chapters': chapters,
            'chapters_complete': chapters_complete,
            'comments': comments,
            'kudos': kudos,
        }
        fics.append(fic_info)
    
    return fics

def scrape_ao3_page(base_url):
    """
    Scrape an AO3 page using Selenium.
    
    Args:
        base_url: URL to scrape
    
    Returns:
        List of fic dictionaries
    """
    html_content = fetch_page_with_selenium(base_url)
    
    if html_content is None:
        print("Failed to fetch page. Skipping...\n")
        return []
    
    return parse_ao3_html(html_content)


def scrape_multiple_pages(url, pages):
    """
    Scrape multiple pages of AO3 search results.
    
    Args:
        url: Base URL with search filters applied
        pages: Number of pages to scrape
    
    Returns:
        List of all fic dictionaries from all pages
    """
    fics = []
    max_page_retries = 2
    
    for page_num in range(pages):
        current_url = f"{url}&page={page_num + 1}"
        print(f"Scraping page {page_num + 1}...")
        
        fics_on_page = []
        for retry_count in range(max_page_retries):
            try:
                fics_on_page = scrape_ao3_page(current_url)
                
                if len(fics_on_page) == 0 and retry_count < max_page_retries - 1:
                    print("No works found. Retrying in 10 seconds...")
                    time.sleep(10)
                else:
                    break
            except Exception as e:
                print(f"Error scraping page: {str(e)}")
                if retry_count < max_page_retries - 1:
                    wait_time = (retry_count + 1) * 15
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"Failed to scrape page {page_num + 1} after {max_page_retries} attempts. Skipping...")
        
        fics.extend(fics_on_page)
        
        # # Rate limiting between pages
        # if page_num < pages - 1:
        #     wait_time = random.uniform(8, 15)
        #     print(f"Waiting {wait_time:.1f} seconds before next page...")
        #     time.sleep(wait_time)
    
    print(f"\n{'='*80}")
    print(f"Successfully scraped {len(fics)} works from {pages} page(s)")
    print(f"{'='*80}\n")
    
    return fics

async def score_fic_batch_async(fics_batch, search_param, ai, batch_num, total_batches):
    """Score a batch of fics concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for fic in fics_batch:
            
            fic_summary = (
                f"Title: {fic['title']}\n"
                f"Fandoms: {', '.join(fic['fandoms'])}\n"
                f"Warnings: {fic['warnings']}\n"
                f"Warnings Tags: {', '.join(fic['warnings_tags'])}\n"
                f"Relationships: {', '.join(fic['relationships'])}\n"
                f"Characters: {', '.join(fic['characters'])}\n"
                f"Tags: {', '.join(fic['freeform_tags'])}\n"
                f"Summary: {fic['summary']}\n"
                f"Word Count: {fic['word_count']}\n"
            )
            prompt = f"fic info:\n{fic_summary}\n\nUSER SEARCH PARAMETER: {search_param}"
            tasks.append(ai.send_message_async(prompt, session))
        
        print(f"Processing batch {batch_num}/{total_batches} ({len(fics_batch)} fics)...")
        responses = await asyncio.gather(*tasks)
        
        for fic, response in zip(fics_batch, responses):
            try:
                word_count_rank = int(response.split("<Word Count: ")[1].split(">")[0])
                relationship_rank = int(response.split("<Relationship: ")[1].split(">")[0])
                overall_relevance_rank = int(response.split("<Overall Relevance: ")[1].split(">")[0])
                fic_ranking = word_count_rank + relationship_rank + overall_relevance_rank
            except (IndexError, ValueError):
                fic_ranking = 15
                print(f"Warning: Failed to parse ranking for '{fic['title']}'. Using default rank of 15.")
            
            fic['llm_rank'] = fic_ranking
        
        return fics_batch

def rank_fics_with_scoring(fics, search_param, batch_size=10):
    """
    Rank fics using LLM scoring system with batch processing for speed.
    
    Args:
        fics: List of fic dictionaries to rank
        search_param: User's search criteria
        batch_size: Number of fics to score concurrently (default: 10)
    
    Returns:
        List of fics sorted by LLM score (highest to lowest)
    """
    ai = OllamaAI(ai_model, 2, max_history_pairs=0)
    print(f"Scoring {len(fics)} fics in batches of {batch_size}...")
    print("(Press Ctrl+C to stop ranking and continue with ranked fics only)")
    
    batches = [fics[i:i + batch_size] for i in range(0, len(fics), batch_size)]
    total_batches = len(batches)
    
    try:
        for batch_num, batch in enumerate(batches, 1):
            asyncio.run(score_fic_batch_async(batch, search_param, ai, batch_num, total_batches))
    except KeyboardInterrupt:
        print(f"\n\n{'='*80}")
        ranked_count = sum(1 for fic in fics if 'llm_rank' in fic)
        print(f"Ranking interrupted! Proceeding with {ranked_count} ranked fics out of {len(fics)} total.")
        print(f"{'='*80}\n")
    
    ranked_fics = [fic for fic in fics if 'llm_rank' in fic]
    ordered_fics = sorted(ranked_fics, reverse=True, key=lambda x: x['llm_rank'])
    
    print(f"\n{'='*80}")
    print(f"Fics sorted by LLM ranking ({len(ordered_fics)} fics):")
    for fic in ordered_fics:
        print(f"Title: {fic['title']}, LLM Rank: {fic['llm_rank']}")
    
    return ordered_fics

def create_markdown_output(fics, filename="filtered_fics.md"):
    """
    Create a markdown file with all fics information formatted nicely.
    
    Args:
        fics: List of fic dictionaries with their information
        filename: Name of the output markdown file
    """
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# Filtered AO3 Fics\n\n")
        f.write(f"**Total fics:** {len(fics)}\n\n")
        f.write("---\n\n")
        
        for idx, fic in enumerate(fics, 1):
            f.write(f"## {idx}. [{fic['title']}]({fic['url']})\n\n")
            
            if 'tournament_rank' in fic:
                f.write(f"**Tournament Rank:** {fic['tournament_rank']}\n\n")
            
            if 'llm_rank' in fic:
                f.write(f"**LLM Rank:** {fic['llm_rank']}\n\n")
            
            f.write(f"**Rating:** {fic['rating']}  \n")
            f.write(f"**Category:** {fic['category']}  \n")
            f.write(f"**Status:** {'Complete' if fic['is_complete'] else 'In Progress'}  \n")
            f.write(f"**Chapters:** {fic['chapters']}  \n")
            f.write(f"**Word Count:** {fic['word_count']:,}  \n\n")
            
            if fic['fandoms']:
                f.write(f"**Fandoms:** {' '.join(f'`{fandom}`' for fandom in fic['fandoms'])}  \n\n")
            
            if fic['warnings'] != 'N/A':
                f.write(f"**Warnings:** {fic['warnings']}  \n\n")
            
            if fic['relationships']:
                f.write(f"**Relationships:** {' '.join(f'`{rel}`' for rel in fic['relationships'])}  \n\n")
            
            if fic['characters']:
                f.write(f"**Characters:** {' '.join(f'`{char}`' for char in fic['characters'])}  \n\n")
            
            if fic['freeform_tags']:
                f.write(f"**Tags:** {' '.join(f'`{tag}`' for tag in fic['freeform_tags'])}  \n\n")
            
            if fic['summary'] != 'N/A':
                f.write("**Summary:**\n\n")
                f.write(f"> {fic['summary']}\n\n")
            
            f.write(f"**Stats:** {fic['kudos']} kudos | {fic['comments']} comments  \n\n")
            f.write("---\n\n")
    
    print(f"\n{'='*80}")
    print(f"Markdown file created: {filename}")
    print(f"{'='*80}\n")

async def compare_fics_batch_async(comparisons, search_param, ai):
    """
    Compare multiple pairs of fics concurrently.
    
    Args:
        comparisons: List of tuples (fic1, fic2, comparison_num, total_comparisons)
        search_param: User's search criteria
        ai: OllamaAI instance
    
    Returns:
        List of boolean results (True if fic1 better, False if fic2 better)
    """
    async with aiohttp.ClientSession() as session:
        tasks = []
        for fic1, fic2, comp_num, total_comp in comparisons:
            fic1_tags = ', '.join(fic1.get('freeform_tags', [])) or 'None'
            fic2_tags = ', '.join(fic2.get('freeform_tags', [])) or 'None'
            
            fic1_summary = (
                f"Title: {fic1['title']}\n"
                f"Fandoms: {', '.join(fic1['fandoms'])}\n"
                f"Warnings: {fic1['warnings']}\n"
                f"Warnings Tags: {', '.join(fic1['warnings_tags'])}\n"
                f"Relationships: {', '.join(fic1['relationships'])}\n"
                f"Characters: {', '.join(fic1['characters'])}\n"
                f"Tags: {', '.join(fic1['freeform_tags'])}\n"
                f"Summary: {fic1['summary']}\n"
                f"Word Count: {fic1['word_count']}\n"
            )
            fic2_summary = (
                f"Title: {fic2['title']}\n"
                f"Fandoms: {', '.join(fic2['fandoms'])}\n"
                f"Warnings: {fic2['warnings']}\n"
                f"Warnings Tags: {', '.join(fic2['warnings_tags'])}\n"
                f"Relationships: {', '.join(fic2['relationships'])}\n"
                f"Characters: {', '.join(fic2['characters'])}\n"
                f"Tags: {', '.join(fic2['freeform_tags'])}\n"
                f"Summary: {fic2['summary']}\n"
                f"Word Count: {fic2['word_count']}\n"
            )
            
            prompt = (
                
                f"Fic 1:\n{fic1_summary}\n\n"
                f"Fic 2:\n{fic2_summary}\n\n"
                f"Compare these two fics strictly based on the user's preferences: {search_param}"
            )
            tasks.append(ai.send_message_async(prompt, session))
        
        responses = await asyncio.gather(*tasks)
        results = []
        
        for (fic1, fic2, comp_num, total_comp), response in zip(comparisons, responses):
            response_lower = response.lower()
            print(f"{comp_num}/{total_comp}: '{fic1['title']}' vs '{fic2['title']}' -> {response.strip()}")
            
            if "<fic 1>" in response_lower or ("fic 1" in response_lower and "fic 2" not in response_lower):
                results.append(True)
            elif "<fic 2>" in response_lower or ("fic 2" in response_lower and "fic 1" not in response_lower):
                results.append(False)
            else:
                try:
                    fic_id = response_lower.split("<")[1].split(">")[0]
                    fic_number = int(''.join(filter(str.isdigit, fic_id)))
                    results.append(fic_number == 1)
                except:
                    results.append(random.choice([True, False]))
        
        return results

def compare_fics_with_llm(fic1, fic2, ai, search_param, comparison_num=None, total_comparisons=None):
    """
    Compare two fics using LLM and return True if fic1 is better than fic2.
    Synchronous wrapper for single comparisons.
    
    Args:
        fic1: First fic dictionary
        fic2: Second fic dictionary
        ai: OllamaAI instance
        search_param: User's search criteria
        comparison_num: Current comparison number (optional)
        total_comparisons: Total expected comparisons (optional)
    
    Returns:
        True if fic1 is better, False if fic2 is better
    """
    comparisons = [(fic1, fic2, comparison_num or 1, total_comparisons or 1)]
    results = asyncio.run(compare_fics_batch_async(comparisons, search_param, ai))
    return results[0]

def merge_sorted_lists(left, right, ai, search_param, depth, state, batch_size=8):
    """
    Merge two sorted lists of fics by comparing items at the boundaries with batch processing.
    
    Args:
        left: Sorted list of fics (best to worst)
        right: Sorted list of fics (best to worst)
        ai: OllamaAI instance
        search_param: User's search criteria
        depth: Current recursion depth for logging
        state: Dictionary to track comparison progress
        batch_size: Number of comparisons to process concurrently
    
    Returns:
        Merged sorted list (best to worst)
    """
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        # Collect batch of comparisons
        comparisons = []
        temp_indices = []
        
        while i < len(left) and j < len(right) and len(comparisons) < batch_size:
            comparisons.append((left[i], right[j], state['current'] + len(comparisons) + 1, state['total']))
            temp_indices.append((i, j))
            # Look ahead to next potential comparison
            if i + 1 < len(left) and j < len(right):
                i += 1
            elif i < len(left) and j + 1 < len(right):
                j += 1
            else:
                break
        
        # Reset indices to process comparisons sequentially with batch results
        i, j = temp_indices[0]
        
        # Process batch
        if comparisons:
            results = asyncio.run(compare_fics_batch_async(comparisons[:1], search_param, ai))
            state['current'] += 1
            
            if results[0]:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])
    
    return result

def merge_sort_fics(fics, ai, search_param, state):
    """
    Recursively sort fics using merge sort with LLM comparisons.
    
    Args:
        fics: List of fic dictionaries to sort
        ai: OllamaAI instance
        search_param: User's search criteria
        state: Dictionary to track comparison progress
    
    Returns:
        Sorted list of fics from best (rank 1) to worst (rank N)
    """
    if len(fics) <= 1:
        return fics
    
    if len(fics) == 2:
        state['current'] += 1
        if compare_fics_with_llm(fics[0], fics[1], ai, search_param, state['current'], state['total']):
            return [fics[0], fics[1]]
        else:
            return [fics[1], fics[0]]
    
    mid = len(fics) // 2
    left_sorted = merge_sort_fics(fics[:mid], ai, search_param, state)
    right_sorted = merge_sort_fics(fics[mid:], ai, search_param, state)
    
    return merge_sorted_lists(left_sorted, right_sorted, ai, search_param, 0, state)

def rank_fics_with_tournament(fics, search_param):
    """
    Rank fics using merge sort with LLM pairwise comparisons.
    Establishes absolute rankings from 1st to Nth place.
    
    Args:
        fics: List of fic dictionaries to rank
        search_param: User's search criteria
    
    Returns:
        List of fics sorted from best (rank 1) to worst (rank N)
    """
    if not fics:
        return []
    
    if not search_param or not isinstance(search_param, str):
        raise ValueError("search_param must be a non-empty string")
    
    required_fields = ['title', 'summary', 'freeform_tags', 'word_count', 'kudos']
    for fic in fics:
        missing_fields = [field for field in required_fields if field not in fic]
        if missing_fields:
            raise ValueError(f"Fic '{fic.get('title', 'Unknown')}' missing required fields: {missing_fields}")
    
    # ai = OllamaAI("goekdenizguelmez/JOSIEFIED-Qwen3:4b", 3, max_history_pairs=0)
    ai = OllamaAI(ai_model, 3, max_history_pairs=0)
    
    if len(fics) > 1:
        expected_comparisons = int(len(fics) * 3.5)
    else:
        expected_comparisons = 0
    
    print(f"\nRanking {len(fics)} fics (estimated {expected_comparisons} comparisons)...\n")
    
    state = {'current': 0, 'total': expected_comparisons}
    
    try:
        sorted_fics = merge_sort_fics(fics, ai, search_param, state)
        
        for rank, fic in enumerate(sorted_fics, 1):
            fic['tournament_rank'] = rank
        
        print(f"\n✓ Ranking complete ({state['current']} comparisons)\n")
        
        return sorted_fics
        
    except KeyboardInterrupt:
        print(f"\n\n⚠ Interrupted after {state['current']} comparisons\n")
        return fics

def main():

    url, pages, search_param = get_user_input()

    # hardcoded configuration
    # url = r"""
    # https://archiveofourown.org/works/search?!!!!ADD_YOUR_FILTERS_HERE!!!!
    # """.strip()
    # pages = 3 # Number of pages to scrape
    # search_param = "ADD_YOUR_SEARCH_CRITERIA_HERE."
    
    
    fics = scrape_multiple_pages(url, pages)
    random.shuffle(fics)
    
    # Choose ranking method:
    # Option 1: Tournament ranking (merge sort - O(N log N) comparisons)
    ordered_fics = rank_fics_with_tournament(fics, search_param)
    
    # Option 2: Scoring system (uncomment to use instead)
    # ordered_fics = rank_fics_with_scoring(fics, search_param)
    
    create_markdown_output(ordered_fics)

if __name__ == "__main__":
    ai_model = "goekdenizguelmez/JOSIEFIED-Qwen3:4b"
    main()