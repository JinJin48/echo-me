# file_reader モジュール

様々な形式のファイルからテキストを読み込むモジュール

## 概要

このモジュールは、複数のファイル形式（テキスト、Markdown、Word文書、PDF）からテキストを抽出する機能を提供します。

## 対応形式

| 拡張子 | 形式 | 必要なライブラリ |
|--------|------|------------------|
| `.txt` | プレーンテキスト | なし |
| `.md` | Markdown | なし |
| `.docx` | Microsoft Word | python-docx |
| `.pdf` | PDF | PyMuPDF |

## 関数一覧

### `read_file(filepath: str) -> str`

指定されたファイルを読み込み、テキストを返します。

**引数:**
- `filepath` (str): 読み込むファイルのパス

**戻り値:**
- `str`: ファイルの内容（テキスト）

**例外:**
- `FileNotFoundError`: ファイルが存在しない場合
- `ValueError`: サポートされていないファイル形式の場合
- `ImportError`: 必要なライブラリがインストールされていない場合

### `get_supported_extensions() -> list[str]`

サポートされているファイル拡張子のリストを返します。

**戻り値:**
- `list[str]`: サポートされている拡張子のリスト（例: `[".txt", ".md", ".docx", ".pdf"]`）

## 使用例

```python
from modules.file_reader import read_file, get_supported_extensions

# テキストファイルを読み込む
text = read_file("input/sample.txt")
print(text)

# Markdownファイルを読み込む
markdown = read_file("input/document.md")

# Word文書を読み込む
docx_text = read_file("input/report.docx")

# PDFを読み込む
pdf_text = read_file("input/manual.pdf")

# サポートされている拡張子を確認
extensions = get_supported_extensions()
print(f"対応形式: {extensions}")
```

## 依存ライブラリ

- `python-docx` - Word文書の読み込みに使用
- `PyMuPDF` - PDFの読み込みに使用

```bash
pip install python-docx PyMuPDF
```
