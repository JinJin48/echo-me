# echo-me

音声/MDファイルからブログ・SNS投稿を自動生成するシステム

## Features

- 複数形式の入力ファイルに対応（.txt, .md, .docx, .pdf）
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

### 通常実行

```bash
# テキストファイルから生成
python src/main.py input/sample.txt

# Markdownファイルから生成
python src/main.py input/sample.md

# Word文書から生成
python src/main.py input/document.docx

# PDFから生成（※OCR処理済みのみ）
python src/main.py input/manual.pdf

# 出力ディレクトリを指定
python src/main.py input/sample.txt -o my_output

# タイムスタンプなしで出力
python src/main.py input/sample.txt --no-timestamp
```

### バックグラウンド実行（推奨）

長時間の処理を行う場合は、バックグラウンド実行を推奨します。

```powershell
# Windows PowerShell
Start-Process -NoNewWindow python -ArgumentList "src/main.py", "input/sample.txt"
```

```bash
# Linux/Mac
nohup python src/main.py input/sample.txt > output.log 2>&1 &
```

## Supported Input Formats

| 形式 | 拡張子 | 備考 |
|------|--------|------|
| プレーンテキスト | .txt | - |
| Markdown | .md | - |
| Microsoft Word | .docx | python-docx使用 |
| PDF | .pdf | OCR処理済みのみ対応 |

### PDF対応の注意事項

- OCR処理済みPDFのみ対応。画像PDFは事前にOCR処理が必要。
- テキストが抽出できない場合（10文字未満）はエラーとなります。
- 推奨OCRツール: PDFelement、Adobe Acrobat など

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
│   ├── main.py                # メイン実行スクリプト
│   └── modules/
│       ├── file_reader/       # ファイル読み込みモジュール
│       ├── llm_processor/     # Claude API呼び出しモジュール
│       └── content_formatter/ # 出力フォーマットモジュール
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
