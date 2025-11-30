import requests
from bs4 import BeautifulSoup
from OllamaAI import OllamaAI
import random

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
            # 'work_id': work_id,
            'title': title,
            # 'author': author,
            # 'author_url': author_url,
            'url': url,
            'fandoms': fandoms,
            'rating': rating,
            'warnings': warnings,
            'category': category,
            'is_complete': is_complete,
            # 'publish_date': publish_date,
            'warnings_tags': warnings_tags,
            'relationships': relationships,
            'characters': characters,
            'freeform_tags': freeform_tags,
            'summary': summary,
            # 'language': language,
            'word_count': word_count,
            'chapters': chapters,
            'chapters_complete': chapters_complete,
            'comments': comments,
            'kudos': kudos,
            # 'bookmarks': bookmarks,
            # 'hits': hits
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
    
    return fics

def LLM_filter_and_sort(fics, search_param):
    ai = OllamaAI("goekdenizguelmez/JOSIEFIED-Qwen3:4b", 2, max_history_pairs=1)
    print(f"Sending {len(fics)} fics to LLM for filtering and sorting...")
    print("(Press Ctrl+C to stop ranking and continue with ranked fics only)")
    x = 0
    try:
        for fic in fics:
            fic_summary = f"Title: {fic['title']}\nSummary: {fic['summary']}\nTags: {', '.join(fic['freeform_tags'])}\nWord Count: {fic['word_count']}\nKudos: {fic['kudos']}\n\n"
            response = ai.send_message(f"fic info:\n{fic_summary}\n\nUSER SEARCH PARAMETER: {search_param}")
            # rank is extracted from response in format "<rank: XX>"
            # fic_ranking = int(response.split("<rank: ")[1].split(">")[0])
            try:
                word_count_rank = int(response.split("<Word Count: ")[1].split(">")[0])
                relationship_rank = int(response.split("<Relationship: ")[1].split(">")[0])
                overall_relevance_rank = int(response.split("<Overall Relevance: ")[1].split(">")[0])
                fic_ranking = word_count_rank + relationship_rank + overall_relevance_rank
            except (IndexError, ValueError):
                # Default to rank of 5 for each category if parsing fails
                word_count_rank = 5
                relationship_rank = 5
                overall_relevance_rank = 5
                fic_ranking = 15
                print(f"Warning: Failed to parse ranking for '{fic['title']}'. Using default rank of 15.")
            fic['llm_rank'] = fic_ranking
            # Chat history is now automatically maintained with sliding window (last 3 fics)
            # ai.wipe_chat_history() - REMOVED to enable contextual ranking
            x += 1
            
            #debug print
            print(f"\n---\nAI response for Fic {x}:\n{response}\n---")
            
            print(f"Fic {x}: '{fic['title']}' assigned LLM rank: {fic_ranking}")
    except KeyboardInterrupt:
        print(f"\n\n{'='*80}")
        print(f"Ranking interrupted! Proceeding with {x} ranked fics out of {len(fics)} total.")
        print(f"{'='*80}\n")
    
    # filter to only fics that have been ranked (have 'llm_rank' key)
    ranked_fics = [fic for fic in fics if 'llm_rank' in fic]
    
    # sort fics by llm_rank
    ordered_fics = sorted(ranked_fics, reverse=True, key=lambda x: x['llm_rank'])
    print(f"\n{'='*80}")
    print(f"Fics sorted by LLM ranking ({len(ordered_fics)} fics):")
    for fic in ordered_fics:
        print(f"Title: {fic['title']}, LLM Rank: {fic['llm_rank']}")
    return ordered_fics

def LLM_make_mark_scheme(search_param):
    ai = OllamaAI("goekdenizguelmez/JOSIEFIED-Qwen3:4b", 1)
    print("Generating mark scheme based on user search parameters...")
    response = ai.send_message(f"USER SEARCH PARAMETER: {search_param}")
    print(f"\n{'='*80}")
    print("Generated Mark Scheme:")
    print(response)
    print(f"{'='*80}\n")
    
    # Create combined system prompt (file 0 + mark scheme) and save as file 2
    with open("0", "r") as f:
        base_prompt = f.read()
    
    combined_prompt = f"{base_prompt}\n\n--- MARK SCHEME ---\n{response}"
    
    with open("2", "w", encoding="utf-8") as f:
        f.write(combined_prompt)
    
    print("Combined system prompt saved to file '2'\n")
    
    return response

