import asyncio
import logging
import time
from typing import Dict, Any, Tuple
from urllib.parse import urlparse, urldefrag

from aiohttp import ClientTimeout
import aiohttp
from aiohttp_retry import RetryClient, ExponentialRetry

from constants import MAX_CONCURRENT_PER_DOMAIN
from core.fetcher import fetch_url
from utils.stats import create_initial_stats


async def should_crawl_url(url: str, depth: int, max_depth: int, visited_urls: set,
                           allowed_domains: list[str], blacklist: list[str]) -> bool:
    """Determine if a URL should be crawled based on various criteria"""
    # Remove URL fragments to avoid duplicate crawling
    url_without_fragment = urldefrag(url)[0]
    if url_without_fragment in visited_urls:
        return False

    if depth > max_depth or url in visited_urls:
        return False

    parsed_url = urlparse(url)
    if allowed_domains and parsed_url.netloc not in allowed_domains:
        return False

    if blacklist and any(url.endswith(ext) for ext in blacklist):
        return False

    return True


async def create_task_for_url(
    url: str,
    depth: int,
    retry_client: RetryClient,
    semaphore: asyncio.Semaphore,
    stats: Dict[str, Any],
    domain_semaphores: dict,
    last_request_times: dict
) -> Tuple[asyncio.Task, str, int]:
    """Create a new task for crawling a URL"""
    task = asyncio.create_task(
        fetch_url(
            url,
            retry_client,
            semaphore,
            stats,
            stats['domain_statistics'],
            domain_semaphores,
            last_request_times
        )
    )
    return task, url, depth


async def process_url_queue(
        urls_to_visit: asyncio.Queue,
        visited_urls: set,
        max_depth: int,
        allowed_domains: list[str],
        blacklist: list[str],
        retry_client: RetryClient,
        semaphore: asyncio.Semaphore,
        stats: Dict[str, Any],
        rate_limit: int,
        domain_semaphores: dict,
        last_request_times: dict
) -> list:
    """Process URLs from the queue and create new tasks"""
    tasks = []
    while not urls_to_visit.empty() and len(tasks) < rate_limit:
        url, depth = await urls_to_visit.get()
        logging.info(f"Processing URL from queue: {url} at depth {depth}")

        if not await should_crawl_url(url, depth, max_depth, visited_urls,
                                      allowed_domains, blacklist):
            logging.info(f"Skipping URL: {url} (failed validation)")
            continue

        visited_urls.add(url)
        task_info = await create_task_for_url(
            url, depth, retry_client, semaphore, stats,
            domain_semaphores, last_request_times
        )
        tasks.append(task_info)
        logging.info(f"Created task for URL: {url}")

    return tasks


async def process_completed_task(
    done_task: asyncio.Task,
    url: str,
    depth: int,
    max_depth: int,
    visited_urls: set,
    urls_to_visit: asyncio.Queue,
    stats: Dict[str, Any]
) -> None:
    """Process a completed crawl task and update relevant statistics"""
    try:
        links, _, _ = await done_task
        stats['total_number_of_urls_crawled'] += 1
        logging.info(f"Successfully processed {url} with {len(links)} links found")

        # Add new links to queue
        if depth < max_depth:
            added_count = 0
            for link in links:
                if link not in visited_urls:
                    await urls_to_visit.put((link, depth + 1))
                    added_count += 1
            logging.info(f"Added {added_count} new URLs to queue from {url}")

    except Exception as e:
        logging.error(f"Error processing {url}: {str(e)}")
        stats['total_number_of_errors'] += 1


async def crawl(
        start_url: str,
        max_depth: int,
        allowed_domains: list[str] = None,
        blacklist: list[str] = None,
        rate_limit: int = 10,
        max_retries: int = 3
) -> Dict[str, Any]:
    """Main crawling function that orchestrates the whole process"""
    if not allowed_domains:
        start_domain = urlparse(start_url).netloc
        allowed_domains = [start_domain]

    # Initialize statistics and queues
    stats = create_initial_stats()
    visited_urls = set()
    urls_to_visit = asyncio.Queue()
    await urls_to_visit.put((start_url, 0))

    # Initialize domain tracking
    domain_semaphores = {}
    last_request_times = {}

    # Configure client with custom headers and timeout
    retry_options = ExponentialRetry(
        attempts=max_retries,
        start_timeout=1,
        max_timeout=10,
        factor=2,
        statuses={500, 502, 503, 504}
    )

    # Add custom headers and longer timeout
    timeout = ClientTimeout(total=30, connect=10)
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; PythonCrawler/1.0)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    semaphore = asyncio.Semaphore(rate_limit)

    print("\nCrawling in progress...")
    start_time = time.time()
    last_status_update = time.time()

    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            retry_client = RetryClient(client_session=session, retry_options=retry_options)
            tasks = []

            while not urls_to_visit.empty() or tasks:
                # Create new tasks if needed
                if len(tasks) < rate_limit:
                    tasks.extend(
                        await process_url_queue(
                            urls_to_visit, visited_urls, max_depth,
                            allowed_domains, blacklist, retry_client,
                            semaphore, stats, rate_limit,
                            domain_semaphores, last_request_times
                        )
                    )

                if not tasks:
                    continue

                # Wait for completed tasks
                done, _ = await asyncio.wait(
                    [task for task, _, _ in tasks],
                    return_when=asyncio.FIRST_COMPLETED
                )

                # Process completed tasks
                for done_task in done:
                    task_index = next(i for i, (t, _, _) in enumerate(tasks) if t == done_task)
                    _, url, depth = tasks.pop(task_index)

                    await process_completed_task(
                        done_task, url, depth, max_depth,
                        visited_urls, urls_to_visit, stats
                    )

                # Update progress with rate calculation
                current_time = time.time()
                if current_time - last_status_update >= 1.0:  # Update every second
                    elapsed_time = current_time - start_time
                    crawl_rate = stats['total_number_of_urls_crawled'] / elapsed_time if elapsed_time > 0 else 0
                    print(f"\rURLs crawled: {stats['total_number_of_urls_crawled']} | "
                          f"Queue size: {urls_to_visit.qsize():03d} | "
                          f"Rate: {crawl_rate:.1f} URLs/sec", end='', flush=True)
                    last_status_update = current_time

    except asyncio.CancelledError:
        logging.warning("Crawl operation was cancelled")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during crawl: {str(e)}")
        raise
    finally:
        # Cleanup resources
        for semaphore in domain_semaphores.values():
            for _ in range(MAX_CONCURRENT_PER_DOMAIN):
                try:
                    semaphore.release()
                except ValueError:
                    pass

        print("\nCrawling completed!")

        # Calculate final statistics
        end_time = time.time()
        total_time = end_time - stats['start_time']
        stats.update({
            'total_time_of_script': total_time,
            'total_number_of_domains': len(stats['domain_statistics']),
            'crawl_rate_per_second': stats['total_number_of_urls_crawled'] / total_time if total_time > 0 else 0
        })

        return stats
