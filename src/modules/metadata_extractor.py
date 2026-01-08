"""
Metadata extractor module for RAG functionality.

Extracts metadata from filenames based on patterns and allows manual override.
"""

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


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


def extract_metadata(
    filename: str,
    source_override: Optional[str] = None,
    type_override: Optional[str] = None,
    topics: Optional[list[str]] = None,
    date_override: Optional[str] = None,
) -> ContentMetadata:
    """
    Extract metadata from filename with optional manual overrides.

    Args:
        filename: The input filename
        source_override: Manual override for source field
        type_override: Manual override for type field
        topics: List of topic tags
        date_override: Manual override for date (ISO format: YYYY-MM-DD)

    Returns:
        ContentMetadata object with all metadata fields
    """
    # Infer base metadata from filename
    inferred = infer_metadata_from_filename(filename)

    # Apply overrides if provided
    source = source_override if source_override else inferred["source"]
    content_type = type_override if type_override else inferred["type"]

    # Use current date if not overridden
    metadata_date = date_override if date_override else date.today().isoformat()

    # Extract original filename (basename only)
    original_file = filename.split("/")[-1].split("\\")[-1]

    return ContentMetadata(
        source=source,
        type=content_type,
        date=metadata_date,
        original_file=original_file,
        topics=topics if topics else [],
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
