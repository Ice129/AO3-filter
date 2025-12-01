# AO3 Filter

A Python tool that scrapes Archive of Our Own (AO3) works and ranks them using AI based on your preferences.

## What It Does

- Scrapes AO3 search results with your filters
- Extracts fic metadata (title, summary, tags, stats, etc.)
- Uses a local AI model (via Ollama) to rank fics based on your search criteria
- Outputs a formatted markdown file with ranked results

## Setup

### Prerequisites

1. **Python 3.7+**
2. **Chrome Browser** (for Selenium)
3. **Ollama** - [Install Ollama](https://ollama.ai)
4. **AI Model** - Pull the model:
   ```bash
   ollama pull goekdenizguelmez/JOSIEFIED-Qwen3:4b
   ```

### Install Dependencies

```bash
pip install selenium beautifulsoup4 aiohttp
```

## How to Use

1. **Configure the script** in `main.py`:
   - Set your AO3 search URL with filters applied
   - Set number of pages to scrape
   - Set your search criteria in natural language

   ```python
   url = "https://archiveofourown.org/works/search?your_filters_here"
   pages = 3
   search_param = "I want long completed fics with happy endings"
   ```

2. **Run the script**:
   ```bash
   python main.py
   ```

3. **View results** in `filtered_fics.md`

## Ranking Methods

The script offers two ranking approaches:

- **Tournament ranking** (default): Uses pairwise comparisons via merge sort - more accurate but slower
- **Scoring system**: Scores each fic independently - faster but less precise

Switch between them by commenting/uncommenting the relevant lines in `main()`.

## Notes

- Be respectful of AO3's servers - the script includes rate limiting
- Processing time depends on the number of fics and ranking method chosen
- You can interrupt ranking with Ctrl+C to proceed with partial results
