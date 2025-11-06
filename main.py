#!/usr/bin/env python3
"""Auto-Blog-Creator: Main CLI application."""

import sys
from pathlib import Path

import typer
from loguru import logger
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.content.formatter import ContentFormatter
from src.content.generator import ContentGenerator
from src.github.content_parser import ContentParser
from src.github.scanner import GitHubScanner
from src.publishers.devto import DevToPublisher
from src.utils.config import Config
from src.utils.file_manager import FileManager

app = typer.Typer(help="Auto-Blog-Creator: Generate and publish blog posts from GitHub repos")
console = Console()


@app.command()
def generate(
    repo_url: str = typer.Argument(..., help="GitHub repository URL or owner/repo"),
    platforms: str = typer.Option(
        "devto,medium",
        "--platforms",
        "-p",
        help="Platforms to generate for (comma-separated: devto,medium)",
    ),
    output_dir: str = typer.Option(
        "generated_content",
        "--output",
        "-o",
        help="Output directory for generated files",
    ),
):
    """Generate blog posts from a GitHub repository."""
    console.print(f"\n[bold blue]🚀 Auto-Blog-Creator[/bold blue]\n")

    # Initialize config
    config = Config()

    # Validate configuration
    if not config.validate():
        console.print("[red]❌ Configuration validation failed. Check your .env file.[/red]")
        raise typer.Exit(1)

    # Parse platforms
    platform_list = [p.strip().lower() for p in platforms.split(",")]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:

        # Step 1: Scan GitHub repository
        task1 = progress.add_task("Scanning GitHub repository...", total=None)

        try:
            scanner = GitHubScanner(github_token=config.github_token)
            repo_identifier = scanner.parse_repo_url(repo_url)
            repo = scanner.get_repository(repo_identifier)

            markdown_files = scanner.scan_markdown_files(
                repo=repo,
                include_patterns=config.get("github.include_patterns"),
                exclude_patterns=config.get("github.exclude_patterns"),
                max_file_size=config.get("github.max_file_size", 1048576),
            )

            repo_metadata = scanner.get_repo_metadata(repo)

            progress.update(task1, completed=True)
            console.print(f"[green]✓[/green] Found {len(markdown_files)} markdown files")

        except Exception as e:
            progress.update(task1, completed=True)
            console.print(f"[red]❌ Failed to scan repository: {e}[/red]")
            raise typer.Exit(1)

        # Step 2: Parse content
        task2 = progress.add_task("Parsing content...", total=None)

        try:
            parser = ContentParser(
                priority_files=config.get("github.priority_files")
            )
            project_info = parser.extract_project_info(markdown_files, repo_metadata)

            progress.update(task2, completed=True)
            console.print(f"[green]✓[/green] Extracted project information")

        except Exception as e:
            progress.update(task2, completed=True)
            console.print(f"[red]❌ Failed to parse content: {e}[/red]")
            raise typer.Exit(1)

        # Step 3: Generate content
        task3 = progress.add_task("Generating blog post with AI...", total=None)

        try:
            generator = ContentGenerator(
                api_key=config.ollama_api_key,
                model=config.ollama_model,
            )

            # Generate title
            title = generator.generate_title(project_info)

            # Generate content
            content = generator.generate_blog_post(
                project_info=project_info,
                tone=config.get("content.tone", "professional but witty"),
                target_length=config.get("content.target_length", 1500),
            )

            # Generate description
            description = generator.generate_description(content)

            progress.update(task3, completed=True)
            console.print(f"[green]✓[/green] Generated blog post: {title}")

        except Exception as e:
            progress.update(task3, completed=True)
            console.print(f"[red]❌ Failed to generate content: {e}[/red]")
            raise typer.Exit(1)

        # Step 4: Format and save content
        task4 = progress.add_task("Formatting and saving content...", total=None)

        try:
            formatter = ContentFormatter()
            file_manager = FileManager(output_dir=output_dir)

            # Extract tags
            tags = formatter.extract_tags_from_content(
                content=content,
                repo_metadata=repo_metadata,
                max_tags=4,
            )

            saved_files = []

            # Generate for each platform
            for platform in platform_list:
                if platform == "devto":
                    formatted = formatter.format_for_devto(
                        content=content,
                        title=title,
                        description=description,
                        tags=tags,
                        canonical_url=repo_metadata["url"],
                        published=False,
                    )

                elif platform == "medium":
                    formatted = formatter.format_for_medium(
                        content=content,
                        title=title,
                        subtitle=description,
                        tags=tags,
                    )

                else:
                    logger.warning(f"Unknown platform: {platform}, skipping")
                    continue

                # Add footer with attribution
                formatted = formatter.add_footer(
                    content=formatted,
                    repo_url=repo_metadata["url"],
                    model_name=config.ollama_model,
                    auto_blog_repo_url=config.get("attribution.repo_url"),
                    include_attribution=config.get("attribution.enabled", True),
                )

                # Save to file
                filepath = file_manager.save_content(
                    content=formatted,
                    repo_name=repo_metadata["name"],
                    platform=platform,
                    timestamp_format=config.get("output.timestamp_format", "%Y%m%d_%H%M%S"),
                )

                saved_files.append((platform, filepath))

            progress.update(task4, completed=True)
            console.print(f"[green]✓[/green] Saved content for {len(saved_files)} platforms")

        except Exception as e:
            progress.update(task4, completed=True)
            console.print(f"[red]❌ Failed to format/save content: {e}[/red]")
            raise typer.Exit(1)

    # Display results
    console.print("\n[bold green]✨ Generation complete![/bold green]\n")
    console.print("[bold]Generated files:[/bold]")
    for platform, filepath in saved_files:
        console.print(f"  • {platform.upper()}: [cyan]{filepath}[/cyan]")

    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Review the generated files")
    console.print(f"  2. For dev.to: python publish_to_devto.py <file> [--publish]")
    console.print("  3. For Medium: Copy and paste the content manually\n")


