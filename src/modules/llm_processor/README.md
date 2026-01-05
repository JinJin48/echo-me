# llm_processor モジュール

Claude APIを使用してコンテンツを生成するモジュール

## 概要

このモジュールは、Anthropic Claude APIを使用して、入力テキストからブログ記事、X(Twitter)投稿、LinkedIn投稿を生成します。

## コンテンツタイプ

| タイプ | 説明 | 最大トークン |
|--------|------|--------------|
| `blog` | 技術ブログ記事（Markdown形式） | 4096 |
| `x_post` | X(Twitter)投稿（280文字以内） | 512 |
| `linkedin` | LinkedIn投稿（プロフェッショナルトーン） | 2048 |

## 関数・クラス一覧

### `generate_content(text: str, content_type: ContentType, api_key: str | None = None, model: str = DEFAULT_MODEL) -> str`

コンテンツを生成する関数インターフェース。

**引数:**
- `text` (str): 入力テキスト
- `content_type` (ContentType): 生成するコンテンツのタイプ（"blog", "x_post", "linkedin"）
- `api_key` (str | None): Anthropic APIキー。Noneの場合は環境変数から取得
- `model` (str): 使用するモデル名（デフォルト: `claude-sonnet-4-20250514`）

**戻り値:**
- `str`: 生成されたコンテンツ

### `get_content_types() -> list[str]`

利用可能なコンテンツタイプのリストを返します。

**戻り値:**
- `list[str]`: コンテンツタイプのリスト（`["blog", "x_post", "linkedin"]`）

### `class LLMProcessor`

Claude APIを使用してコンテンツを生成するクラス。

#### `__init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL)`

LLMProcessorを初期化します。

**引数:**
- `api_key` (str | None): Anthropic APIキー
- `model` (str): 使用するモデル名

**例外:**
- `ValueError`: APIキーが設定されていない場合

#### `generate_content(self, text: str, content_type: ContentType) -> str`

指定されたタイプのコンテンツを生成します。

**引数:**
- `text` (str): 入力テキスト
- `content_type` (ContentType): 生成するコンテンツのタイプ

**戻り値:**
- `str`: 生成されたコンテンツ

## 使用例

```python
from modules.llm_processor import generate_content, LLMProcessor, get_content_types

# 関数インターフェースを使用（シンプルな用途向け）
blog = generate_content(
    text="今日はSAPのS/4HANA移行について議論しました...",
    content_type="blog"
)
print(blog)

# クラスインターフェースを使用（複数コンテンツ生成向け）
processor = LLMProcessor()

blog = processor.generate_content(input_text, "blog")
x_post = processor.generate_content(input_text, "x_post")
linkedin = processor.generate_content(input_text, "linkedin")

# 利用可能なコンテンツタイプを確認
types = get_content_types()
print(f"利用可能なタイプ: {types}")
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `ANTHROPIC_API_KEY` | Anthropic APIキー |

## 依存ライブラリ

- `anthropic` - Claude API クライアント
- `python-dotenv` - 環境変数の読み込み

```bash
pip install anthropic python-dotenv
```
