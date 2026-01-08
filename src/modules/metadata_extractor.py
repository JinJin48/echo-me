"""
Metadata extractor module for RAG functionality.

Extracts metadata from filenames based on patterns and allows manual override.
Supports .meta.yaml files for per-file metadata configuration.
"""

import os
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

import yaml


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
) -> ContentMetadata:
    """
    Extract metadata with priority: CLI args > .meta.yaml > filename inference.

    Priority order:
    1. Command-line arguments (source_override, type_override, etc.)
    2. .meta.yaml file (if exists next to input file)
    3. Filename pattern inference

    Args:
        filename: The input filename
        source_override: Manual override for source field (highest priority)
        type_override: Manual override for type field (highest priority)
        topics: List of topic tags (highest priority)
        date_override: Manual override for date (ISO format: YYYY-MM-DD)

    Returns:
        ContentMetadata object with all metadata fields
    """
    # Layer 1: Infer base metadata from filename (lowest priority)
    inferred = infer_metadata_from_filename(filename)
    base_source = inferred["source"]
    base_type = inferred["type"]
    base_topics: list[str] = []
    base_date = date.today().isoformat()

    # Layer 2: Load from .meta.yaml file (medium priority)
    yaml_metadata = load_metadata_from_yaml(filename)
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

    # Layer 3: Apply CLI overrides if provided (highest priority)
    final_source = source_override if source_override else base_source
    final_type = type_override if type_override else base_type
    final_topics = topics if topics else base_topics
    final_date = date_override if date_override else base_date

    # Extract original filename (basename only)
    original_file = filename.split("/")[-1].split("\\")[-1]

    return ContentMetadata(
        source=final_source,
        type=final_type,
        date=final_date,
        original_file=original_file,
        topics=final_topics,
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