def create_markdown_output(fics, filename="filtered_fics.md"):
    """
    Creates a markdown file with all fics information formatted nicely.
    
    Args:
        fics: List of fic dictionaries with their information
        filename: Name of the output markdown file
    """
    with open(filename, 'w', encoding='utf-8') as f:
        # Write header
        f.write("# Filtered AO3 Fics\n\n")
        f.write(f"**Total fics:** {len(fics)}\n\n")
        f.write("---\n\n")
        
        # Write each fic
        for idx, fic in enumerate(fics, 1):
            # Title with link
            f.write(f"## {idx}. [{fic['title']}]({fic['url']})\n\n")
            
            # Tournament Rank if available
            if 'tournament_rank' in fic:
                f.write(f"**Tournament Rank:** {fic['tournament_rank']}\n\n")
            
            # LLM Rank if available
            if 'llm_rank' in fic:
                f.write(f"**LLM Rank:** {fic['llm_rank']}\n\n")
            
            # Basic info
            f.write(f"**Rating:** {fic['rating']}  \n")
            f.write(f"**Category:** {fic['category']}  \n")
            f.write(f"**Status:** {'Complete' if fic['is_complete'] else 'In Progress'}  \n")
            f.write(f"**Chapters:** {fic['chapters']}  \n")
            f.write(f"**Word Count:** {fic['word_count']:,}  \n\n")
            
            # Fandoms
            if fic['fandoms']:
                f.write(f"**Fandoms:** {' '.join(f'`{fandom}`' for fandom in fic['fandoms'])}  \n\n")
            
            # Warnings
            if fic['warnings'] != 'N/A':
                f.write(f"**Warnings:** {fic['warnings']}  \n\n")
            
            # Relationships
            if fic['relationships']:
                f.write(f"**Relationships:** {' '.join(f'`{rel}`' for rel in fic['relationships'])}  \n\n")
            
            # Characters
            if fic['characters']:
                f.write(f"**Characters:** {' '.join(f'`{char}`' for char in fic['characters'])}  \n\n")
            
            # Tags
            if fic['freeform_tags']:
                f.write(f"**Tags:** {' '.join(f'`{tag}`' for tag in fic['freeform_tags'])}  \n\n")
            
            # Summary
            if fic['summary'] != 'N/A':
                f.write(f"**Summary:**\n\n")
                f.write(f"> {fic['summary']}\n\n")
            
            # Stats
            f.write(f"**Stats:** {fic['kudos']} kudos | {fic['comments']} comments  \n\n")
            
            # Separator
            f.write("---\n\n")
    
    print(f"\n{'='*80}")
    print(f"Markdown file created: {filename}")
    print(f"{'='*80}\n")

def llm_compare_pair(fic1, fic2, ai, search_param, comparison_cache):
    """
    Compare two fics using LLM and return True if fic1 is better than fic2.
    Uses caching to avoid redundant comparisons.
    
    Args:
        fic1: First fic dictionary
        fic2: Second fic dictionary
        ai: OllamaAI instance
        search_param: User's search criteria
        comparison_cache: Dictionary to cache comparison results
    
    Returns:
        True if fic1 is better, False if fic2 is better
    """
    # Track total attempts
    if hasattr(comparison_cache, '_total_attempts'):
        comparison_cache._total_attempts += 1
    
    # Create cache key using URLs (order-independent) to handle duplicate titles
    cache_key = tuple(sorted([fic1.get('url', fic1['title']), fic2.get('url', fic2['title'])]))  
    
    # Check cache first
    if cache_key in comparison_cache:
        result = comparison_cache[cache_key]
        # Track cache hit (increment counter if it exists)
        if hasattr(comparison_cache, '_hits'):
            comparison_cache._hits += 1
        print(f"{'  ' * 8}💾 Cache hit! Skipping LLM call.")
        # Return True if fic1 was the winner in cached result
        return result == fic1.get('url', fic1['title'])
    
    # Format fic summaries
    fic1_tags = ', '.join(fic1.get('freeform_tags', [])) or 'None'
    fic2_tags = ', '.join(fic2.get('freeform_tags', [])) or 'None'
    fic1_summary = f"Title: {fic1['title']}\nSummary: {fic1['summary']}\nTags: {fic1_tags}\nWord Count: {fic1['word_count']}\nKudos: {fic1['kudos']}"
    fic2_summary = f"Title: {fic2['title']}\nSummary: {fic2['summary']}\nTags: {fic2_tags}\nWord Count: {fic2['word_count']}\nKudos: {fic2['kudos']}"
    
    # Ask LLM to compare
    prompt = f"Compare these two fics based on the user's preferences: {search_param}\n\nFic 1:\n{fic1_summary}\n\nFic 2:\n{fic2_summary}\n\nWhich fic better matches the search criteria? Respond with ONLY '<Fic 1>' or '<Fic 2>'."
    response = ai.send_message(prompt)
    
    # Parse response - check for exact format markers first, then fallback to case-insensitive
    response_lower = response.lower()
    if "<fic 1>" in response_lower or ("fic 1" in response_lower and "fic 2" not in response_lower):
        winner = fic1.get('url', fic1['title'])
        result = True
    elif "<fic 2>" in response_lower or ("fic 2" in response_lower and "fic 1" not in response_lower):
        winner = fic2.get('url', fic2['title'])
        result = False
    else:
        # Unclear response - use random selection as fallback
        result = random.choice([True, False])
        winner = fic1.get('url', fic1['title']) if result else fic2.get('url', fic2['title'])
        print(f"  ⚠ Unclear LLM response: '{response[:50]}...'. Randomly selected: '{fic1['title'] if result else fic2['title']}'")
    
    # Cache the result
    comparison_cache[cache_key] = winner
    
    return result

