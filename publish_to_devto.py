#!/usr/bin/env python3
"""Standalone script to publish generated blog posts to dev.to."""

import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.publishers.devto import DevToPublisher
from src.utils.config import Config


def main():
    """Main function to publish to dev.to."""
    # Load environment variables
    load_dotenv()

    # Initialize config
    config = Config()

    # Check if API key is present
    if not config.devto_api_key:
        logger.error("DEVTO_API_KEY not found in environment variables")
        logger.error("Please set DEVTO_API_KEY in your .env file")
        sys.exit(1)

    # Get file path from command line
    if len(sys.argv) < 2:
        logger.error("Usage: python publish_to_devto.py <markdown_file> [--publish]")
        logger.error("  <markdown_file>: Path to the generated markdown file")
        logger.error("  --publish: Publish immediately (default: save as draft)")
        sys.exit(1)

    filepath = sys.argv[1]
    publish_immediately = "--publish" in sys.argv

    # Check if file exists
    if not Path(filepath).exists():
        logger.error(f"File not found: {filepath}")
        sys.exit(1)

    # Initialize publisher
    publisher = DevToPublisher(
        api_key=config.devto_api_key,
        base_url=config.get("api.devto.base_url", "https://dev.to/api"),
    )

    try:
        # Publish article
        logger.info(f"Publishing article from: {filepath}")
        logger.info(f"Mode: {'Publish' if publish_immediately else 'Draft'}")

        result = publisher.create_article_from_file(
            filepath=filepath,
            published=publish_immediately,
        )

        # Display results
        print("\n" + "=" * 60)
        print("✅ Article published successfully!")
        print("=" * 60)
        print(f"Title: {result.get('title', 'N/A')}")
        print(f"URL: {result.get('url', 'N/A')}")
        print(f"Status: {'Published' if result.get('published') else 'Draft'}")
        print(f"ID: {result.get('id', 'N/A')}")
        print("=" * 60)

        # Respect rate limit
        publisher.respect_rate_limit()

    except Exception as e:
        logger.error(f"Failed to publish article: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
