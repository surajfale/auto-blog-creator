"""Content formatter for different publishing platforms."""

import re
from datetime import datetime
from typing import Dict, List, Optional

import yaml
from loguru import logger


class ContentFormatter:
    """Formats blog content for different platforms."""

    def __init__(self):
        """Initialize content formatter."""
        pass

    def format_for_devto(
        self,
        content: str,
        title: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        canonical_url: Optional[str] = None,
        published: bool = False,
        series: Optional[str] = None,
        cover_image: Optional[str] = None,
    ) -> str:
        """Format content for dev.to with frontmatter.

        Args:
            content: Blog post content
            title: Post title
            description: Post description
            tags: List of tags (max 4)
            canonical_url: Canonical URL if cross-posting
            published: Whether to publish immediately
            series: Series name
            cover_image: Cover image URL

        Returns:
            Formatted content with dev.to frontmatter
        """
        # Limit tags to 4
        if tags and len(tags) > 4:
            logger.warning(f"Dev.to allows max 4 tags, truncating from {len(tags)}")
            tags = tags[:4]

        # Build frontmatter
        frontmatter = {
            "title": title,
            "published": published,
        }

        if description:
            frontmatter["description"] = description

        if tags:
            frontmatter["tags"] = tags

        if canonical_url:
            frontmatter["canonical_url"] = canonical_url

        if series:
            frontmatter["series"] = series

        if cover_image:
            frontmatter["cover_image"] = cover_image

        # Format frontmatter as YAML
        yaml_frontmatter = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)

        # Combine frontmatter and content
        formatted = f"---\n{yaml_frontmatter}---\n\n{content}"

        logger.info("Formatted content for dev.to")
        return formatted

    def format_for_medium(
        self,
        content: str,
        title: str,
        subtitle: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Format content for Medium with appropriate styling.

        Args:
            content: Blog post content
            title: Post title
            subtitle: Post subtitle
            tags: List of tags

        Returns:
            Formatted content for Medium
        """
        sections = []

        # Add title as H1
        sections.append(f"# {title}")
        sections.append("")

        # Add subtitle if provided
        if subtitle:
            sections.append(f"*{subtitle}*")
            sections.append("")

        # Add content
        # Medium prefers certain formatting
        formatted_content = self._enhance_medium_formatting(content)
        sections.append(formatted_content)

        # Add tags as footer note
        if tags:
            sections.append("")
            sections.append("---")
            sections.append("")
            sections.append(f"*Tags: {', '.join(tags)}*")

        formatted = "\n".join(sections)

        logger.info("Formatted content for Medium")
        return formatted

    def _enhance_medium_formatting(self, content: str) -> str:
        """Enhance content formatting for Medium.

        Args:
            content: Original content

        Returns:
            Enhanced content
        """
        # Medium-specific enhancements
        enhanced = content

        # Use larger headers (## becomes #)
        # Medium typically uses H1 for title, H2 for main sections
        # So we keep the structure as-is but ensure proper hierarchy

        # Add extra line breaks for better readability
        enhanced = re.sub(r"\n\n", "\n\n", enhanced)

        return enhanced

    def extract_tags_from_content(
        self,
        content: str,
        repo_metadata: Optional[Dict[str, any]] = None,
        max_tags: int = 4,
    ) -> List[str]:
        """Extract or generate tags from content and metadata.

        Args:
            content: Blog post content
            repo_metadata: Repository metadata
            max_tags: Maximum number of tags

        Returns:
            List of tags
        """
        tags = []

        # Add tags from repo topics
        if repo_metadata and repo_metadata.get("topics"):
            tags.extend(repo_metadata["topics"][:max_tags])

        # Add language as tag
        if repo_metadata and repo_metadata.get("language"):
            language = repo_metadata["language"].lower()
            if language not in tags:
                tags.append(language)

        # Add some default tags
        default_tags = ["opensource", "github", "project"]
        for tag in default_tags:
            if tag not in tags and len(tags) < max_tags:
                tags.append(tag)

        # Limit to max_tags
        tags = tags[:max_tags]

        # Clean tags (lowercase, no spaces)
        tags = [self._clean_tag(tag) for tag in tags]

        logger.debug(f"Extracted tags: {tags}")
        return tags

    def _clean_tag(self, tag: str) -> str:
        """Clean tag for platform compatibility.

        Args:
            tag: Raw tag

        Returns:
            Cleaned tag
        """
        # Convert to lowercase
        tag = tag.lower()

        # Remove special characters, replace spaces with hyphens
        tag = re.sub(r"[^a-z0-9\s-]", "", tag)
        tag = re.sub(r"\s+", "-", tag)

        # Remove multiple consecutive hyphens
        tag = re.sub(r"-+", "-", tag)

        # Strip leading/trailing hyphens
        tag = tag.strip("-")

        return tag

    def add_header_image(self, content: str, image_url: str) -> str:
        """Add header image to content.

        Args:
            content: Blog post content
            image_url: Image URL

        Returns:
            Content with header image
        """
        # Add image at the beginning
        image_markdown = f"![Header Image]({image_url})\n\n"
        return image_markdown + content

    def add_footer(
        self,
        content: str,
        repo_url: Optional[str] = None,
        author_note: Optional[str] = None,
        model_name: Optional[str] = None,
        auto_blog_repo_url: Optional[str] = None,
        include_attribution: bool = True,
    ) -> str:
        """Add footer to content with attribution.

        Args:
            content: Blog post content
            repo_url: Repository URL for the project being blogged about
            author_note: Custom author note
            model_name: Name of the AI model used for generation
            auto_blog_repo_url: URL to Auto-Blog-Creator repository
            include_attribution: Whether to include attribution section

        Returns:
            Content with footer
        """
        footer_parts = []

        footer_parts.append("---")
        footer_parts.append("")

        if repo_url:
            footer_parts.append(f"**🔗 Repository:** {repo_url}")
            footer_parts.append("")

        if author_note:
            footer_parts.append(author_note)
            footer_parts.append("")

        # Attribution section (if enabled)
        if include_attribution:
            footer_parts.append("## 🤖 About This Post")
            footer_parts.append("")

            if auto_blog_repo_url:
                footer_parts.append(f"This blog post was automatically generated using [**Auto-Blog-Creator**]({auto_blog_repo_url}), an AI-powered tool that transforms GitHub repositories into engaging blog content.")
            else:
                footer_parts.append("This blog post was automatically generated using **Auto-Blog-Creator**, an AI-powered tool that transforms GitHub repositories into engaging blog content.")

            footer_parts.append("")

            if model_name:
                footer_parts.append(f"**🧠 AI Model:** `{model_name}` via [Ollama Cloud](https://ollama.com)")
            else:
                footer_parts.append("**🧠 AI Model:** Powered by [Ollama Cloud](https://ollama.com)")

            footer_parts.append("")
            footer_parts.append("**✨ Key Features:**")
            footer_parts.append("- Automated blog generation from GitHub repos")
            footer_parts.append("- AI-powered content creation with advanced prompt engineering")
            footer_parts.append("- Multi-platform support (dev.to, Medium)")
            footer_parts.append("- Smart content parsing and formatting")
            footer_parts.append("")
            footer_parts.append("*Interested in automated blog generation? Star and contribute to Auto-Blog-Creator!*")

        footer = "\n".join(footer_parts)
        return f"{content}\n\n{footer}"

    def remove_title_if_present(self, content: str) -> tuple[str, Optional[str]]:
        """Remove title from content if it's the first line.

        Args:
            content: Blog post content

        Returns:
            Tuple of (content without title, extracted title or None)
        """
        lines = content.split("\n")

        if not lines:
            return content, None

        # Check if first line is a title (# Title)
        first_line = lines[0].strip()
        if first_line.startswith("# "):
            title = first_line[2:].strip()
            # Remove first line and any following empty lines
            remaining_lines = lines[1:]
            while remaining_lines and not remaining_lines[0].strip():
                remaining_lines.pop(0)

            content_without_title = "\n".join(remaining_lines)
            logger.debug(f"Extracted title from content: {title}")
            return content_without_title, title

        return content, None