@app.command()
def publish(
    file: str = typer.Argument(..., help="Path to generated markdown file"),
    platform: str = typer.Option("devto", "--platform", "-p", help="Platform to publish to"),
    publish_now: bool = typer.Option(False, "--publish", help="Publish immediately (default: draft)"),
):
    """Publish a generated blog post to a platform."""
    console.print(f"\n[bold blue]📤 Publishing to {platform}[/bold blue]\n")

    # Check if file exists
    filepath = Path(file)
    if not filepath.exists():
        console.print(f"[red]❌ File not found: {file}[/red]")
        raise typer.Exit(1)

    # Initialize config
    config = Config()

    if platform.lower() == "devto":
        if not config.devto_api_key:
            console.print("[red]❌ DEVTO_API_KEY not found in environment[/red]")
            raise typer.Exit(1)

        try:
            publisher = DevToPublisher(api_key=config.devto_api_key)

            console.print(f"Publishing: [cyan]{filepath.name}[/cyan]")
            console.print(f"Mode: [yellow]{'Publish' if publish_now else 'Draft'}[/yellow]\n")

            result = publisher.create_article_from_file(
                filepath=str(filepath),
                published=publish_now,
            )

            console.print("[bold green]✅ Published successfully![/bold green]")
            console.print(f"Title: {result.get('title', 'N/A')}")
            console.print(f"URL: [link]{result.get('url', 'N/A')}[/link]")
            console.print(f"Status: {('Published' if result.get('published') else 'Draft')}\n")

        except Exception as e:
            console.print(f"[red]❌ Failed to publish: {e}[/red]")
            raise typer.Exit(1)

    else:
        console.print(f"[red]❌ Unsupported platform: {platform}[/red]")
        console.print("Supported platforms: devto")
        raise typer.Exit(1)


@app.command()
def list_files(
    platform: str = typer.Option(None, "--platform", "-p", help="Filter by platform"),
    repo: str = typer.Option(None, "--repo", "-r", help="Filter by repository name"),
):
    """List generated blog post files."""
    config = Config()
    file_manager = FileManager(output_dir=config.get("output.directory", "generated_content"))

    files = file_manager.list_generated_files(platform=platform, repo_name=repo)

    if not files:
        console.print("[yellow]No generated files found[/yellow]")
        return

    console.print(f"\n[bold]Generated files ({len(files)}):[/bold]\n")

    for filepath in files:
        # Parse filename
        parts = filepath.stem.split("_")
        if len(parts) >= 3:
            repo_name = "_".join(parts[:-2])
            platform_name = parts[-2]
            timestamp = parts[-1]

            console.print(f"  • [cyan]{filepath.name}[/cyan]")
            console.print(f"    Repo: {repo_name} | Platform: {platform_name} | Time: {timestamp}")
        else:
            console.print(f"  • [cyan]{filepath.name}[/cyan]")

    console.print()


@app.command()
def config_check():
    """Check configuration and validate API keys."""
    console.print("\n[bold blue]🔍 Configuration Check[/bold blue]\n")

    config = Config()

    checks = [
        ("Ollama API Key", bool(config.ollama_api_key)),
        ("Ollama Model", bool(config.ollama_model)),
        ("Dev.to API Key", bool(config.devto_api_key)),
        ("GitHub Token", bool(config.github_token)),
        ("Config File", config.config_path.exists()),
    ]

    for name, status in checks:
        icon = "[green]✓[/green]" if status else "[red]✗[/red]"
        console.print(f"{icon} {name}")

    console.print()

    if all(status for _, status in checks[:2]):  # Check required keys
        console.print("[green]✅ Configuration is valid![/green]")
    else:
        console.print("[red]❌ Configuration is incomplete. Check your .env file.[/red]")


if __name__ == "__main__":
    app()
