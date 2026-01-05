"""
content_formatter モジュール

生成されたコンテンツを出力ファイルとして保存する
"""

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import NamedTuple


class OutputPaths(NamedTuple):
    """出力ファイルパスを格納するNamedTuple"""

    blog: str
    x_post: str
    linkedin: str
    output_dir: str


@dataclass
class ContentOutput:
    """出力コンテンツを格納するデータクラス"""

    blog: str
    x_post: str
    linkedin: str


def save_outputs(
    blog: str,
    x_post: str,
    linkedin: str,
    output_dir: str = "output",
    use_timestamp: bool = True,
) -> OutputPaths:
    """生成されたコンテンツを出力ファイルとして保存する

    Args:
        blog: ブログ記事の内容
        x_post: X投稿の内容
        linkedin: LinkedIn投稿の内容
        output_dir: 出力ディレクトリのパス
        use_timestamp: タイムスタンプ付きサブディレクトリを作成するか

    Returns:
        OutputPaths: 保存されたファイルのパス情報
    """
    # タイムスタンプ付きサブディレクトリを作成
    if use_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_output_dir = os.path.join(output_dir, timestamp)
    else:
        final_output_dir = output_dir

    # ディレクトリを作成
    Path(final_output_dir).mkdir(parents=True, exist_ok=True)

    # 各ファイルを保存
    blog_path = _save_file(final_output_dir, "blog.md", blog)
    x_post_path = _save_file(final_output_dir, "x_post.txt", x_post)
    linkedin_path = _save_file(final_output_dir, "linkedin_post.txt", linkedin)

    return OutputPaths(
        blog=blog_path,
        x_post=x_post_path,
        linkedin=linkedin_path,
        output_dir=final_output_dir,
    )


def _save_file(output_dir: str, filename: str, content: str) -> str:
    """単一のファイルを保存する

    Args:
        output_dir: 出力ディレクトリ
        filename: ファイル名
        content: 保存する内容

    Returns:
        保存したファイルのパス
    """
    file_path = os.path.join(output_dir, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_path


def save_single_output(
    content: str,
    output_dir: str,
    filename: str,
) -> str:
    """単一のコンテンツを保存する

    Args:
        content: 保存する内容
        output_dir: 出力ディレクトリ
        filename: ファイル名

    Returns:
        保存したファイルのパス
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    return _save_file(output_dir, filename, content)


def get_output_filenames() -> dict[str, str]:
    """出力ファイル名の辞書を返す

    Returns:
        コンテンツタイプとファイル名の対応辞書
    """
    return {
        "blog": "blog.md",
        "x_post": "x_post.txt",
        "linkedin": "linkedin_post.txt",
    }
