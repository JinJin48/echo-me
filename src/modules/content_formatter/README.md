# content_formatter モジュール

生成されたコンテンツを出力ファイルとして保存するモジュール

## 概要

このモジュールは、LLMで生成されたコンテンツ（ブログ、X投稿、LinkedIn投稿）を適切なファイル形式で保存します。タイムスタンプ付きのサブディレクトリを自動作成する機能も備えています。

## 出力ファイル

| ファイル名 | 形式 | コンテンツタイプ |
|------------|------|------------------|
| `blog.md` | Markdown | ブログ記事 |
| `x_post.txt` | Plain Text | X(Twitter)投稿 |
| `linkedin_post.txt` | Plain Text | LinkedIn投稿 |

## 関数・クラス一覧

### `save_outputs(blog: str, x_post: str, linkedin: str, output_dir: str = "output", use_timestamp: bool = True) -> OutputPaths`

生成されたコンテンツを出力ファイルとして保存します。

**引数:**
- `blog` (str): ブログ記事の内容
- `x_post` (str): X投稿の内容
- `linkedin` (str): LinkedIn投稿の内容
- `output_dir` (str): 出力ディレクトリのパス（デフォルト: "output"）
- `use_timestamp` (bool): タイムスタンプ付きサブディレクトリを作成するか（デフォルト: True）

**戻り値:**
- `OutputPaths`: 保存されたファイルのパス情報を含むNamedTuple

### `save_single_output(content: str, output_dir: str, filename: str) -> str`

単一のコンテンツを保存します。

**引数:**
- `content` (str): 保存する内容
- `output_dir` (str): 出力ディレクトリ
- `filename` (str): ファイル名

**戻り値:**
- `str`: 保存したファイルのパス

### `get_output_filenames() -> dict[str, str]`

出力ファイル名の辞書を返します。

**戻り値:**
- `dict[str, str]`: コンテンツタイプとファイル名の対応辞書

### `class OutputPaths(NamedTuple)`

出力ファイルパスを格納するNamedTuple。

**属性:**
- `blog` (str): ブログ記事ファイルのパス
- `x_post` (str): X投稿ファイルのパス
- `linkedin` (str): LinkedIn投稿ファイルのパス
- `output_dir` (str): 出力ディレクトリのパス

### `class ContentOutput(dataclass)`

出力コンテンツを格納するデータクラス。

**属性:**
- `blog` (str): ブログ記事の内容
- `x_post` (str): X投稿の内容
- `linkedin` (str): LinkedIn投稿の内容

## 使用例

```python
from modules.content_formatter import save_outputs, save_single_output, get_output_filenames

# すべてのコンテンツを一括保存
paths = save_outputs(
    blog="# ブログ記事\n\n内容...",
    x_post="X投稿の内容 #SAP #テクノロジー",
    linkedin="LinkedIn投稿の内容...",
    output_dir="output"
)

print(f"ブログ: {paths.blog}")
print(f"X投稿: {paths.x_post}")
print(f"LinkedIn: {paths.linkedin}")
print(f"出力ディレクトリ: {paths.output_dir}")

# 単一ファイルを保存
path = save_single_output(
    content="カスタム内容",
    output_dir="output/custom",
    filename="custom.txt"
)

# ファイル名の対応を確認
filenames = get_output_filenames()
# {'blog': 'blog.md', 'x_post': 'x_post.txt', 'linkedin': 'linkedin_post.txt'}
```

## 出力ディレクトリ構造

タイムスタンプ付きサブディレクトリを使用した場合:

```
output/
└── 20240315_143052/
    ├── blog.md
    ├── x_post.txt
    └── linkedin_post.txt
```

## 依存ライブラリ

このモジュールはPython標準ライブラリのみを使用します。追加のインストールは不要です。
