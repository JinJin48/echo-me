# echo-me

音声/MDファイルからブログ・SNS投稿を自動生成するシステム

## Features

- 音声文字起こし（Plaud AI）やMarkdownファイルを入力として受け付け
- Claude APIを使用して3種類のコンテンツを自動生成:
  - **blog.md**: 構造化されたブログ記事
  - **x_post.txt**: X(Twitter)投稿（280文字以内、ハッシュタグ付き）
  - **linkedin_post.txt**: LinkedIn投稿

## Installation

```bash
# リポジトリをクローン
git clone https://github.com/JinJin48/echo-me.git
cd echo-me

# 仮想環境を作成（推奨）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt

# 環境変数を設定
cp .env.example .env
# .envファイルを編集してANTHROPIC_API_KEYを設定
```

## Usage

```bash
# テキストファイルから生成
python src/content_generator.py input/sample.txt

# Markdownファイルから生成
python src/content_generator.py input/sample.md

# 出力ディレクトリを指定
python src/content_generator.py input/sample.txt -o my_output
```

## Output

出力は `output/YYYYMMDD_HHMMSS/` ディレクトリに生成されます:

```
output/
└── 20250105_123456/
    ├── blog.md
    ├── x_post.txt
    └── linkedin_post.txt
```

## Project Structure

```
echo-me/
├── CLAUDE.md                  # Claude Code用コンテキスト
├── src/
│   └── content_generator.py   # メインスクリプト
├── input/                     # 入力ファイル置き場
├── output/                    # 出力ファイル置き場
├── .env                       # API Key（Git管理外）
├── .env.example               # 環境変数のサンプル
├── .gitignore
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.9+
- Anthropic API Key

## License

MIT
