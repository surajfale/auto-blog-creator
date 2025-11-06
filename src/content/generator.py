"""Content generator using Ollama API."""

from typing import Optional

from loguru import logger
from ollama import Client
from tenacity import retry, stop_after_attempt, wait_exponential


class ContentGenerator:
    """Generates blog content using Ollama AI."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-oss:120b-cloud",
        host: str = "https://ollama.com",
    ):
        """Initialize content generator.

        Args:
            api_key: Ollama API key
            model: Model name to use
            host: Ollama API host
        """
        self.model = model
        self.client = Client(
            host=host,
            headers={"Authorization": f"Bearer {api_key}"},
        )

        logger.info(f"Initialized Ollama client with model: {model}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def generate_blog_post(
        self,
        project_info: str,
        tone: str = "professional but witty",
        target_length: int = 1500,
        additional_instructions: Optional[str] = None,
    ) -> str:
        """Generate blog post content.

        Args:
            project_info: Combined project information
            tone: Desired tone for the content
            target_length: Target word count
            additional_instructions: Additional instructions for generation

        Returns:
            Generated blog post content

        Raises:
            Exception: If generation fails after retries
        """
        # Build prompt
        prompt = self._build_prompt(
            project_info=project_info,
            tone=tone,
            target_length=target_length,
            additional_instructions=additional_instructions,
        )

        logger.info(f"Generating blog post with {len(prompt)} character prompt")

        try:
            # Generate content
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a skilled technical writer who creates engaging, modern, and visually appealing blog posts about software projects. You use emojis strategically to enhance readability and engagement. You focus on showcasing projects' core strengths, features, and technical implementation—especially AI/ML and prompt engineering aspects—rather than setup instructions.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )

            content = response["message"]["content"]
            logger.info(f"Generated {len(content)} characters of content")

            return content

        except Exception as e:
            logger.error(f"Failed to generate content: {e}")
            raise

    def generate_blog_post_streaming(
        self,
        project_info: str,
        tone: str = "professional but witty",
        target_length: int = 1500,
        additional_instructions: Optional[str] = None,
    ):
        """Generate blog post content with streaming.

        Args:
            project_info: Combined project information
            tone: Desired tone for the content
            target_length: Target word count
            additional_instructions: Additional instructions for generation

        Yields:
            Content chunks as they are generated
        """
        prompt = self._build_prompt(
            project_info=project_info,
            tone=tone,
            target_length=target_length,
            additional_instructions=additional_instructions,
        )

        logger.info(f"Starting streaming generation with {len(prompt)} character prompt")

        try:
            for chunk in self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a skilled technical writer who creates engaging, modern, and visually appealing blog posts about software projects. You use emojis strategically to enhance readability and engagement. You focus on showcasing projects' core strengths, features, and technical implementation—especially AI/ML and prompt engineering aspects—rather than setup instructions.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                stream=True,
            ):
                content = chunk["message"]["content"]
                yield content

            logger.info("Streaming generation completed")

        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            raise

    def _build_prompt(
        self,
        project_info: str,
        tone: str,
        target_length: int,
        additional_instructions: Optional[str] = None,
    ) -> str:
        """Build prompt for content generation.

        Args:
            project_info: Project information
            tone: Desired tone
            target_length: Target word count
            additional_instructions: Additional instructions

        Returns:
            Complete prompt
        """
        prompt_parts = [
            "You are a technical writer creating an engaging, modern blog post about a GitHub project.",
            "",
            "Project Information:",
            project_info,
            "",
            "Instructions:",
            f"- Write in a {tone} tone",
            f"- Target length: approximately {target_length} words",
            "- **IMPORTANT**: Use emojis liberally throughout the content (at least 2-3 emojis per section)",
            "- Add emojis to section headings (e.g., '🚀 Key Features', '✨ Core Strengths', '🤖 AI Implementation')",
            "- Use emojis to highlight important points and make the text visually appealing",
            "",
            "CONTENT FOCUS (CRITICAL):",
            "- **PRIMARY FOCUS**: Highlight the project's CORE STRENGTHS and KEY FEATURES",
            "- Explain the problem the project solves and its unique value proposition",
            "- If the project uses AI/LLMs: Deep dive into the AI implementation, prompt engineering strategies, and how AI is leveraged",
            "- Showcase technical architecture and design decisions that make the project stand out",
            "- Include code examples that demonstrate the project's capabilities (not setup instructions)",
            "- Discuss use cases, benefits, and real-world applications",
            "- Write for developers interested in the project's technical implementation and capabilities",
            "",
            "WHAT TO AVOID:",
            "- **DO NOT** focus on setup/installation steps (briefly mention setup exists with a link to documentation)",
            "- **DO NOT** provide detailed 'Getting Started' or 'How to Run Locally' sections",
            "- **DO NOT** include extensive environment setup or configuration details",
            "- Instead of setup instructions, direct readers: 'For setup instructions, see [README.md](link) or [CONTRIBUTING.md](link)'",
            "- Keep setup references to 1-2 sentences maximum",
            "",
            "STRUCTURE:",
            "- Start with a compelling introduction about what the project does",
            "- Focus heavily on features, architecture, and technical implementation",
            "- If applicable, dedicate a section to AI/ML implementation and prompt engineering techniques",
            "- Use clear sections with emoji-enhanced headings",
            "- Make it engaging, modern, and technically insightful",
            "",
        ]

        if additional_instructions:
            prompt_parts.append("Additional Instructions:")
            prompt_parts.append(additional_instructions)
            prompt_parts.append("")

        prompt_parts.append(
            "Generate a comprehensive, engaging blog post in Markdown format that showcases the project's technical excellence and core capabilities."
        )

        return "\n".join(prompt_parts)

    def generate_title(self, project_info: str) -> str:
        """Generate a catchy title for the blog post.

        Args:
            project_info: Project information

        Returns:
            Generated title
        """
        prompt = f"""Based on this GitHub project information, generate a catchy, engaging blog post title.

Project Information:
{project_info[:1000]}  # Truncate for title generation

Requirements:
- Keep it concise (under 80 characters)
- Make it engaging and clickable
- Clearly convey what the project is about
- Use action words when appropriate

Generate ONLY the title, nothing else."""

        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )

            title = response["message"]["content"].strip()
            # Remove quotes if present
            title = title.strip('"\'')

            logger.info(f"Generated title: {title}")
            return title

        except Exception as e:
            logger.error(f"Failed to generate title: {e}")
            # Return a default title
            return "Exploring an Interesting GitHub Project"

    def generate_description(self, content: str, max_length: int = 160) -> str:
        """Generate a meta description from the blog content.

        Args:
            content: Blog post content
            max_length: Maximum length for description

        Returns:
            Generated description
        """
        # Take first paragraph or first 500 characters
        excerpt = content[:500]

        prompt = f"""Based on this blog post excerpt, generate a compelling meta description.

Excerpt:
{excerpt}

Requirements:
- Maximum {max_length} characters
- Summarize the main point
- Make it engaging
- Include key information

Generate ONLY the description, nothing else."""

        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )

            description = response["message"]["content"].strip()
            # Remove quotes if present
            description = description.strip('"\'')

            # Truncate if needed
            if len(description) > max_length:
                description = description[:max_length - 3] + "..."

            logger.info(f"Generated description: {description}")
            return description

        except Exception as e:
            logger.error(f"Failed to generate description: {e}")
            # Return excerpt
            return excerpt[:max_length - 3] + "..." if len(excerpt) > max_length else excerpt
