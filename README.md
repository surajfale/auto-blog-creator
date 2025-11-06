# Auto-Blog-Creator

Automatically generate and publish engaging blog posts from GitHub repositories using AI.

## Overview

Auto-Blog-Creator scans GitHub repositories, extracts project information from markdown files, generates professional blog content using Ollama AI, and publishes to dev.to with a single command. It saves time for developers who want to promote their projects through blog posts.

## Features

- 🔍 **Smart GitHub Scanning** - Automatically finds and reads all markdown files in any public repository
- 🤖 **AI-Powered Content Generation** - Uses Ollama's gpt-oss:120b-cloud model to create engaging, professional content
- 📝 **Multi-Platform Support** - Formats content for dev.to (auto-publish) and Medium (manual copy-paste)
- ⚡ **One-Command Workflow** - Generate and review blog posts with a single command
- 🎨 **Customizable Tone** - Configure writing style (professional, witty, technical, etc.)
- 💾 **Local Storage** - All generated content saved locally for review before publishing
- 🚀 **CLI & Standalone Scripts** - Use as a CLI tool or standalone scripts

## Quick Start

### Prerequisites

- Python 3.8 or higher
- [Ollama cloud account](https://ollama.com) with API access
- [Dev.to account](https://dev.to) with API key
- GitHub personal access token (optional but recommended)

### Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/auto-blog-creator.git
cd auto-blog-creator
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API keys
```

Required environment variables:
- `OLLAMA_API_KEY` - Get from [ollama.com/settings/keys](https://ollama.com/settings/keys)
- `DEVTO_API_KEY` - Generate at [dev.to/settings/extensions](https://dev.to/settings/extensions)
- `GITHUB_TOKEN` - Optional, create at [github.com/settings/tokens](https://github.com/settings/tokens)

### Usage

#### Generate Blog Posts

```bash
# Generate blog posts from a GitHub repository
python main.py generate https://github.com/username/repo

# Generate for specific platforms
python main.py generate https://github.com/username/repo --platforms devto,medium

# Specify custom output directory
python main.py generate https://github.com/username/repo --output my_posts
```

This will:
1. Scan the repository for markdown files
2. Extract project information
3. Generate blog content using AI
4. Format for dev.to and Medium
5. Save files to `generated_content/`

#### Review Generated Content

Generated files are saved in the `generated_content/` directory with the format:
```
{repo_name}_{platform}_{timestamp}.md
```

Example:
```
generated_content/
├── awesome-project_devto_20250106_120000.md
└── awesome-project_medium_20250106_120000.md
```

#### Publish to dev.to

After reviewing the generated content:

```bash
# Publish as draft (recommended first)
python main.py publish generated_content/awesome-project_devto_20250106_120000.md

# Publish immediately
python main.py publish generated_content/awesome-project_devto_20250106_120000.md --publish
```

Or use the standalone script:

```bash
# Publish as draft
python publish_to_devto.py generated_content/awesome-project_devto_20250106_120000.md

# Publish immediately
python publish_to_devto.py generated_content/awesome-project_devto_20250106_120000.md --publish
```

#### Additional Commands

```bash
# Check configuration
python main.py config-check

# List all generated files
python main.py list-files

# Filter by platform
python main.py list-files --platform devto

# Filter by repository
python main.py list-files --repo awesome-project
```

## Configuration

### Application Settings

Edit `config/config.yaml` to customize:

- **Content generation**: Tone, style, target word count
- **GitHub scanning**: File patterns to include/exclude
- **Output**: Filename format, timestamp format
- **API settings**: Retry logic, timeouts, rate limits

Example customizations:

```yaml
# Change content tone
content:
  tone: "technical and detailed"  # or "casual and friendly", etc.
  target_length: 2000  # words

# Add more file patterns
github:
  include_patterns:
    - "*.md"
    - "docs/**/*.md"
    - "CHANGELOG.md"
```

### Environment Variables

All sensitive data goes in `.env`:

```env
# Required
OLLAMA_API_KEY=your_ollama_api_key
DEVTO_API_KEY=your_devto_api_key

# Optional
GITHUB_TOKEN=your_github_token
OLLAMA_MODEL=gpt-oss:120b-cloud
DEVTO_AUTO_PUBLISH=false
```

## Project Structure

```
auto-blog-creator/
├── src/
│   ├── github/              # GitHub integration
│   │   ├── scanner.py       # Repository scanning
│   │   └── content_parser.py # Content extraction
│   ├── content/             # AI content generation
│   │   ├── generator.py     # Ollama integration
│   │   └── formatter.py     # Platform formatting
│   ├── publishers/          # Platform publishers
│   │   └── devto.py        # Dev.to API
│   └── utils/               # Utilities
│       ├── config.py        # Configuration
│       └── file_manager.py  # File operations
├── config/
│   └── config.yaml          # App configuration
├── generated_content/       # Generated posts (gitignored)
├── main.py                  # CLI application
├── publish_to_devto.py     # Standalone publisher
├── requirements.txt         # Dependencies
└── .env                     # API keys (gitignored)
```

## How It Works

1. **GitHub Scanner** connects to GitHub API and recursively scans for markdown files
2. **Content Parser** prioritizes README files and extracts project information
3. **Content Generator** sends project info to Ollama AI with custom prompts
4. **Content Formatter** formats the output for dev.to (with frontmatter) and Medium
5. **File Manager** saves files locally with timestamp naming
6. **Dev.to Publisher** posts to dev.to via their REST API

## API Rate Limits

- **Dev.to**: 10 requests per 30 seconds (handled automatically)
- **GitHub**: 60/hour without token, 5,000/hour with token
- **Ollama**: Depends on your cloud plan

The application implements automatic retry logic and rate limiting to respect these limits.

## Tips

1. **Start with drafts**: Always publish as draft first to review on dev.to
2. **Review AI content**: AI-generated content should be reviewed and edited
3. **Use GitHub token**: Increases rate limit from 60 to 5,000 requests/hour
4. **Test with small repos**: Try with a small repository first
5. **Customize prompts**: Edit `config/config.yaml` to adjust content generation
6. **Medium posts**: Copy from generated Medium file and paste manually

## Troubleshooting

### "OLLAMA_API_KEY not found"
Make sure you've created a `.env` file and added your API key:
```bash
cp .env.example .env
# Edit .env and add OLLAMA_API_KEY=your_key
```

### "GitHub rate limit exceeded"
Add a `GITHUB_TOKEN` to your `.env` file to increase limits from 60 to 5,000 requests/hour.

### "Failed to generate content"
Check your Ollama API key and ensure you have cloud API access. The model `gpt-oss:120b-cloud` requires cloud access.

### "Dev.to API error"
Verify your `DEVTO_API_KEY` is correct and has write permissions.

## Medium Publishing

Medium's API is officially deprecated, so this tool generates Medium-formatted markdown files that you can:

1. Open the generated `*_medium_*.md` file
2. Copy the content
3. Go to [medium.com/new-story](https://medium.com/new-story)
4. Paste the content
5. Publish manually

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with [PyGithub](https://github.com/PyGithub/PyGithub) for GitHub API
- Powered by [Ollama](https://ollama.com) for AI content generation
- Uses [Typer](https://typer.tiangolo.com/) for CLI framework
- Publishes to [dev.to](https://dev.to) via their API

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

**Made with ❤️ for developers who want to share their projects**
