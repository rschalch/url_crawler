import time
from typing import Dict, Any, Tuple
import asyncio
import logging
from aiohttp_retry import RetryClient
from bs4 import BeautifulSoup, SoupStrainer
from urllib.parse import urljoin, urlparse
from aiohttp import ClientError, ClientTimeout

from constants import ALLOWED_CONTENT_TYPES


async def fetch_url(
        url: str,
        client: RetryClient,
        semaphore: asyncio.Semaphore,
        stats: Dict[str, Any],
        domain_stats: Dict[str, Dict],
        domain_semaphores: dict = None,
        last_request_times: dict = None
) -> Tuple[list, str, int]:
    """Fetch a URL and extract its links and title"""
    domain = urlparse(url).netloc
    start_time = time.time()

    if domain not in domain_stats:
        domain_stats[domain] = {
            'total_time_to_crawl': 0,
            'total_number_of_crawled_urls': 0,
            'total_number_of_errors': 0,
            'status_code_statistics': {},
            'first_request_time': start_time,
            'last_request_time': start_time
        }
        base_domain = '.'.join(domain.split('.')[-2:])  # Get base domain (e.g., python.org)
        if not any(base_domain in d for d in domain_stats):
            logging.info(f"Skipping external domain: {domain}")
            return [], "", 0

    # Initialize domain tracking if not provided
    if domain_semaphores is None:
        domain_semaphores = {}
    if last_request_times is None:
        last_request_times = {}

    # Get or create domain semaphore
    if domain not in domain_semaphores:
        domain_semaphores[domain] = asyncio.Semaphore(2)

    async with semaphore, domain_semaphores[domain]:
        last_request_times[domain] = time.time()
        domain_stats[domain]['last_request_time'] = time.time()

        try:
            async with client.get(url, timeout=ClientTimeout(total=20)) as response:
                # Handle rate limiting
                if response.status == 429:
                    domain_stats[domain]['consecutive_429s'] = domain_stats[domain].get('consecutive_429s', 0) + 1
                    wait_time = int(response.headers.get('Retry-After', 30))
                    logging.warning(f"Rate limited on {domain}, waiting {wait_time} seconds")
                    await asyncio.sleep(wait_time)
                    return [], "", 0
                else:
                    domain_stats[domain]['consecutive_429s'] = 0

                # Check content type before processing
                content_type = response.headers.get('Content-Type', '').lower()
                if not any(allowed_type in content_type for allowed_type in ALLOWED_CONTENT_TYPES):
                    logging.info(f"Skipping non-HTML content: {url}")
                    return [], "", 0

                content = await response.text()
                content_size = len(content.encode('utf-8'))
                status = response.status
                content_type = response.headers.get('Content-Type', '').lower()

                # Update statistics
                stats['status_code_statistics'][status] = stats['status_code_statistics'].get(status, 0) + 1
                domain_stats[domain]['status_code_statistics'][status] = \
                    domain_stats[domain]['status_code_statistics'].get(status, 0) + 1

                # Update domain-specific stats
                domain_stats[domain]['total_number_of_crawled_urls'] += 1
                domain_stats[domain]['total_time_to_crawl'] = \
                    time.time() - domain_stats[domain]['first_request_time']

                if 200 <= status < 300:
                    parser = 'html.parser'
                    if 'xml' in content_type or content.lstrip().startswith('<?xml'):
                        parser = 'xml'
                    elif 'xhtml' in content_type:
                        parser = 'lxml'

                    # Only parse <a> and <title> tags
                    parse_only = SoupStrainer(['a', 'title'])
                    soup = BeautifulSoup(content, parser, parse_only=parse_only)

                    # Get title efficiently
                    title_tag = soup.find('title')
                    title = title_tag.string if title_tag else ""

                    # Process links more efficiently
                    links = []
                    for link in soup.find_all('a', href=True):
                        href = link.get('href')
                        if href and not href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                            absolute_url = urljoin(url, href)
                            if absolute_url.startswith(('http://', 'https://')):
                                links.append(absolute_url)

                    logging.info(f"Found {len(links)} links in {url}")
                    return links, title, content_size
                else:
                    stats['total_number_of_errors'] += 1
                    domain_stats[domain]['total_number_of_errors'] += 1
                    return [], "", content_size

        except (asyncio.TimeoutError, ClientError) as e:
            logging.error(f"Network error crawling {url}: {str(e)}")
            stats['total_number_of_errors'] += 1
            domain_stats[domain]['total_number_of_errors'] += 1
            return [], "", 0
        except Exception as e:
            logging.error(f"Error crawling {url}: {str(e)}")
            stats['total_number_of_errors'] += 1
            domain_stats[domain]['total_number_of_errors'] += 1
            return [], "", 0
