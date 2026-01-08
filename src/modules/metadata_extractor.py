"""
Metadata extractor module for RAG functionality.

Extracts metadata from filenames based on patterns and allows manual override.
Supports .meta.yaml files for per-file metadata configuration.
Supports LLM-based metadata generation using Claude API.
"""

import os
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

import yaml
from anthropic import Anthropic
from dotenv import load_dotenv


# Filename pattern to metadata mapping
FILENAME_PATTERNS = {
    r"^meeting_": {"source": "meeting", "type": "minutes"},
    r"^interview_": {"source": "interview", "type": "transcript"},
    r"^memo_": {"source": "memo", "type": "note"},
    r"^webinar_": {"source": "webinar", "type": "summary"},
}

# Default metadata for unrecognized patterns
DEFAULT_METADATA = {"source": "unknown", "type": "general"}


@dataclass
class ContentMetadata:
    """Metadata for RAG content."""

    source: str
    type: str
    date: str
    original_file: str
    topics: list[str] = field(default_factory=list)
    summary: str = ""

    def to_yaml_frontmatter(self) -> str:
        """Convert metadata to YAML frontmatter string."""
        lines = ["---"]
        lines.append(f"source: {self.source}")
        lines.append(f"type: {self.type}")
        lines.append(f"date: {self.date}")

        if self.topics:
            topics_str = ", ".join(self.topics)
            lines.append(f"topics: [{topics_str}]")
        else:
            lines.append("topics: []")

        if self.summary:
            lines.append(f"summary: {self.summary}")

        lines.append(f"original_file: {self.original_file}")
        lines.append("---")
        lines.append("")  # Empty line after frontmatter

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert metadata to dictionary."""
        return {
            "source": self.source,
            "type": self.type,
            "date": self.date,
            "topics": self.topics,
            "summary": self.summary,
            "original_file": self.original_file,
        }


def infer_metadata_from_filename(filename: str) -> dict:
    """
    Infer metadata from filename based on predefined patterns.

    Args:
        filename: The input filename (with or without extension)

    Returns:
        Dictionary with 'source' and 'type' keys
    """
    # Remove path and get just the filename
    base_filename = filename.split("/")[-1].split("\\")[-1]

    for pattern, metadata in FILENAME_PATTERNS.items():
        if re.match(pattern, base_filename, re.IGNORECASE):
            return metadata.copy()

    return DEFAULT_METADATA.copy()


def get_meta_yaml_path(filepath: str) -> str:
    """
    Get the path to the .meta.yaml file for a given input file.

    Args:
        filepath: Path to the input file

    Returns:
        Path to the corresponding .meta.yaml file

    Example:
        meeting_20250108.txt -> meeting_20250108.meta.yaml
    """
    path = Path(filepath)
    # Remove extension and add .meta.yaml
    return str(path.parent / f"{path.stem}.meta.yaml")


def load_metadata_from_yaml(filepath: str) -> Optional[dict]:
    """
    Load metadata from a .meta.yaml file if it exists.

    Args:
        filepath: Path to the input file (not the .meta.yaml file)

    Returns:
        Dictionary with metadata fields, or None if file doesn't exist
    """
    meta_path = get_meta_yaml_path(filepath)

    if not os.path.exists(meta_path):
        return None

    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data is None:
                return None
            return data
    except (yaml.YAMLError, OSError) as e:
        print(f"Warning: Failed to load metadata from {meta_path}: {e}")
        return None


def extract_metadata(
    filename: str,
    source_override: Optional[str] = None,
    type_override: Optional[str] = None,
    topics: Optional[list[str]] = None,
    date_override: Optional[str] = None,
    content: Optional[str] = None,
    use_llm: bool = True,
    summary_override: Optional[str] = None,
) -> ContentMetadata:
    """
    Extract metadata with priority: CLI args > .meta.yaml > LLM > filename inference.

    Priority order:
    1. Command-line arguments (source_override, type_override, etc.)
    2. .meta.yaml file (if exists next to input file)
    3. LLM-based generation (if content is provided and use_llm=True)
    4. Filename pattern inference

    Args:
        filename: The input filename
        source_override: Manual override for source field (highest priority)
        type_override: Manual override for type field (highest priority)
        topics: List of topic tags (highest priority)
        date_override: Manual override for date (ISO format: YYYY-MM-DD)
        content: Text content for LLM-based metadata generation
        use_llm: Whether to use LLM for metadata generation (default: True)
        summary_override: Manual override for summary field

    Returns:
        ContentMetadata object with all metadata fields
    """
    # Layer 1: Infer base metadata from filename (lowest priority)
    inferred = infer_metadata_from_filename(filename)
    base_source = inferred["source"]
    base_type = inferred["type"]
    base_topics: list[str] = []
    base_date = date.today().isoformat()
    base_summary = ""

    # Layer 2: LLM-based generation (if no .meta.yaml and content provided)
    yaml_metadata = load_metadata_from_yaml(filename)
    llm_metadata: Optional[dict] = None

    if yaml_metadata is None and content and use_llm:
        # No .meta.yaml file - try LLM generation
        try:
            llm_metadata = generate_metadata_with_llm(content)
            if llm_metadata:
                base_source = llm_metadata.get("source", base_source)
                base_type = llm_metadata.get("type", base_type)
                base_topics = llm_metadata.get("topics", base_topics)
                base_summary = llm_metadata.get("summary", base_summary)
        except Exception as e:
            # LLM generation failed - continue with filename inference
            print(f"Warning: LLMメタデータ生成に失敗しました: {e}")

    # Layer 3: Load from .meta.yaml file (medium-high priority)
    if yaml_metadata:
        if "source" in yaml_metadata:
            base_source = yaml_metadata["source"]
        if "type" in yaml_metadata:
            base_type = yaml_metadata["type"]
        if "topics" in yaml_metadata:
            # Handle both list and comma-separated string
            yaml_topics = yaml_metadata["topics"]
            if isinstance(yaml_topics, list):
                base_topics = yaml_topics
            elif isinstance(yaml_topics, str):
                base_topics = parse_topics_string(yaml_topics)
        if "date" in yaml_metadata:
            base_date = yaml_metadata["date"]
        if "summary" in yaml_metadata:
            base_summary = yaml_metadata["summary"]

    # Layer 4: Apply CLI overrides if provided (highest priority)
    final_source = source_override if source_override else base_source
    final_type = type_override if type_override else base_type
    final_topics = topics if topics else base_topics
    final_date = date_override if date_override else base_date
    final_summary = summary_override if summary_override else base_summary

    # Extract original filename (basename only)
    original_file = filename.split("/")[-1].split("\\")[-1]

    return ContentMetadata(
        source=final_source,
        type=final_type,
        date=final_date,
        original_file=original_file,
        topics=final_topics,
        summary=final_summary,
    )


def parse_topics_string(topics_str: str) -> list[str]:
    """
    Parse comma-separated topics string into a list.

    Args:
        topics_str: Comma-separated topics (e.g., "SAP,BTP,Cloud")

    Returns:
        List of topic strings, trimmed of whitespace
    """
    if not topics_str:
        return []
    return [topic.strip() for topic in topics_str.split(",") if topic.strip()]


def add_frontmatter_to_content(content: str, metadata: ContentMetadata) -> str:
    """
    Add YAML frontmatter to markdown content.

    Args:
        content: The markdown content
        metadata: ContentMetadata object

    Returns:
        Content with YAML frontmatter prepended
    """
    frontmatter = metadata.to_yaml_frontmatter()
    return frontmatter + content


# LLM metadata generation prompt
LLM_METADATA_PROMPT = """以下の文章を分析して、メタデータをYAML形式で出力してください。

