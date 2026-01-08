# echo-me

音声/MDファイルからブログ・SNS投稿を自動生成するシステム

## System Flow

```
【INPUT】
┌──────────────────────┐
│    Google Drive      │
│   100. Input/        │
│  (.md/.txt/.pdf)     │
└──────────┬───────────┘
           │
           ↓
【TRIGGER】
┌──────────────────────┐
│   Cloud Scheduler    │
│     (15分ごと)        │
└──────────┬───────────┘
           │
           ↓
【PROCESSING】
┌─────────────────────────────────────────┐
│              Cloud Run                  │
│  1. Google Driveから取得                 │
│  2. Claude APIで加工                     │
│  3. 3種類のコンテンツ生成                 │
│     - blog.md / linkedin.txt / x_post.txt│
└──────────┬──────────────────────────────┘
           │
           ↓
【OUTPUT】
┌──────────────────────┐
│    Google Drive      │
│ 200. Awaiting review │
└──────────┬───────────┘
           │
           ↓
【REVIEW - 人による承認】
┌─────────────────────────────────────────┐
│  承認フォルダへ移動                       │
│  - 300. Approved/Notion                 │
│  - 300. Approved/LinkedIn               │
│  - 300. Approved/X                      │
└──────────┬──────────────────────────────┘
           │
           ↓
【PUBLISH】
┌─────────────┬─────────────┬─────────────┐
│   Notion    │  LinkedIn   │      X      │
│  自動投稿 ✅ │  手動投稿    │   手動投稿   │
└─────────────┴─────────────┴─────────────┘

【投稿後】
┌──────────────────────┐
│ 400. Posted/Notion   │
└──────────────────────┘

【通知】
┌──────────────────────┐
│    Discord通知        │
│  - 生成完了           │
│  - Notion投稿結果     │
└──────────────────────┘
```

## Features

- **コンテンツ自動生成**: Claude APIで3種類のコンテンツを生成
  - blog.md（Notion用）
  - linkedin.txt（LinkedIn用）
  - x_post.txt（X/Twitter用）
- **RAGメタデータ**: 出力MDファイルにYAMLフロントマターを自動追加
- **入力形式**: .txt, .md, .docx, .pdf（OCR処理済み）
- **定期実行**: Cloud Run + Cloud Scheduler（15分ごと）
- **承認ワークフロー**: 人によるレビュー後、プラットフォームへ配信
- **自動投稿**:
  - Notion: 承認後に自動投稿 ✅
  - LinkedIn: 手動投稿（コンテンツ生成のみ）
  - X: 手動投稿（コンテンツ生成のみ）
- **Discord通知**: 生成完了、Notion投稿結果
- **CI/CD**: Cloud Buildによる自動デプロイ

## CLI Usage (Local)

ローカルでファイルを処理するCLIツール `echo-me.py` が利用可能です。

### 基本的な使い方

```bash
# 自動推測（ファイル名からメタデータを推測）
python echo-me.py meeting_20250108.txt

# 手動上書き
python echo-me.py input.txt --source "webinar" --type "summary" --topics "SAP,BTP"

# 出力先を指定
python echo-me.py input.txt --output ./my_output
```

### オプション

| オプション | 短縮形 | 説明 |
|-----------|--------|------|
| `--output` | `-o` | 出力ディレクトリ（デフォルト: output） |
| `--source` | `-s` | メタデータのsourceを手動指定 |
| `--type` | `-t` | メタデータのtypeを手動指定 |
| `--topics` | - | トピックタグをカンマ区切りで指定 |
| `--date` | - | 日付を手動指定（ISO形式: YYYY-MM-DD） |
| `--no-timestamp` | - | 出力ディレクトリにタイムスタンプを付けない |

## RAG Metadata

生成されたブログ記事（blog.md）にはYAMLフロントマターが自動追加されます。

### 出力例

```yaml
---
source: meeting
type: minutes
date: 2025-01-08
topics: [SAP, GAP]
original_file: meeting_20250108.txt
---

# ブログ記事の内容...
```

### ファイル名パターンによる自動推測

| パターン | source | type |
|----------|--------|------|
| `meeting_*` | meeting | minutes |
| `interview_*` | interview | transcript |
| `memo_*` | memo | note |
| `webinar_*` | webinar | summary |
| その他 | unknown | general |

## Cost Estimate

月額コスト: 約1,000〜1,200円

| サービス | 詳細 | 月額目安 |
|----------|------|----------|
| Cloud Run | 毎時実行、512MB、最大9分 | 〜500円 |
| Cloud Scheduler | 1ジョブ | 無料枠内 |
| Secret Manager | 4シークレット | 〜100円 |
| Anthropic API | Claude Sonnet、ファイル数による | 〜500円 |
| **合計** | | **約1,000〜1,200円** |

## Deployment

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
4. Container Registry (`gcr.io/$PROJECT_ID/echo-me`) にプッシュ
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
| `GDRIVE_APPROVED_FOLDER_ID` | 承認済みフォルダID | - |
| `GDRIVE_POSTED_FOLDER_ID` | Notion投稿済みフォルダID | - |
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
├── echo-me.py                 # ローカル用CLIツール
├── Dockerfile                 # Cloud Run用Dockerイメージ定義
├── Procfile                   # Cloud Run用プロセス定義
├── cloudbuild.yaml            # Cloud Build CI/CD設定
├── CLAUDE.md                  # Claude Code用コンテキスト
├── src/
│   ├── cloud_function.py      # Cloud Run用コア処理
│   └── modules/
│       ├── file_reader/       # ファイル読み込みモジュール
│       ├── llm_processor/     # Claude API呼び出しモジュール
│       ├── content_formatter/ # 出力フォーマットモジュール
│       ├── gdrive_watcher/    # Google Drive監視
│       ├── notifier/          # Discord通知
│       ├── notion_publisher.py    # Notion投稿モジュール
│       ├── approval_watcher.py    # 承認済みファイル監視
│       └── metadata_extractor.py  # RAGメタデータ抽出
├── .gitignore
├── requirements.txt
└── README.md
```

## Security Policy

### 機密情報の管理方針
- .envファイルは作成しない
- 全ての機密情報はGCP Secret Managerに登録
- ローカル開発時もSecret Managerを参照

## Requirements

- Python 3.9+
- Anthropic API Key
- Google Cloud Platform アカウント
- Discord Webhook URL（オプション、エラー通知用）

## License

MIT
