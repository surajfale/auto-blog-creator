"""GitHub repository scanner for markdown files."""

import re
from typing import Dict, List, Optional

from github import Github, GithubException, Repository
from loguru import logger


class GitHubScanner:
    """Scans GitHub repositories for markdown files."""

    def __init__(self, github_token: Optional[str] = None):
        """Initialize GitHub scanner.

        Args:
            github_token: GitHub personal access token (optional but recommended)
        """
        self.github = Github(github_token) if github_token else Github()
        self._check_rate_limit()

    def _check_rate_limit(self) -> None:
        """Check and log GitHub API rate limit."""
        try:
            rate_limit = self.github.get_rate_limit()
            core_remaining = rate_limit.core.remaining
            logger.info(f"GitHub API rate limit: {core_remaining} requests remaining")

            if core_remaining < 100:
                logger.warning(f"Low GitHub API rate limit: {core_remaining} remaining")

        except Exception as e:
            logger.warning(f"Could not check rate limit: {e}")

    def parse_repo_url(self, repo_url: str) -> str:
        """Parse GitHub repository URL to extract owner/repo format.

        Args:
            repo_url: GitHub repository URL

        Returns:
            Repository identifier in 'owner/repo' format

        Raises:
            ValueError: If URL is invalid
        """
        # Handle various URL formats
        patterns = [
            r"github\.com/([^/]+)/([^/]+?)(?:\.git)?$",  # https://github.com/owner/repo
            r"github\.com/([^/]+)/([^/]+)/",  # https://github.com/owner/repo/...
            r"^([^/]+)/([^/]+)$",  # owner/repo
        ]

        for pattern in patterns:
            match = re.search(pattern, repo_url.strip())
            if match:
                owner, repo = match.groups()
                # Remove .git suffix if present
                repo = repo.replace(".git", "")
                return f"{owner}/{repo}"

        raise ValueError(f"Invalid GitHub repository URL: {repo_url}")

    def get_repository(self, repo_identifier: str) -> Repository.Repository:
        """Get GitHub repository object.

        Args:
            repo_identifier: Repository in 'owner/repo' format or URL

        Returns:
            GitHub repository object

        Raises:
            GithubException: If repository not found or inaccessible
        """
        # Parse URL if needed
        if "github.com" in repo_identifier or "/" in repo_identifier:
            repo_identifier = self.parse_repo_url(repo_identifier)

        try:
            repo = self.github.get_repo(repo_identifier)
            logger.info(f"Found repository: {repo.full_name}")
            return repo

        except GithubException as e:
            logger.error(f"Failed to get repository {repo_identifier}: {e}")
            raise

    def scan_markdown_files(
        self,
        repo: Repository.Repository,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_file_size: int = 1048576,  # 1MB
    ) -> List[Dict[str, str]]:
        """Scan repository for markdown files.

        Args:
            repo: GitHub repository object
            include_patterns: File patterns to include
            exclude_patterns: File patterns to exclude
            max_file_size: Maximum file size to read (bytes)

        Returns:
            List of dictionaries containing file information
        """
        if include_patterns is None:
            include_patterns = ["*.md"]

        if exclude_patterns is None:
            exclude_patterns = [
                "node_modules/*",
                ".git/*",
                "vendor/*",
                "build/*",
                "dist/*",
            ]

        markdown_files = []

        try:
            # Get all contents recursively
            contents = repo.get_contents("")

            while contents:
                file_content = contents.pop(0)

                # Skip excluded paths
                if any(self._matches_pattern(file_content.path, pattern) for pattern in exclude_patterns):
                    logger.debug(f"Skipping excluded file: {file_content.path}")
                    continue

                # If directory, add its contents
                if file_content.type == "dir":
                    try:
                        contents.extend(repo.get_contents(file_content.path))
                    except GithubException as e:
                        logger.warning(f"Could not access directory {file_content.path}: {e}")
                    continue

                # Check if file matches include patterns
                if not any(self._matches_pattern(file_content.path, pattern) for pattern in include_patterns):
                    continue

                # Check file size
                if file_content.size > max_file_size:
                    logger.warning(
                        f"Skipping large file {file_content.path} ({file_content.size} bytes)"
                    )
                    continue

                # Decode and store file content
                try:
                    content = file_content.decoded_content.decode("utf-8")
                    markdown_files.append(
                        {
                            "path": file_content.path,
                            "name": file_content.name,
                            "content": content,
                            "size": file_content.size,
                            "url": file_content.html_url,
                        }
                    )
                    logger.debug(f"Found markdown file: {file_content.path}")

                except Exception as e:
                    logger.warning(f"Could not read file {file_content.path}: {e}")

            logger.info(f"Found {len(markdown_files)} markdown files")
            return markdown_files

        except GithubException as e:
            logger.error(f"Error scanning repository: {e}")
            raise

    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches glob-like pattern.

        Args:
            path: File path
            pattern: Glob pattern

        Returns:
            True if path matches pattern
        """
        # Simple glob matching
        pattern_regex = pattern.replace("*", ".*").replace("?", ".")
        return re.match(pattern_regex, path) is not None

    def get_repo_metadata(self, repo: Repository.Repository) -> Dict[str, any]:
        """Get repository metadata.

        Args:
            repo: GitHub repository object

        Returns:
            Dictionary containing repository metadata
        """
        metadata = {
            "name": repo.name,
            "full_name": repo.full_name,
            "description": repo.description or "",
            "url": repo.html_url,
            "homepage": repo.homepage or "",
            "language": repo.language or "",
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "open_issues": repo.open_issues_count,
            "topics": repo.get_topics(),
            "license": repo.license.name if repo.license else "",
            "created_at": repo.created_at.isoformat(),
            "updated_at": repo.updated_at.isoformat(),
        }

        logger.debug(f"Repository metadata: {repo.full_name}")
        return metadata
