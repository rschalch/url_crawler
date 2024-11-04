from typing import Dict, Any
import time
import json
from datetime import datetime
from constants import HTTP_STATUS_CODES  # Make sure to use relative import

def create_domain_stats() -> Dict[str, Any]:
    return {
        'total_time_to_crawl': 0,
        'total_number_of_crawled_urls': 0,
        'total_number_of_errors': 0,
        'status_code_statistics': {}
    }

def create_initial_stats() -> Dict[str, Any]:
    return {
        'start_time': time.time(),
        'total_time_of_script': 0,
        'total_number_of_urls_crawled': 0,
        'total_number_of_errors': 0,
        'total_number_of_domains': 0,
        'status_code_statistics': {},
        'domain_statistics': {}
    }

def save_results(stats: Dict[str, Any], filename: str = None):
    """
    Save crawling results to a JSON file and print human-readable summary
    """
    if filename is None:
        filename = f"crawler_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # Create a copy of stats to modify
    output_stats = stats.copy()

    # Remove start_time
    if 'start_time' in output_stats:
        del output_stats['start_time']

    # Clean up timing fields before saving
    for domain_stats in output_stats['domain_statistics'].values():
        if 'first_request_time' in domain_stats:
            del domain_stats['first_request_time']
        if 'last_request_time' in domain_stats:
            del domain_stats['last_request_time']

    # Round all floating point numbers to 2 decimals
    def round_floats(obj):
        if isinstance(obj, float):
            return round(obj, 2)
        elif isinstance(obj, dict):
            return {k: round_floats(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [round_floats(x) for x in obj]
        return obj

    output_stats = round_floats(output_stats)

    # Save to JSON file
    with open(filename, 'w') as f:
        json.dump(output_stats, f, indent=4)

    # Print human-readable summary
    print("\n=== Crawling Summary ===")
    print(f"Total execution time: {output_stats['total_time_of_script']:.2f} seconds")
    print(f"Total URLs crawled: {output_stats['total_number_of_urls_crawled']}")
    print(f"Total errors: {output_stats['total_number_of_errors']}")
    print(f"Total domains: {output_stats['total_number_of_domains']}")

    print("\nStatus Code Distribution:")
    for status, count in sorted(output_stats['status_code_statistics'].items()):
        status_name = HTTP_STATUS_CODES.get(int(status), "Unknown")
        print(f"  {status} ({status_name}): {count}")

    print("\nPer-Domain Statistics:")
    for domain, domain_stats in sorted(output_stats['domain_statistics'].items()):
        print(f"\n{domain}:")
        print(f"  Time to crawl: {domain_stats['total_time_to_crawl']:.2f} seconds")
        print(f"  URLs crawled: {domain_stats['total_number_of_crawled_urls']}")
        print(f"  Errors encountered: {domain_stats['total_number_of_errors']}")

        if domain_stats['status_code_statistics']:
            print("  Status Code Distribution:")
            for status, count in sorted(domain_stats['status_code_statistics'].items()):
                status_name = HTTP_STATUS_CODES.get(int(status), "Unknown")
                print(f"    {status} ({status_name}): {count}")

    print(f"\nDetailed results saved to: {filename}")
