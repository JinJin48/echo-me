# echo-me

音声/MDファイルからブログ・SNS投稿を自動生成するシステム

## Features

- Google Driveフォルダの自動監視
- 複数形式の入力ファイルに対応（.txt, .md, .docx, .pdf）
- Claude APIを使用して3種類のコンテンツを自動生成:
  - **blog.md**: 構造化されたブログ記事
  - **x_post.txt**: X(Twitter)投稿（280文字以内、ハッシュタグ付き）
  - **linkedin_post.txt**: LinkedIn投稿
- Cloud Functionsによる自動処理
- エラー時のDiscord通知

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
# .envファイルを編集してAPIキーとフォルダIDを設定
```

## Usage

### ローカルテスト実行

Google Driveの入力フォルダからファイルを取得し、処理結果を出力フォルダにアップロードします。

```bash
python src/local_test.py
```

初回実行時はOAuth認証のためブラウザが開きます。認証後は`token.json`が保存され、次回以降は自動的に認証されます。

### 処理フロー

1. Google Driveの入力フォルダから未処理ファイルを取得
2. Claude APIでコンテンツ生成（ブログ、X、LinkedIn）
3. 生成結果をGoogle Driveの出力フォルダにアップロード
4. 処理済みファイルを`_processed`でリネーム

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

## Project Structure

```
echo-me/
├── CLAUDE.md                  # Claude Code用コンテキスト
├── src/
│   ├── local_test.py          # ローカルテスト用スクリプト
│   ├── cloud_function.py      # Cloud Functions用エントリーポイント
│   └── modules/
│       ├── file_reader/       # ファイル読み込みモジュール
│       ├── llm_processor/     # Claude API呼び出しモジュール
│       ├── content_formatter/ # 出力フォーマットモジュール
│       ├── gdrive_watcher/    # Google Drive監視
│       └── notifier/          # Discord通知
├── .env                       # API Key（Git管理外）
├── .env.example               # 環境変数のサンプル
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup

### 1. Google Cloud Consoleでの設定

1. [Google Cloud Console](https://console.cloud.google.com/)でプロジェクトを作成
2. Google Drive APIを有効化
3. OAuth同意画面を設定（外部、テストユーザーに自分を追加）
4. 認証情報 → OAuthクライアントIDを作成（デスクトップアプリ）
5. `credentials.json`をダウンロードして`src/`に配置

### 2. Google Driveフォルダの設定

1. Google Driveで入力/出力フォルダを作成
2. フォルダURLからIDを取得（`https://drive.google.com/drive/folders/FOLDER_ID`）
3. `.env`にフォルダIDを設定

### 3. 環境変数の設定

```bash
# .envファイル
ANTHROPIC_API_KEY=your_api_key
GDRIVE_INPUT_FOLDER_ID=your_input_folder_id
GDRIVE_OUTPUT_FOLDER_ID=your_output_folder_id
DISCORD_WEBHOOK_URL=your_webhook_url  # オプション
```

> **セキュリティ注意**
> - `credentials.json`および`token.json`は**絶対にGitHubにプッシュしないでください**
> - これらのファイルは`.gitignore`に登録されています

## Cloud Functions デプロイ

### 1. GCPプロジェクトの設定

```bash
# GCPプロジェクトを作成・選択
gcloud projects create echo-me-project
gcloud config set project echo-me-project

# 必要なAPIを有効化
gcloud services enable drive.googleapis.com
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
```

### 2. サービスアカウントの作成

```bash
# サービスアカウントを作成
gcloud iam service-accounts create echo-me-sa \
    --display-name="echo-me Service Account"

# Google Driveフォルダをサービスアカウントに共有
# echo-me-sa@echo-me-project.iam.gserviceaccount.com
```

### 3. Cloud Functionsへのデプロイ

```bash
gcloud functions deploy echo-me \
    --runtime python311 \
    --trigger-http \
    --entry-point http_handler \
    --source src/ \
    --set-env-vars ANTHROPIC_API_KEY=xxx,GDRIVE_INPUT_FOLDER_ID=xxx,GDRIVE_OUTPUT_FOLDER_ID=xxx,DISCORD_WEBHOOK_URL=xxx \
    --memory 512MB \
    --timeout 540s
```

### 4. スケジュール実行の設定（オプション）

```bash
gcloud scheduler jobs create http echo-me-scheduler \
    --schedule="0 * * * *" \
    --uri="https://REGION-PROJECT_ID.cloudfunctions.net/echo-me" \
    --http-method=POST
```

## Requirements

- Python 3.9+
- Anthropic API Key
- Google Cloud Platform アカウント
- Discord Webhook URL（オプション、エラー通知用）

## License

MIT