def merge_sorted_lists(left, right, ai, search_param, comparison_cache, depth):
    """
    Merge two sorted lists of fics by comparing items at the boundaries.
    
    Args:
        left: Sorted list of fics (best to worst)
        right: Sorted list of fics (best to worst)
        ai: OllamaAI instance
        search_param: User's search criteria
        comparison_cache: Dictionary to cache comparison results
        depth: Current recursion depth for logging
    
    Returns:
        Merged sorted list (best to worst)
    """
    result = []
    i = j = 0
    comparisons_this_merge = 0
    
    print(f"{'  ' * depth}Merging {len(left)} and {len(right)} fics...")
    
    while i < len(left) and j < len(right):
        # Compare front items from each list
        if llm_compare_pair(left[i], right[j], ai, search_param, comparison_cache):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
        comparisons_this_merge += 1
    
    # Append remaining items
    result.extend(left[i:])
    result.extend(right[j:])
    
    print(f"{'  ' * depth}✓ Merged into {len(result)} fics ({comparisons_this_merge} comparisons)")
    
    return result

def merge_sort_fics(fics, ai, search_param, comparison_cache, depth=0):
    """
    Recursively sort fics using merge sort with LLM comparisons.
    
    Args:
        fics: List of fic dictionaries to sort
        ai: OllamaAI instance
        search_param: User's search criteria
        comparison_cache: Dictionary to cache comparison results
        depth: Current recursion depth for logging
    
    Returns:
        Sorted list of fics from best (rank 1) to worst (rank N)
    """
    # Base case: 0 or 1 items are already sorted
    if len(fics) <= 1:
        return fics
    
    # Base case: 2 items - direct comparison
    if len(fics) == 2:
        print(f"{'  ' * depth}Comparing: '{fics[0]['title']}' vs '{fics[1]['title']}'")
        if llm_compare_pair(fics[0], fics[1], ai, search_param, comparison_cache):
            return [fics[0], fics[1]]
        else:
            return [fics[1], fics[0]]
    
    # Recursive case: divide and conquer
    mid = len(fics) // 2
    print(f"{'  ' * depth}Dividing {len(fics)} fics into {mid} and {len(fics) - mid}...")
    
    left_sorted = merge_sort_fics(fics[:mid], ai, search_param, comparison_cache, depth + 1)
    right_sorted = merge_sort_fics(fics[mid:], ai, search_param, comparison_cache, depth + 1)
    
    return merge_sorted_lists(left_sorted, right_sorted, ai, search_param, comparison_cache, depth)

