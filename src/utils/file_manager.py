"""File manager for storing generated content."""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger


class FileManager:
    """Manages file storage for generated blog content."""

    def __init__(self, output_dir: str = "generated_content"):
        """Initialize file manager.

        Args:
            output_dir: Directory to store generated content
        """
        self.output_dir = Path(output_dir)
        self._ensure_output_dir()

    def _ensure_output_dir(self) -> None:
        """Ensure output directory exists."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Output directory ready: {self.output_dir}")

    def generate_filename(
        self,
        repo_name: str,
        platform: str,
        timestamp_format: str = "%Y%m%d_%H%M%S",
    ) -> str:
        """Generate filename for blog post.

        Args:
            repo_name: Name of the GitHub repository
            platform: Target platform (devto, medium)
            timestamp_format: Format for timestamp

        Returns:
            Generated filename
        """
        # Clean repo name (remove owner/ prefix if present)
        clean_repo_name = repo_name.split("/")[-1].replace(" ", "_")

        # Generate timestamp
        timestamp = datetime.now().strftime(timestamp_format)

        # Create filename
        filename = f"{clean_repo_name}_{platform}_{timestamp}.md"

        return filename

    def save_content(
        self,
        content: str,
        repo_name: str,
        platform: str,
        timestamp_format: str = "%Y%m%d_%H%M%S",
    ) -> Path:
        """Save generated content to file.

        Args:
            content: Content to save
            repo_name: Name of the GitHub repository
            platform: Target platform (devto, medium)
            timestamp_format: Format for timestamp

        Returns:
            Path to saved file
        """
        filename = self.generate_filename(repo_name, platform, timestamp_format)
        filepath = self.output_dir / filename

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Content saved to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to save content to {filepath}: {e}")
            raise

    def read_content(self, filepath: str) -> str:
        """Read content from file.

        Args:
            filepath: Path to file

        Returns:
            File contents

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        path = Path(filepath)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            logger.debug(f"Read content from: {filepath}")
            return content

        except Exception as e:
            logger.error(f"Failed to read content from {filepath}: {e}")
            raise

    def list_generated_files(
        self,
        platform: Optional[str] = None,
        repo_name: Optional[str] = None,
    ) -> list[Path]:
        """List generated files with optional filtering.

        Args:
            platform: Filter by platform (devto, medium)
            repo_name: Filter by repository name

        Returns:
            List of file paths
        """
        files = []

        for filepath in self.output_dir.glob("*.md"):
            # Apply filters
            if platform and f"_{platform}_" not in filepath.name:
                continue

            if repo_name and not filepath.name.startswith(repo_name):
                continue

            files.append(filepath)

        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return files

    def get_latest_file(
        self,
        platform: Optional[str] = None,
        repo_name: Optional[str] = None,
    ) -> Optional[Path]:
        """Get the most recently generated file.

        Args:
            platform: Filter by platform
            repo_name: Filter by repository name

        Returns:
            Path to latest file or None if no files found
        """
        files = self.list_generated_files(platform=platform, repo_name=repo_name)
        return files[0] if files else None
