import argparse


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments for the web crawler.

    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Web crawler with depth control and domain restrictions'
    )

    # Required arguments
    parser.add_argument(
        'start_url',
        type=str,
        help='The starting URL to begin crawling from'
    )

    parser.add_argument(
        '--max-depth',
        type=int,
        required=True,
        help='Maximum depth of links to crawl'
    )

    # Optional arguments
    parser.add_argument(
        '--domains',
        type=str,
        nargs='*',
        help='List of allowed domains to crawl (if none specified, crawls all domains)'
    )

    parser.add_argument(
        '--blacklist',
        type=str,
        nargs='*',
        help='File extensions to ignore (e.g., jpg css png)'
    )

    args = parser.parse_args()

    # Validate the starting URL
    if not args.start_url.startswith(('http://', 'https://')):
        parser.error('Starting URL must begin with http:// or https://')

    # Process blacklist only if provided
    if args.blacklist:
        args.blacklist = [f".{ext.lower().strip('.')}" for ext in args.blacklist]

    # Process domains only if provided
    if args.domains:
        args.domains = [domain.strip().lower() for domain in args.domains]

    return args
