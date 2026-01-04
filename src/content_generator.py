"""
echo-me Content Generator

音声文字起こしやMarkdownファイルからブログ・SNS投稿を自動生成するスクリプト
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv


def load_input_file(file_path: str) -> str:
    """入力ファイルを読み込む

    Args:
        file_path: 入力ファイルのパス

    Returns:
        ファイルの内容

    Raises:
        FileNotFoundError: ファイルが存在しない場合
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {file_path}")

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def generate_blog_post(client: Anthropic, content: str) -> str:
    """ブログ記事を生成する

    Args:
        client: Anthropic APIクライアント
        content: 入力コンテンツ

    Returns:
        生成されたブログ記事（Markdown形式）
    """
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": f"""以下のコンテンツを元に、技術ブログ記事を作成してください。

【要件】
- Markdown形式で出力
- 読みやすい構造（見出し、箇条書きを適切に使用）
- 技術的な正確性を保ちつつ、分かりやすく説明
- SAP/IT技術に関連する場合は専門用語を適切に使用
- 導入、本文、まとめの構成

【入力コンテンツ】
{content}

ブログ記事のみを出力してください（説明や前置きは不要）:""",
            }
        ],
    )
    return message.content[0].text


def generate_x_post(client: Anthropic, content: str) -> str:
    """X(Twitter)投稿を生成する

    Args:
        client: Anthropic APIクライアント
        content: 入力コンテンツ

    Returns:
        生成されたX投稿（280文字以内）
    """
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": f"""以下のコンテンツを元に、X(Twitter)投稿を作成してください。

【要件】
- 280文字以内（日本語）
- キャッチーで興味を引く内容
- 関連するハッシュタグを2-3個含める（例: #SAP #テクノロジー #DX）
- 絵文字は控えめに使用（0-2個程度）

【入力コンテンツ】
{content}

X投稿のみを出力してください（説明や前置きは不要）:""",
            }
        ],
    )
    return message.content[0].text


def generate_linkedin_post(client: Anthropic, content: str) -> str:
    """LinkedIn投稿を生成する

    Args:
        client: Anthropic APIクライアント
        content: 入力コンテンツ

    Returns:
        生成されたLinkedIn投稿
    """
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": f"""以下のコンテンツを元に、LinkedIn投稿を作成してください。

【要件】
- プロフェッショナルなトーン
- 読みやすい段落構成
- 価値提供や学びを強調
- 最後に質問や議論を促すCTA（Call To Action）を含める
- 関連するハッシュタグを3-5個含める

【入力コンテンツ】
{content}

LinkedIn投稿のみを出力してください（説明や前置きは不要）:""",
            }
        ],
    )
    return message.content[0].text


def save_output(output_dir: str, filename: str, content: str) -> str:
    """出力ファイルを保存する

    Args:
        output_dir: 出力ディレクトリ
        filename: ファイル名
        content: 保存する内容

    Returns:
        保存したファイルのパス
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    file_path = output_path / filename
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return str(file_path)


def main():
    """メイン関数"""
    # 環境変数を読み込み
    load_dotenv()

    # APIキーの確認
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("エラー: ANTHROPIC_API_KEYが設定されていません。")
        print(".envファイルにANTHROPIC_API_KEY=your_api_keyを設定してください。")
        sys.exit(1)

    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(
        description="音声/MDファイルからブログ・SNS投稿を自動生成"
    )
    parser.add_argument("input_file", help="入力ファイルのパス（.txt または .md）")
    parser.add_argument(
        "-o",
        "--output-dir",
        default="output",
        help="出力ディレクトリ（デフォルト: output）",
    )
    args = parser.parse_args()

    try:
        # 入力ファイルを読み込み
        print(f"入力ファイルを読み込み中: {args.input_file}")
        input_content = load_input_file(args.input_file)

        # Anthropicクライアントを初期化
        client = Anthropic(api_key=api_key)

        # タイムスタンプ付きのサブディレクトリを作成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_subdir = os.path.join(args.output_dir, timestamp)

        # 各コンテンツを生成
        print("ブログ記事を生成中...")
        blog_content = generate_blog_post(client, input_content)
        blog_path = save_output(output_subdir, "blog.md", blog_content)
        print(f"  -> {blog_path}")

        print("X投稿を生成中...")
        x_content = generate_x_post(client, input_content)
        x_path = save_output(output_subdir, "x_post.txt", x_content)
        print(f"  -> {x_path}")

        print("LinkedIn投稿を生成中...")
        linkedin_content = generate_linkedin_post(client, input_content)
        linkedin_path = save_output(output_subdir, "linkedin_post.txt", linkedin_content)
        print(f"  -> {linkedin_path}")

        print("\n生成完了!")
        print(f"出力ディレクトリ: {output_subdir}")

    except FileNotFoundError as e:
        print(f"エラー: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
