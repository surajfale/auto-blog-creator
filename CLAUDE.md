# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Auto-Blog-Creator is a Python application that automatically generates and publishes blog posts from GitHub repositories. It scans repository documentation, uses AI to generate engaging content, and publishes to dev.to (with optional Medium export).

**Key Features:**
- Scans GitHub repositories for markdown files
- Extracts project information intelligently
- Generates blog content using Ollama AI (gpt-oss:120b-cloud)
- Formats content for dev.to and Medium
- Auto-publishes to dev.to via API
- Stores generated content locally (not committed)

## Development Setup

### Prerequisites
- Python 3.8+
- Ollama cloud API access
- Dev.to account with API key
- GitHub personal access token (optional but recommended)

### Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
```

### Required Environment Variables

Edit `.env` file with:
- `OLLAMA_API_KEY` - Get from https://ollama.com/settings/keys
- `DEVTO_API_KEY` - Generate at https://dev.to/settings/extensions
- `GITHUB_TOKEN` - Optional, from https://github.com/settings/tokens
- `OLLAMA_MODEL` - Default: gpt-oss:120b-cloud

## Commands

### Main CLI Application

```bash
# Generate blog posts from a GitHub repo
python main.py generate <github-repo-url>

# Generate for specific platforms
python main.py generate <repo-url> --platforms devto,medium

# Check configuration
python main.py config-check

# List generated files
python main.py list-files
python main.py list-files --platform devto
python main.py list-files --repo <repo-name>

# Publish to dev.to
python main.py publish <file-path> --platform devto
python main.py publish <file-path> --platform devto --publish  # Publish immediately
```

### Standalone Publishing Script

```bash
# Publish as draft
python publish_to_devto.py generated_content/myrepo_devto_20250106_120000.md

# Publish immediately
python publish_to_devto.py generated_content/myrepo_devto_20250106_120000.md --publish
```

### Development Commands

```bash
# Run with verbose logging
# (Edit config/config.yaml and set logging.level to DEBUG)

# Install in development mode
pip install -e .
```

## Architecture

### Directory Structure

```
auto-blog-creator/
├── src/                          # Main source code
│   ├── github/                   # GitHub integration
│   │   ├── scanner.py           # Repository scanning with PyGithub
│   │   └── content_parser.py    # Markdown parsing and content extraction
│   ├── content/                  # Content generation
│   │   ├── generator.py         # Ollama AI integration
│   │   └── formatter.py         # Platform-specific formatting
│   ├── publishers/               # Platform publishers
│   │   └── devto.py            # Dev.to API integration
│   └── utils/                    # Utilities
│       ├── config.py            # Configuration management
│       └── file_manager.py      # Local file storage
├── config/
│   └── config.yaml              # Application configuration
├── generated_content/            # Output directory (gitignored)
├── main.py                       # Main CLI application
└── publish_to_devto.py          # Standalone publisher
```

### Data Flow

1. **GitHub Scanner** ([src/github/scanner.py](src/github/scanner.py))
   - Accepts GitHub repo URL
   - Uses PyGithub to scan for `*.md` files
   - Respects include/exclude patterns from config
   - Returns list of markdown files with content

2. **Content Parser** ([src/github/content_parser.py](src/github/content_parser.py))
   - Prioritizes README files
   - Parses frontmatter if present
   - Combines repo metadata with markdown content
   - Returns comprehensive project information

3. **Content Generator** ([src/content/generator.py](src/content/generator.py))
   - Connects to Ollama cloud API
   - Sends project info with tone/style instructions
   - Uses gpt-oss:120b-cloud model (120B parameters)
   - Generates blog post, title, and description
   - Supports streaming for long content

4. **Content Formatter** ([src/content/formatter.py](src/content/formatter.py))
   - Formats content for dev.to (with YAML frontmatter)
   - Formats content for Medium (manual copy-paste)
   - Extracts tags from repo topics
   - Adds footers and metadata

5. **File Manager** ([src/utils/file_manager.py](src/utils/file_manager.py))
   - Saves to `generated_content/{repo_name}_{platform}_{timestamp}.md`
   - Does NOT commit (directory is gitignored)
   - Provides file listing and retrieval

6. **Dev.to Publisher** ([src/publishers/devto.py](src/publishers/devto.py))
   - Publishes via dev.to REST API
   - Supports draft and immediate publish
   - Handles rate limiting (3 second delay)
   - Implements retry logic with tenacity

### Key Design Decisions

- **Modular Architecture**: Each component is independent and reusable
- **Configuration-Driven**: Settings in `config.yaml`, secrets in `.env`
- **CLI-First**: Typer framework for clean command-line interface
- **Error Handling**: Comprehensive error handling with loguru logging
- **Rate Limiting**: Built-in delays to respect API limits
- **Local Storage**: Generated content stored locally for review before publishing

### Important Notes

- **Medium API**: Deprecated - content is generated for manual copy-paste only
- **Rate Limits**:
  - Dev.to: 10 requests/30 seconds (handled automatically)
  - GitHub: 5000/hour with token, 60/hour without
  - Ollama: Based on cloud plan
- **File Naming**: `{repo_name}_{platform}_{timestamp}.md` format
- **Content Review**: Always review generated content before publishing
- **API Keys**: Never commit `.env` file with real keys

### Configuration Files

- **[config/config.yaml](config/config.yaml)**: Application settings (tone, formatting, patterns)
- **[.env](.env)**: API keys and secrets (not committed)
- **[requirements.txt](requirements.txt)**: Python dependencies

### Error Handling Strategy

- Retry logic on API calls (3 attempts with exponential backoff)
- Graceful degradation (e.g., generate title from project name if AI fails)
- Comprehensive logging at all levels
- User-friendly error messages in CLI

### Testing Strategy

When adding new features:
1. Test with a small public GitHub repo first
2. Review generated content before publishing
3. Use draft mode for initial dev.to posts
4. Check logs for any warnings or errors
5. Verify rate limits are respected
