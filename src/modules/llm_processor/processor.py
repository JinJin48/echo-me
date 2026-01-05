"""
llm_processor モジュール

Claude APIを使用してコンテンツを生成する
"""

import os
from typing import Literal

from anthropic import Anthropic
from dotenv import load_dotenv


# コンテンツタイプの型定義
ContentType = Literal["blog", "x_post", "linkedin"]

# デフォルトのモデル
DEFAULT_MODEL = "claude-sonnet-4-20250514"

# 各コンテンツタイプのプロンプト設定
PROMPTS = {
    "blog": {
        "max_tokens": 4096,
        "system_prompt": """以下のコンテンツを元に、技術ブログ記事を作成してください。

【要件】
- Markdown形式で出力
- 読みやすい構造（見出し、箇条書きを適切に使用）
- 技術的な正確性を保ちつつ、分かりやすく説明
- SAP/IT技術に関連する場合は専門用語を適切に使用
- 導入、本文、まとめの構成

【入力コンテンツ】
{content}

ブログ記事のみを出力してください（説明や前置きは不要）:""",
    },
    "x_post": {
        "max_tokens": 512,
        "system_prompt": """以下のコンテンツを元に、X(Twitter)投稿を作成してください。

【要件】
- 280文字以内（日本語）
- キャッチーで興味を引く内容
- 関連するハッシュタグを2-3個含める（例: #SAP #テクノロジー #DX）
- 絵文字は控えめに使用（0-2個程度）

【入力コンテンツ】
{content}

X投稿のみを出力してください（説明や前置きは不要）:""",
    },
    "linkedin": {
        "max_tokens": 2048,
        "system_prompt": """以下のコンテンツを元に、LinkedIn投稿を作成してください。

【要件】
- プロフェッショナルなトーン
- 読みやすい段落構成
- 価値提供や学びを強調
- 最後に質問や議論を促すCTA（Call To Action）を含める
- 関連するハッシュタグを3-5個含める

【入力コンテンツ】
{content}

LinkedIn投稿のみを出力してください（説明や前置きは不要）:""",
    },
}


class LLMProcessor:
    """Claude APIを使用してコンテンツを生成するクラス"""

    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL):
        """LLMProcessorを初期化する

        Args:
            api_key: Anthropic APIキー。Noneの場合は環境変数から取得
            model: 使用するモデル名

        Raises:
            ValueError: APIキーが設定されていない場合
        """
        if api_key is None:
            load_dotenv()
            api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEYが設定されていません。"
                ".envファイルまたは環境変数で設定してください。"
            )

        self.client = Anthropic(api_key=api_key)
        self.model = model

    def generate_content(self, text: str, content_type: ContentType) -> str:
        """指定されたタイプのコンテンツを生成する

        Args:
            text: 入力テキスト
            content_type: 生成するコンテンツのタイプ
                         ("blog", "x_post", "linkedin")

        Returns:
            生成されたコンテンツ

        Raises:
            ValueError: 不正なcontent_typeが指定された場合
        """
        if content_type not in PROMPTS:
            raise ValueError(
                f"不正なcontent_typeです: {content_type}. "
                f"有効な値: {list(PROMPTS.keys())}"
            )

        prompt_config = PROMPTS[content_type]
        prompt = prompt_config["system_prompt"].format(content=text)

        message = self.client.messages.create(
            model=self.model,
            max_tokens=prompt_config["max_tokens"],
            messages=[{"role": "user", "content": prompt}],
        )

        return message.content[0].text


def generate_content(
    text: str,
    content_type: ContentType,
    api_key: str | None = None,
    model: str = DEFAULT_MODEL,
) -> str:
    """コンテンツを生成する（関数インターフェース）

    Args:
        text: 入力テキスト
        content_type: 生成するコンテンツのタイプ
                     ("blog", "x_post", "linkedin")
        api_key: Anthropic APIキー。Noneの場合は環境変数から取得
        model: 使用するモデル名

    Returns:
        生成されたコンテンツ
    """
    processor = LLMProcessor(api_key=api_key, model=model)
    return processor.generate_content(text, content_type)


def get_content_types() -> list[str]:
    """利用可能なコンテンツタイプのリストを返す

    Returns:
        コンテンツタイプのリスト
    """
    return list(PROMPTS.keys())
