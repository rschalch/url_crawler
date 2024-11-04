import asyncio
from utils.arguments import parse_arguments
from core.crawler import crawl
from utils.logging_config import setup_logging
from utils.stats import save_results
import logging

async def main():
    """Main entry point of the crawler"""
    setup_logging()

    args = parse_arguments()

    # Print configuration
    print("\n=== Crawler Configuration ===")
    print(f"Starting URL: {args.start_url}")
    print(f"Maximum depth: {args.max_depth}")
    print(f"Allowed domains: {args.domains if args.domains else 'All'}")
    print(f"Blacklisted extensions: {args.blacklist if args.blacklist else 'None'}")
    print("=" * 25)

    logging.info(f"Starting crawl from: {args.start_url}")

    stats = await crawl(
        start_url=args.start_url,
        max_depth=args.max_depth,
        allowed_domains=args.domains,
        blacklist=args.blacklist,
        rate_limit=10,  # Keep default values
        max_retries=3   # Keep default values
    )

    save_results(stats)

if __name__ == "__main__":
    asyncio.run(main())
