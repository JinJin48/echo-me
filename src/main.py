"""
echo-me Content Generator

音声文字起こしやMarkdownファイルからブログ・SNS投稿を自動生成するメインスクリプト
"""

import argparse
import sys

from modules.file_reader import read_file, get_supported_extensions
from modules.llm_processor import LLMProcessor
from modules.content_formatter import save_outputs


def main():
    """メイン関数"""
    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(
        description="音声/MDファイルからブログ・SNS投稿を自動生成"
    )
    parser.add_argument(
        "input_file",
        help=f"入力ファイルのパス（対応形式: {', '.join(get_supported_extensions())}）",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="output",
        help="出力ディレクトリ（デフォルト: output）",
    )
    parser.add_argument(
        "--no-timestamp",
        action="store_true",
        help="タイムスタンプ付きサブディレクトリを作成しない",
    )
    args = parser.parse_args()

    try:
        # 入力ファイルを読み込み
        print(f"入力ファイルを読み込み中: {args.input_file}")
        input_content = read_file(args.input_file)

        # LLMプロセッサを初期化
        print("Claude APIに接続中...")
        processor = LLMProcessor()

        # 各コンテンツを生成
        print("ブログ記事を生成中...")
        blog_content = processor.generate_content(input_content, "blog")

        print("X投稿を生成中...")
        x_content = processor.generate_content(input_content, "x_post")

        print("LinkedIn投稿を生成中...")
        linkedin_content = processor.generate_content(input_content, "linkedin")

        # 出力を保存
        print("ファイルを保存中...")
        paths = save_outputs(
            blog=blog_content,
            x_post=x_content,
            linkedin=linkedin_content,
            output_dir=args.output_dir,
            use_timestamp=not args.no_timestamp,
        )

        print(f"\n生成完了!")
        print(f"出力ディレクトリ: {paths.output_dir}")
        print(f"  - ブログ: {paths.blog}")
        print(f"  - X投稿: {paths.x_post}")
        print(f"  - LinkedIn: {paths.linkedin}")

    except FileNotFoundError as e:
        print(f"エラー: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"エラー: {e}")
        sys.exit(1)
    except ImportError as e:
        print(f"エラー: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
