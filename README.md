# Specular Crawler

A high-performance, scalable web crawler built with modern Python async capabilities. This crawler is designed for reliability, efficiency, and ease of use, making it perfect for both small-scale scraping tasks and larger web crawling operations.

## Why This Crawler?

- **High Performance**: Built with Python's asyncio for maximum efficiency
- **Memory Efficient**: Streams responses and processes data on-the-fly
- **Production Ready**: Includes robust error handling and retry mechanisms
- **Respectful Crawling**: Built-in rate limiting and domain restrictions
- **Rich Statistics**: Detailed crawling metrics and domain-specific statistics
- **Easy to Extend**: Well-organized codebase with clear separation of concerns
- **Zero Configuration**: Works out of the box with sensible defaults

## Features

- Asynchronous crawling for improved performance
- Configurable crawling depth
- Domain restriction capabilities
- File extension blacklisting
- Rate limiting and concurrent request handling
- Detailed statistics and logging
- JSON output of crawling results
- Automatic retry on failed requests
- Smart memory management
- Comprehensive error handling

## Requirements

This project uses Poetry for dependency management. Make sure you have Poetry installed:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd web-crawler
```

2. Install dependencies with Poetry:
```bash
poetry install
```

## Usage

Basic syntax:
```bash
poetry run python main.py <start_url> --max-depth <depth> [--domains domain1 domain2...] [--blacklist ext1 ext2...]
```

### Required Parameters

- `start_url`: The initial URL to begin crawling (must start with http:// or https://)
- `--max-depth`: Maximum depth of links to crawl (positive integer)

### Optional Parameters

- `--domains`: List of allowed domains to crawl (if none specified, crawls only the start URL's domain)
- `--blacklist`: File extensions to ignore (e.g., pdf, jpg, css)

### Examples

1. Basic crawl with depth limit:
```bash
poetry run python main.py https://python.org --max-depth 1
```

2. Crawl specific domains:
```bash
poetry run python main.py https://python.org --max-depth 2 --domains python.org docs.python.org
```

3. Exclude specific file types:
```bash
poetry run python main.py https://python.org --max-depth 1 --blacklist pdf jpg png css js
```

4. Combined options:
```bash
poetry run python main.py https://python.org --max-depth 2 --domains python.org docs.python.org --blacklist pdf jpg png
```

## Output

The crawler generates two types of output:

1. Console Output:
   - Crawling configuration
   - Real-time progress
   - Summary statistics

2. File Output:
   - `crawler_debug.log`: Detailed logging information
   - `crawler_results_[timestamp].json`: Complete crawling statistics and results

### Sample Output Structure

```json
{
    "total_time_of_script": 44.42,
    "total_number_of_urls_crawled": 586,
    "total_number_of_errors": 0,
    "total_number_of_domains": 1,
    "status_code_statistics": {
        "200": 586
    },
    "domain_statistics": {
        "python.org": {
            "total_time_to_crawl": 44.41,
            "total_number_of_crawled_urls": 586,
            "total_number_of_errors": 0,
            "status_code_statistics": {
                "200": 586
            }
        }
    }
}
```

## Project Structure

```
crawler/
├── __init__.py
├── main.py
├── utils/
│   ├── __init__.py
│   ├── arguments.py
│   ├── stats.py
│   └── logging_config.py
├── core/
│   ├── __init__.py
│   ├── crawler.py
│   └── fetcher.py
└── constants.py
```

## Dependencies

The project uses Poetry for dependency management. Key dependencies include:
- aiohttp: For async HTTP requests
- beautifulsoup4: For HTML parsing
- aiohttp-retry: For retry logic
- logging: For debug information

## Limitations

- Respects robots.txt by default
- Rate limited to prevent server overload
- Some websites may block automated crawling
- Deep crawls may take significant time

## Error Handling

The crawler includes robust error handling for:
- Network timeouts
- Invalid URLs
- Server errors
- Rate limiting
- Domain restrictions
