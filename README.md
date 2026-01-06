# echo-me

音声/MDファイルからブログ・SNS投稿を自動生成するシステム

## System Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Google Drive   │     │    Cloud Run     │     │  Google Drive   │
│  (Input Folder) │────▶│   (echo-me)      │────▶│ (Output Folder) │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               │ Claude API
                               ▼
                        ┌──────────────────┐
                        │   Anthropic API  │
                        └──────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                      Cloud Scheduler                              │
│                   (毎時実行: 0 * * * *)                           │
└──────────────────────────────────────────────────────────────────┘
```

## Features

- Google Driveフォルダの自動監視
- 複数形式の入力ファイルに対応（.txt, .md, .docx, .pdf）
- Claude APIを使用して3種類のコンテンツを自動生成:
  - **blog.md**: 構造化されたブログ記事
  - **x_post.txt**: X(Twitter)投稿（280文字以内、ハッシュタグ付き）
  - **linkedin_post.txt**: LinkedIn投稿
- Cloud Run + Cloud Schedulerによる定期自動処理
- Cloud Buildによる自動デプロイ（CI/CD）
- **承認ワークフロー**: 承認済みフォルダからNotionへ自動投稿
- **Discord通知**:
  - レビュー待ちファイル作成時
  - Notion投稿成功時（ページURLリンク付き）
  - エラー発生時（処理エラー、Notion投稿エラー）

## Cost Estimate

月額コスト: 約1,000〜1,200円

| サービス | 詳細 | 月額目安 |
|----------|------|----------|
| Cloud Run | 毎時実行、512MB、最大9分 | 〜500円 |
| Cloud Scheduler | 1ジョブ | 無料枠内 |
| Secret Manager | 4シークレット | 〜100円 |
| Anthropic API | Claude Sonnet、ファイル数による | 〜500円 |
| **合計** | | **約1,000〜1,200円** |

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

## Local Development

### OAuth認証の準備

1. [Google Cloud Console](https://console.cloud.google.com/)でプロジェクトを作成
2. Google Drive APIを有効化
3. OAuth同意画面を設定（外部、テストユーザーに自分を追加）
4. 認証情報 → OAuthクライアントIDを作成（デスクトップアプリ）
5. `credentials.json`をダウンロードして`src/`に配置

### ローカルテスト実行

```bash
python src/local_test.py
```

初回実行時はOAuth認証のためブラウザが開きます。認証後は`token.json`が保存され、次回以降は自動的に認証されます。

## Cloud Run Deployment

### 1. GCPプロジェクトの設定

```bash
# プロジェクトを設定
gcloud config set project YOUR_PROJECT_ID

# 必要なAPIを有効化
gcloud services enable drive.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 2. Secret Managerに認証情報を登録

```bash
# OAuth credentials.jsonを登録
gcloud secrets create gdrive-credentials \
    --data-file=src/credentials.json

# OAuth token.jsonを登録（ローカルで認証後）
gcloud secrets create gdrive-token \
    --data-file=src/token.json

# 環境変数を登録
echo -n "your_anthropic_api_key" | gcloud secrets create anthropic-api-key --data-file=-
echo -n "your_discord_webhook_url" | gcloud secrets create discord-webhook-url --data-file=-
```

### 3. Dockerイメージをビルド・デプロイ

```bash
# Cloud Buildでイメージをビルド
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/echo-me

# Cloud Runにデプロイ
gcloud run deploy echo-me \
    --image gcr.io/YOUR_PROJECT_ID/echo-me \
    --region asia-northeast1 \
    --memory 512Mi \
    --timeout 540s \
    --set-env-vars "GDRIVE_INPUT_FOLDER_ID=YOUR_INPUT_FOLDER_ID,GDRIVE_OUTPUT_FOLDER_ID=YOUR_OUTPUT_FOLDER_ID" \
    --set-secrets "ANTHROPIC_API_KEY=anthropic-api-key:latest,DISCORD_WEBHOOK_URL=discord-webhook-url:latest,/secrets-cred/credentials.json=gdrive-credentials:latest,/secrets-token/token.json=gdrive-token:latest" \
    --no-allow-unauthenticated
```

### 4. Cloud Schedulerの設定

```bash
# サービスアカウントにCloud Run起動権限を付与
gcloud run services add-iam-policy-binding echo-me \
    --region asia-northeast1 \
    --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/run.invoker"

# スケジューラージョブを作成（毎時実行）
gcloud scheduler jobs create http echo-me-scheduler \
    --schedule="0 * * * *" \
    --uri="https://echo-me-XXXXX-an.a.run.app" \
    --http-method=POST \
    --location=asia-northeast1 \
    --oidc-service-account-email=YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com
```

## CI/CD Automation

mainブランチへのpushで自動的にビルド・デプロイが実行されます。

### 仕組み

1. `git push origin main` を実行
2. Cloud Build Triggerが検知
3. `cloudbuild.yaml`に基づいてDockerイメージをビルド
4. Container Registry (`gcr.io/echo-me-483413/echo-me`) にプッシュ
5. Cloud Run (`asia-southeast1`) に自動デプロイ

### Cloud Build Triggerの設定

```bash
# GitHubリポジトリと連携したトリガーを作成
gcloud builds triggers create github \
    --repo-name=echo-me \
    --repo-owner=JinJin48 \
    --branch-pattern=^main$ \
    --build-config=cloudbuild.yaml
```

### 手動ビルド

```bash
# 手動でCloud Buildを実行
gcloud builds submit --config=cloudbuild.yaml
```

## Environment Variables

| 変数名 | 説明 | 必須 |
|--------|------|------|
| `ANTHROPIC_API_KEY` | Claude APIキー | ○ |
| `GDRIVE_INPUT_FOLDER_ID` | Google Drive入力フォルダID | ○ |
| `GDRIVE_OUTPUT_FOLDER_ID` | Google Drive出力フォルダID | ○ |
| `DISCORD_WEBHOOK_URL` | Discord通知用Webhook URL | - |
| `NOTION_API_KEY` | Notion APIキー | - |
| `NOTION_DATABASE_ID` | Notion データベースID | - |

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
├── main.py                    # Cloud Run用エントリーポイント
├── Dockerfile                 # Cloud Run用Dockerイメージ定義
├── Procfile                   # Cloud Run用プロセス定義
├── cloudbuild.yaml            # Cloud Build CI/CD設定
├── CLAUDE.md                  # Claude Code用コンテキスト
├── src/
│   ├── local_test.py          # ローカルテスト用スクリプト
│   ├── cloud_function.py      # Cloud Run用コア処理
│   └── modules/
│       ├── file_reader/       # ファイル読み込みモジュール
│       ├── llm_processor/     # Claude API呼び出しモジュール
│       ├── content_formatter/ # 出力フォーマットモジュール
│       ├── gdrive_watcher/    # Google Drive監視
│       ├── notifier/          # Discord通知
│       ├── notion_publisher.py # Notion投稿モジュール
│       └── approval_watcher.py # 承認済みファイル監視
├── .env                       # API Key（Git管理外）
├── .env.example               # 環境変数のサンプル
├── .gitignore
├── requirements.txt
└── README.md
```

## Security Notes

- `credentials.json`および`token.json`は**絶対にGitHubにプッシュしないでください**
- これらのファイルは`.gitignore`に登録されています
- 本番環境ではSecret Managerを使用して認証情報を管理

## Requirements

- Python 3.9+
- Anthropic API Key
- Google Cloud Platform アカウント
- Discord Webhook URL（オプション、エラー通知用）

## License

MIT
