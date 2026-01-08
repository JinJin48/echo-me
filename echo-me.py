#!/usr/bin/env python3
"""
echo-me CLI

ローカルでファイルからブログ・SNS投稿を生成するCLIツール。
RAGメタデータ機能付き。
"""

import argparse
import os
import sys

# Add src to path for module imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from modules.file_reader import read_file, get_supported_extensions
from modules.llm_processor import LLMProcessor
from modules.content_formatter import save_outputs
from modules.metadata_extractor import (
    extract_metadata,
    parse_topics_string,
    add_frontmatter_to_content,
    get_meta_yaml_path,
    load_metadata_from_yaml,
)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="音声ファイルやMarkdownファイルからブログ・SNS投稿を自動生成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 自動推測（ファイル名からメタデータを推測）
  python echo-me.py meeting_20250108.txt

  # 手動上書き
  python echo-me.py input.txt --source "webinar" --type "summary" --topics "SAP,BTP"

  # 出力先を指定
  python echo-me.py input.txt --output ./my_output

ファイル名パターンによるメタデータ自動推測:
  meeting_*   → source: meeting, type: minutes
  interview_* → source: interview, type: transcript
  memo_*      → source: memo, type: note
  webinar_*   → source: webinar, type: summary
  その他       → source: unknown, type: general
        """,
    )

    parser.add_argument(
        "input_file",
        help=f"入力ファイル（対応形式: {', '.join(get_supported_extensions())}）",
    )

    parser.add_argument(
        "--output",
        "-o",
        default="output",
        help="出力ディレクトリ（デフォルト: output）",
    )

    parser.add_argument(
        "--source",
        "-s",
        help="メタデータのsourceを手動指定（例: meeting, webinar, interview）",
    )

    parser.add_argument(
        "--type",
        "-t",
        help="メタデータのtypeを手動指定（例: minutes, summary, transcript）",
    )

    parser.add_argument(
        "--topics",
        help="トピックタグをカンマ区切りで指定（例: SAP,BTP,Cloud）",
    )

    parser.add_argument(
        "--date",
        help="日付を手動指定（ISO形式: YYYY-MM-DD、デフォルト: 今日の日付）",
    )

    parser.add_argument(
        "--no-timestamp",
        action="store_true",
        help="出力ディレクトリにタイムスタンプを付けない",
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    # Check input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: ファイルが見つかりません: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    # Check file extension
    _, ext = os.path.splitext(args.input_file)
    if ext.lower() not in get_supported_extensions():
        print(
            f"Error: 未対応のファイル形式です: {ext}\n"
            f"対応形式: {', '.join(get_supported_extensions())}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"処理中: {args.input_file}")

    # Read input file
    try:
        content = read_file(args.input_file)
        print(f"  ファイル読み込み完了（{len(content)} 文字）")
    except Exception as e:
        print(f"Error: ファイル読み込みエラー: {e}", file=sys.stderr)
        sys.exit(1)

    # Check for .meta.yaml file
    yaml_metadata = load_metadata_from_yaml(args.input_file)
    if yaml_metadata:
        meta_path = get_meta_yaml_path(args.input_file)
        print(f"  メタデータファイル読み込み: {meta_path}")

    # Extract metadata with priority: CLI > .meta.yaml > filename inference
    topics = parse_topics_string(args.topics) if args.topics else None
    metadata = extract_metadata(
        filename=args.input_file,
        source_override=args.source,
        type_override=args.type,
        topics=topics,
        date_override=args.date,
    )
    print(f"  メタデータ: source={metadata.source}, type={metadata.type}")
    if metadata.topics:
        print(f"  トピック: {', '.join(metadata.topics)}")

    # Initialize LLM processor
    try:
        processor = LLMProcessor()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Generate content
    print("  コンテンツ生成中...")
    try:
        blog = processor.generate_content(content, "blog")
        print("    - ブログ記事 生成完了")

        x_post = processor.generate_content(content, "x_post")
        print("    - X投稿 生成完了")

        linkedin = processor.generate_content(content, "linkedin")
        print("    - LinkedIn投稿 生成完了")
    except Exception as e:
        print(f"Error: コンテンツ生成エラー: {e}", file=sys.stderr)
        sys.exit(1)

    # Add frontmatter to blog content
    blog_with_frontmatter = add_frontmatter_to_content(blog, metadata)

    # Save outputs
    try:
        paths = save_outputs(
            blog=blog_with_frontmatter,
            x_post=x_post,
            linkedin=linkedin,
            output_dir=args.output,
            use_timestamp=not args.no_timestamp,
        )
        print(f"\n出力完了:")
        print(f"  - ブログ: {paths.blog}")
        print(f"  - X投稿: {paths.x_post}")
        print(f"  - LinkedIn: {paths.linkedin}")
        print(f"  - 出力先: {paths.output_dir}")
    except Exception as e:
        print(f"Error: ファイル保存エラー: {e}", file=sys.stderr)
        sys.exit(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())