def LLM_tournament_style_ranking(fics, search_param):
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
    
    # Validate that fics have required fields
    required_fields = ['title', 'summary', 'freeform_tags', 'word_count', 'kudos']
    for fic in fics:
        missing_fields = [field for field in required_fields if field not in fic]
        if missing_fields:
            raise ValueError(f"Fic '{fic.get('title', 'Unknown')}' missing required fields: {missing_fields}")
    
    ai = OllamaAI("goekdenizguelmez/JOSIEFIED-Qwen3:4b", 3, max_history_pairs=0)
    
    # Create cache with hit tracking
    comparison_cache = {}
    comparison_cache._hits = 0  # Track cache hits
    comparison_cache._total_attempts = 0  # Track total comparison attempts
    
    import math
    
    print(f"\n{'='*80}")
    print(f"Starting Tournament-Style Ranking (Merge Sort Algorithm)")
    print(f"Total fics: {len(fics)}")
    # More accurate formula: N*log2(N) is average, worst case can be up to N*log2(N) + N
    if len(fics) > 1:
        expected_min = int(len(fics) * math.log2(len(fics)) * 0.5)
        expected_max = int(len(fics) * math.log2(len(fics)))
        print(f"Expected comparisons: ~{expected_min} to {expected_max}")
    print(f"{'='*80}\n")
    
    try:
        # Perform merge sort
        sorted_fics = merge_sort_fics(fics, ai, search_param, comparison_cache, depth=0)
        
        # Assign tournament ranks (1 = best)
        for rank, fic in enumerate(sorted_fics, 1):
            fic['tournament_rank'] = rank
        
        print(f"\n{'='*80}")
        print(f"Tournament Ranking Complete!")
        print(f"Total unique comparisons: {len(comparison_cache)}")
        if hasattr(comparison_cache, '_total_attempts'):
            total_attempts = comparison_cache._total_attempts
            cache_hits = comparison_cache._hits
            cache_misses = len(comparison_cache)
            print(f"Cache statistics:")
            print(f"  - Total attempts: {total_attempts}")
            print(f"  - Cache hits: {cache_hits} ({cache_hits/total_attempts*100:.1f}% hit rate)")
            print(f"  - Cache misses (new comparisons): {cache_misses}")
            print(f"  - LLM calls saved: {cache_hits}")
        print(f"{'='*80}\n")
        
        # Display final rankings
        print("Final Tournament Rankings:")
        for rank, fic in enumerate(sorted_fics, 1):
            print(f"  {rank}. '{fic['title']}' (Word Count: {fic['word_count']:,})")
        print()
        
        return sorted_fics
        
    except KeyboardInterrupt:
        print(f"\n\n{'='*80}")
        print(f"Tournament interrupted! Partial rankings may be incomplete.")
        print(f"Comparisons completed: {len(comparison_cache)}")
        print(f"{'='*80}\n")
        return fics

def main():
    # url, pages, search_param = get_user_input()
    url = r"https://archiveofourown.org/works?work_search%5Bsort_column%5D=kudos_count&work_search%5Bother_tag_names%5D=&exclude_work_search%5Barchive_warning_ids%5D%5B%5D=19&exclude_work_search%5Barchive_warning_ids%5D%5B%5D=20&exclude_work_search%5Bfandom_ids%5D%5B%5D=236208&exclude_work_search%5Bfandom_ids%5D%5B%5D=58290284&exclude_work_search%5Bfandom_ids%5D%5B%5D=115270897&exclude_work_search%5Brelationship_ids%5D%5B%5D=63193414&exclude_work_search%5Brelationship_ids%5D%5B%5D=5276584&work_search%5Bexcluded_tag_names%5D=&work_search%5Bcrossover%5D=F&work_search%5Bcomplete%5D=T&work_search%5Bwords_from%5D=&work_search%5Bwords_to%5D=&work_search%5Bdate_from%5D=&work_search%5Bdate_to%5D=&work_search%5Bquery%5D=&work_search%5Blanguage_id%5D=en&commit=Sort+and+Filter&tag_id=Adrian+Chase*s*Reader"
    pages = 1
    search_param = "less than 10k words, but more than 3k. it needs to be aidrian chase x reader. no angst, smut is nice but not required. happy endings preferred. no anal at all, or watersports or oviposition. no fics that use placeholders like (y/n) or (name)."
    fics = get_pages(url, pages)
    random.shuffle(fics)  # shuffle fics to avoid any order bias (shuffles in-place)
    LLM_make_mark_scheme(search_param)
    
    # Choose ranking method:
    # Option 1: Use tournament ranking (merge sort - optimal O(N log N))
    ordered_fics = LLM_tournament_style_ranking(fics, search_param)
    
    # Option 2: Use original scoring system (uncomment to use instead)
    # ordered_fics = LLM_filter_and_sort(fics, search_param)
    
    create_markdown_output(ordered_fics)

if __name__ == "__main__":
    main()