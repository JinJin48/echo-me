"""
notion_publisher モジュール

Notion APIを使用してMarkdownコンテンツをNotionデータベースに投稿する
"""

import os
import re
from typing import Optional

from dotenv import load_dotenv
from notion_client import Client


class NotionPublisher:
    """Notionにコンテンツを投稿するクラス"""

    def __init__(
        self,
        api_key: str | None = None,
        database_id: str | None = None,
    ):
        """NotionPublisherを初期化する

        Args:
            api_key: Notion APIキー。Noneの場合は環境変数から取得
            database_id: NotionデータベースID。Noneの場合は環境変数から取得

        Raises:
            ValueError: 必要な設定が不足している場合
        """
        load_dotenv()

        self.api_key = api_key or os.getenv("NOTION_API_KEY")
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID")

        if not self.api_key:
            raise ValueError(
                "NOTION_API_KEYが設定されていません。"
                ".envファイルで設定してください。"
            )

        if not self.database_id:
            raise ValueError(
                "NOTION_DATABASE_IDが設定されていません。"
                ".envファイルで設定してください。"
            )

        self.client = Client(auth=self.api_key)

    def markdown_to_notion_blocks(self, markdown: str) -> list[dict]:
        """MarkdownをNotionブロックに変換する

        Args:
            markdown: Markdown形式のテキスト

        Returns:
            Notionブロックのリスト
        """
        blocks = []
        lines = markdown.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]

            # 空行
            if not line.strip():
                i += 1
                continue

            # 見出し
            if line.startswith("### "):
                blocks.append(self._create_heading_block(line[4:], 3))
                i += 1
                continue
            elif line.startswith("## "):
                blocks.append(self._create_heading_block(line[3:], 2))
                i += 1
                continue
            elif line.startswith("# "):
                blocks.append(self._create_heading_block(line[2:], 1))
                i += 1
                continue

            # コードブロック
            if line.startswith("```"):
                language = line[3:].strip() or "plain text"
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].startswith("```"):
                    code_lines.append(lines[i])
                    i += 1
                blocks.append(self._create_code_block("\n".join(code_lines), language))
                i += 1
                continue

            # 箇条書き
            if line.startswith("- ") or line.startswith("* "):
                blocks.append(self._create_bulleted_list_block(line[2:]))
                i += 1
                continue

            # 番号付きリスト
            numbered_match = re.match(r"^\d+\.\s+(.+)$", line)
            if numbered_match:
                blocks.append(self._create_numbered_list_block(numbered_match.group(1)))
                i += 1
                continue

            # 引用
            if line.startswith("> "):
                blocks.append(self._create_quote_block(line[2:]))
                i += 1
                continue

            # 通常の段落
            blocks.append(self._create_paragraph_block(line))
            i += 1

        return blocks

    def _create_heading_block(self, text: str, level: int) -> dict:
        """見出しブロックを作成する"""
        heading_type = f"heading_{level}"
        return {
            "object": "block",
            "type": heading_type,
            heading_type: {
                "rich_text": self._parse_rich_text(text),
            },
        }

    def _create_paragraph_block(self, text: str) -> dict:
        """段落ブロックを作成する"""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": self._parse_rich_text(text),
            },
        }

    def _create_bulleted_list_block(self, text: str) -> dict:
        """箇条書きブロックを作成する"""
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": self._parse_rich_text(text),
            },
        }

    def _create_numbered_list_block(self, text: str) -> dict:
        """番号付きリストブロックを作成する"""
        return {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": self._parse_rich_text(text),
            },
        }

    def _create_quote_block(self, text: str) -> dict:
        """引用ブロックを作成する"""
        return {
            "object": "block",
            "type": "quote",
            "quote": {
                "rich_text": self._parse_rich_text(text),
            },
        }

    def _create_code_block(self, code: str, language: str) -> dict:
        """コードブロックを作成する"""
        return {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{"type": "text", "text": {"content": code}}],
                "language": language,
            },
        }

    def _parse_rich_text(self, text: str) -> list[dict]:
        """テキストをリッチテキスト形式に変換する

        太字、イタリック、コード、リンクを処理する
        """
        rich_text = []
        remaining = text

        while remaining:
            # 太字 **text**
            bold_match = re.match(r"^(.*?)\*\*(.+?)\*\*(.*)$", remaining, re.DOTALL)
            if bold_match:
                before, bold_text, after = bold_match.groups()
                if before:
                    rich_text.extend(self._parse_rich_text(before))
                rich_text.append({
                    "type": "text",
                    "text": {"content": bold_text},
                    "annotations": {"bold": True},
                })
                remaining = after
                continue

            # イタリック *text* または _text_
            italic_match = re.match(r"^(.*?)(?:\*([^*]+)\*|_([^_]+)_)(.*)$", remaining, re.DOTALL)
            if italic_match:
                before = italic_match.group(1)
                italic_text = italic_match.group(2) or italic_match.group(3)
                after = italic_match.group(4)
                if before:
                    rich_text.extend(self._parse_rich_text(before))
                rich_text.append({
                    "type": "text",
                    "text": {"content": italic_text},
                    "annotations": {"italic": True},
                })
                remaining = after
                continue

            # インラインコード `code`
            code_match = re.match(r"^(.*?)`([^`]+)`(.*)$", remaining, re.DOTALL)
            if code_match:
                before, code_text, after = code_match.groups()
                if before:
                    rich_text.extend(self._parse_rich_text(before))
                rich_text.append({
                    "type": "text",
                    "text": {"content": code_text},
                    "annotations": {"code": True},
                })
                remaining = after
                continue

            # リンク [text](url)
            link_match = re.match(r"^(.*?)\[([^\]]+)\]\(([^)]+)\)(.*)$", remaining, re.DOTALL)
            if link_match:
                before, link_text, url, after = link_match.groups()
                if before:
                    rich_text.extend(self._parse_rich_text(before))
                rich_text.append({
                    "type": "text",
                    "text": {"content": link_text, "link": {"url": url}},
                })
                remaining = after
                continue

            # プレーンテキスト
            rich_text.append({
                "type": "text",
                "text": {"content": remaining},
            })
            break

        return rich_text

    def create_page(
        self,
        title: str,
        content: str,
        properties: dict | None = None,
    ) -> str:
        """Notionデータベースに新しいページを作成する

        Args:
            title: ページタイトル
            content: Markdown形式のコンテンツ
            properties: 追加のプロパティ（オプション）

        Returns:
            作成されたページのID
        """
        # Markdownをブロックに変換
        blocks = self.markdown_to_notion_blocks(content)

        # ページプロパティを設定
        page_properties = {
            "title": {
                "title": [{"type": "text", "text": {"content": title}}]
            }
        }

        if properties:
            page_properties.update(properties)

        # ページを作成
        response = self.client.pages.create(
            parent={"database_id": self.database_id},
            properties=page_properties,
            children=blocks,
        )

        return response["id"]


def post_to_notion(
    title: str,
    content: str,
    api_key: str | None = None,
    database_id: str | None = None,
) -> str:
    """Notionにコンテンツを投稿する（関数インターフェース）

    Args:
        title: ページタイトル
        content: Markdown形式のコンテンツ
        api_key: Notion APIキー（オプション）
        database_id: NotionデータベースID（オプション）

    Returns:
        作成されたページのID
    """
    publisher = NotionPublisher(api_key, database_id)
    return publisher.create_page(title, content)