【出力形式】
source: meeting / interview / memo / webinar / unknown から1つ選択
type: minutes / transcript / note / summary / general から1つ選択
topics: 本文から抽出した重要キーワード（3〜5個、リスト形式）
summary: 1行要約（50文字以内）

【選択基準】
- source: コンテンツの出所を判断
  - meeting: 会議、ミーティング、打ち合わせの記録
  - interview: インタビュー、対談、質疑応答
  - memo: メモ、覚書、個人的なノート
  - webinar: ウェビナー、オンラインセミナー、講演
  - unknown: 上記に当てはまらない場合
- type: コンテンツの種類を判断
  - minutes: 議事録形式
  - transcript: 文字起こし、会話の書き起こし
  - note: メモ、ノート形式
  - summary: 要約、まとめ
  - general: 一般的な文書

【入力文章】
{content}

YAMLのみを出力してください（説明や前置きは不要）:
```yaml"""


def generate_metadata_with_llm(
    content: str,
    api_key: str | None = None,
    model: str = "claude-sonnet-4-20250514",
) -> dict:
    """
    Generate metadata using Claude API.

    Args:
        content: The text content to analyze
        api_key: Anthropic API key (uses env var if None)
        model: Model to use for generation

    Returns:
        Dictionary with source, type, topics, and summary

    Raises:
        ValueError: If API key is not set
        Exception: If API call fails
    """
    if api_key is None:
        load_dotenv()
        api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEYが設定されていません。"
            ".envファイルまたは環境変数で設定してください。"
        )

    client = Anthropic(api_key=api_key)

    # Truncate content if too long (first 3000 chars for metadata analysis)
    truncated_content = content[:3000] if len(content) > 3000 else content

    prompt = LLM_METADATA_PROMPT.format(content=truncated_content)

    message = client.messages.create(
        model=model,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text

    # Parse YAML from response
    return _parse_llm_metadata_response(response_text)


def _parse_llm_metadata_response(response: str) -> dict:
    """
    Parse LLM response to extract metadata.

    Args:
        response: Raw response from LLM

    Returns:
        Dictionary with parsed metadata
    """
    # Clean up response - remove markdown code blocks if present
    cleaned = response.strip()
    if cleaned.startswith("```yaml"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        parsed = yaml.safe_load(cleaned)
        if parsed is None:
            parsed = {}
    except yaml.YAMLError:
        parsed = {}

    result = {
        "source": parsed.get("source", "unknown"),
        "type": parsed.get("type", "general"),
        "topics": [],
        "summary": parsed.get("summary", ""),
    }

    # Validate source and type values
    valid_sources = ["meeting", "interview", "memo", "webinar", "unknown"]
    valid_types = ["minutes", "transcript", "note", "summary", "general"]

    if result["source"] not in valid_sources:
        result["source"] = "unknown"
    if result["type"] not in valid_types:
        result["type"] = "general"

    # Handle topics - could be list or comma-separated string
    topics = parsed.get("topics", [])
    if isinstance(topics, list):
        result["topics"] = [str(t).strip() for t in topics if t]
    elif isinstance(topics, str):
        result["topics"] = parse_topics_string(topics)

    # Truncate summary if too long
    if len(result["summary"]) > 50:
        result["summary"] = result["summary"][:47] + "..."

    return result
