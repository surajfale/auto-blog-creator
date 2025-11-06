"""Dev.to publisher for blog posts."""

import time
from typing import Dict, Optional

import requests
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential


class DevToPublisher:
    """Publishes blog posts to dev.to."""

    def __init__(self, api_key: str, base_url: str = "https://dev.to/api"):
        """Initialize dev.to publisher.

        Args:
            api_key: Dev.to API key
            base_url: Dev.to API base URL
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "api-key": self.api_key,
                "Content-Type": "application/json",
            }
        )

        logger.info("Initialized dev.to publisher")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def create_article(
        self,
        title: str,
        body_markdown: str,
        published: bool = False,
        tags: Optional[list[str]] = None,
        series: Optional[str] = None,
        canonical_url: Optional[str] = None,
        description: Optional[str] = None,
        cover_image: Optional[str] = None,
    ) -> Dict:
        """Create a new article on dev.to.

        Args:
            title: Article title
            body_markdown: Article content in markdown
            published: Whether to publish immediately (default: False for draft)
            tags: List of tags (max 4)
            series: Series name
            canonical_url: Canonical URL for cross-posting
            description: Article description
            cover_image: Cover image URL

        Returns:
            Response data from dev.to API

        Raises:
            requests.RequestException: If API request fails
        """
        # Limit tags to 4
        if tags and len(tags) > 4:
            logger.warning(f"Dev.to allows max 4 tags, using first 4")
            tags = tags[:4]

        # Build article data
        article_data = {
            "article": {
                "title": title,
                "published": published,
                "body_markdown": body_markdown,
            }
        }

        if tags:
            article_data["article"]["tags"] = tags

        if series:
            article_data["article"]["series"] = series

        if canonical_url:
            article_data["article"]["canonical_url"] = canonical_url

        if description:
            article_data["article"]["description"] = description

        if cover_image:
            article_data["article"]["cover_image"] = cover_image

        # Make API request
        url = f"{self.base_url}/articles"

        logger.info(f"Creating article on dev.to: {title}")
        logger.debug(f"Published: {published}, Tags: {tags}")

        try:
            response = self.session.post(url, json=article_data, timeout=30)
            response.raise_for_status()

            result = response.json()

            # Log result
            article_url = result.get("url", "N/A")
            article_id = result.get("id", "N/A")

            logger.info(f"Article created successfully!")
            logger.info(f"  ID: {article_id}")
            logger.info(f"  URL: {article_url}")
            logger.info(f"  Status: {'Published' if published else 'Draft'}")

            return result

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error creating article: {e}")
            logger.error(f"Response: {e.response.text if e.response else 'N/A'}")
            raise

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error creating article: {e}")
            raise

    def create_article_from_file(
        self,
        filepath: str,
        published: bool = False,
    ) -> Dict:
        """Create article from a markdown file with frontmatter.

        Args:
            filepath: Path to markdown file
            published: Override published status from frontmatter

        Returns:
            Response data from dev.to API
        """
        import frontmatter

        logger.info(f"Reading article from file: {filepath}")

        try:
            # Parse file with frontmatter
            with open(filepath, "r", encoding="utf-8") as f:
                post = frontmatter.load(f)

            # Extract metadata
            title = post.get("title", "Untitled")
            body_markdown = post.content
            tags = post.get("tags", [])
            series = post.get("series")
            canonical_url = post.get("canonical_url")
            description = post.get("description")
            cover_image = post.get("cover_image")

            # Use frontmatter published status if not overridden
            if "published" in post.metadata and not published:
                published = post.get("published", False)

            # Create article
            return self.create_article(
                title=title,
                body_markdown=body_markdown,
                published=published,
                tags=tags,
                series=series,
                canonical_url=canonical_url,
                description=description,
                cover_image=cover_image,
            )

        except Exception as e:
            logger.error(f"Failed to create article from file: {e}")
            raise

    def get_my_articles(
        self,
        page: int = 1,
        per_page: int = 30,
    ) -> list[Dict]:
        """Get user's published articles.

        Args:
            page: Page number
            per_page: Articles per page

        Returns:
            List of articles
        """
        url = f"{self.base_url}/articles/me"
        params = {"page": page, "per_page": per_page}

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            articles = response.json()
            logger.info(f"Retrieved {len(articles)} articles")

            return articles

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get articles: {e}")
            raise

    def get_article(self, article_id: int) -> Dict:
        """Get a specific article by ID.

        Args:
            article_id: Article ID

        Returns:
            Article data
        """
        url = f"{self.base_url}/articles/{article_id}"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            article = response.json()
            logger.info(f"Retrieved article: {article.get('title', 'N/A')}")

            return article

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get article {article_id}: {e}")
            raise

    def update_article(
        self,
        article_id: int,
        title: Optional[str] = None,
        body_markdown: Optional[str] = None,
        published: Optional[bool] = None,
        tags: Optional[list[str]] = None,
    ) -> Dict:
        """Update an existing article.

        Args:
            article_id: Article ID
            title: New title
            body_markdown: New content
            published: New published status
            tags: New tags

        Returns:
            Updated article data
        """
        url = f"{self.base_url}/articles/{article_id}"

        article_data = {"article": {}}

        if title is not None:
            article_data["article"]["title"] = title

        if body_markdown is not None:
            article_data["article"]["body_markdown"] = body_markdown

        if published is not None:
            article_data["article"]["published"] = published

        if tags is not None:
            if len(tags) > 4:
                logger.warning("Dev.to allows max 4 tags, using first 4")
                tags = tags[:4]
            article_data["article"]["tags"] = tags

        try:
            response = self.session.put(url, json=article_data, timeout=30)
            response.raise_for_status()

            result = response.json()
            logger.info(f"Article {article_id} updated successfully")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update article {article_id}: {e}")
            raise

    def respect_rate_limit(self, delay: int = 3) -> None:
        """Respect dev.to rate limits with a delay.

        Args:
            delay: Delay in seconds (default: 3)
        """
        logger.debug(f"Rate limit delay: {delay} seconds")
        time.sleep(delay)
