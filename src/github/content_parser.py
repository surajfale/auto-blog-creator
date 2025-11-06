"""Content parser for extracting and combining markdown content."""

from typing import Dict, List

import frontmatter
from loguru import logger


class ContentParser:
    """Parses and combines markdown content for blog generation."""

    def __init__(self, priority_files: Optional[List[str]] = None):
        """Initialize content parser.

        Args:
            priority_files: List of priority filenames (e.g., README.md)
        """
        self.priority_files = priority_files or [
            "README.md",
            "README.MD",
            "readme.md",
        ]

    def parse_markdown_file(self, content: str) -> Dict[str, any]:
        """Parse markdown file with optional frontmatter.

        Args:
            content: Markdown file content

        Returns:
            Dictionary with 'frontmatter' and 'content' keys
        """
        try:
            # Try to parse frontmatter
            post = frontmatter.loads(content)

            return {
                "frontmatter": dict(post.metadata),
                "content": post.content,
            }

        except Exception as e:
            logger.debug(f"No frontmatter found or parsing error: {e}")
            return {
                "frontmatter": {},
                "content": content,
            }

    def extract_project_info(
        self,
        markdown_files: List[Dict[str, str]],
        repo_metadata: Dict[str, any],
    ) -> str:
        """Extract and combine project information for blog generation.

        Args:
            markdown_files: List of markdown files from GitHub scanner
            repo_metadata: Repository metadata

        Returns:
            Combined project information as text
        """
        sections = []

        # Add repository overview
        sections.append("# Repository Overview")
        sections.append(f"**Name:** {repo_metadata['full_name']}")
        sections.append(f"**Description:** {repo_metadata['description']}")
        sections.append(f"**URL:** {repo_metadata['url']}")

        if repo_metadata["homepage"]:
            sections.append(f"**Homepage:** {repo_metadata['homepage']}")

        if repo_metadata["language"]:
            sections.append(f"**Primary Language:** {repo_metadata['language']}")

        sections.append(
            f"**Stats:** {repo_metadata['stars']} stars, {repo_metadata['forks']} forks"
        )

        if repo_metadata["topics"]:
            sections.append(f"**Topics:** {', '.join(repo_metadata['topics'])}")

        if repo_metadata["license"]:
            sections.append(f"**License:** {repo_metadata['license']}")

        sections.append("")  # Empty line

        # Sort files by priority
        sorted_files = self._sort_by_priority(markdown_files)

        # Add content from markdown files
        for file_info in sorted_files:
            parsed = self.parse_markdown_file(file_info["content"])

            sections.append(f"## Content from: {file_info['path']}")
            sections.append("")

            # Add frontmatter if present
            if parsed["frontmatter"]:
                sections.append("**Frontmatter:**")
                for key, value in parsed["frontmatter"].items():
                    sections.append(f"- {key}: {value}")
                sections.append("")

            # Add content (limit to reasonable size)
            content = parsed["content"].strip()
            max_length = 5000  # Limit per file to avoid overwhelming the LLM

            if len(content) > max_length:
                content = content[:max_length] + "\n\n[... content truncated ...]"

            sections.append(content)
            sections.append("")
            sections.append("---")
            sections.append("")

        combined = "\n".join(sections)
        logger.info(
            f"Extracted project info: {len(combined)} characters from {len(markdown_files)} files"
        )

        return combined

    def _sort_by_priority(
        self, markdown_files: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Sort files by priority (README first, etc.).

        Args:
            markdown_files: List of markdown file dictionaries

        Returns:
            Sorted list of markdown files
        """
        priority_map = {name.lower(): i for i, name in enumerate(self.priority_files)}

        def get_priority(file_info: Dict[str, str]) -> tuple:
            """Get priority for sorting (lower is higher priority)."""
            name_lower = file_info["name"].lower()

            # Check if in priority list
            if name_lower in priority_map:
                return (0, priority_map[name_lower])

            # README files always get priority even if not in exact list
            if "readme" in name_lower:
                return (1, 0)

            # Other files sorted by path depth (shallow first)
            depth = file_info["path"].count("/")
            return (2, depth, file_info["path"])

        sorted_files = sorted(markdown_files, key=get_priority)

        logger.debug(
            f"Sorted {len(sorted_files)} files, priority file: {sorted_files[0]['name'] if sorted_files else 'none'}"
        )

        return sorted_files

    def extract_code_blocks(self, content: str) -> List[str]:
        """Extract code blocks from markdown content.

        Args:
            content: Markdown content

        Returns:
            List of code blocks
        """
        import re

        pattern = r"```[\w]*\n(.*?)```"
        code_blocks = re.findall(pattern, content, re.DOTALL)

        logger.debug(f"Found {len(code_blocks)} code blocks")
        return code_blocks

    def extract_links(self, content: str) -> List[Dict[str, str]]:
        """Extract links from markdown content.

        Args:
            content: Markdown content

        Returns:
            List of dictionaries with 'text' and 'url' keys
        """
        import re

        # Match markdown links [text](url)
        pattern = r"\[([^\]]+)\]\(([^\)]+)\)"
        matches = re.findall(pattern, content)

        links = [{"text": text, "url": url} for text, url in matches]

        logger.debug(f"Found {len(links)} links")
        return links


# Fix import
from typing import Optional
