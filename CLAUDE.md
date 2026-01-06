# echo-me Project Context

## Overview
echo-meは、音声ファイルやMarkdownファイルからブログ・SNS投稿を自動生成するシステムです。

### 背景
- 会議の議事録や技術トピックを効率的にコンテンツ化したい
- 複数のプラットフォーム（ブログ、X、LinkedIn）向けに最適化された投稿を生成
- SAP/IT技術系のコンテンツを発信するワークフローを自動化

## Current Status

### Phase 1: ローカル実行 ✅ 完了
- 複数形式対応（.txt, .md, .docx, .pdf）
- Claude APIによるコンテンツ生成

### Phase 2: 自動化強化 ✅ 完了
- Google Drive連携によるフォルダ監視・ファイル自動取得
- Cloud Run + Cloud Schedulerによる定期自動処理（15分ごと）
- Discord Webhookによる通知（生成完了、エラー）
- Secret Managerによる認証情報管理
- Cloud Build CI/CD（mainブランチへのpushで自動デプロイ）

### Phase 3: Notion連携 ✅ 完了
- [x] Notion API連携によるレビューワークフロー
- [x] 承認済みファイルのNotion自動投稿
- [x] Discord通知（投稿成功/エラー）

### Phase 4: 配信自動化（予定）
- [ ] LinkedIn API連携による自動投稿
- [ ] X API連携による自動投稿
- [ ] SAP Community連携

### Phase 5: AI強化（予定）
- [ ] コンテンツの品質スコアリング
- [ ] トレンド分析による最適投稿時間提案
- [ ] マルチ言語対応（日英）

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

## Technical Decisions

### デプロイ方式: Dockerfile（Buildpacksから変更）
- **理由**: Buildpacksでは依存関係のインストールに問題が発生
- **採用**: `python:3.11-slim`ベースのDockerfile
- `functions-framework`を使用してHTTPハンドラーを起動

### 認証方式: OAuth + Secret Manager
- Secret Managerからマウント
  - `/secrets-cred/credentials.json`
  - `/secrets-token/token.json`
- サービスアカウントではなくOAuth認証を使用（個人のGoogle Driveアクセスのため）

### CI/CD: Cloud Build + GitHub連携
- mainブランチへのpushで自動ビルド・デプロイ
- `cloudbuild.yaml`でビルド・デプロイ手順を定義
- Container Registry: `gcr.io/$PROJECT_ID/echo-me`
- デプロイ先: Cloud Run (`asia-southeast1`)

### 月額コスト: 約1,000〜1,200円
| サービス | 月額目安 |
|----------|----------|
| Cloud Run | 〜500円 |
| Secret Manager | 〜100円 |
| Anthropic API | 〜500円 |

## File Structure

```
echo-me/
├── main.py                    # Cloud Run用エントリーポイント
├── Dockerfile                 # Cloud Run用Dockerイメージ定義
├── Procfile                   # Cloud Run用プロセス定義
├── cloudbuild.yaml            # Cloud Build CI/CD設定
├── CLAUDE.md                  # このファイル（Claude Code用コンテキスト）
├── src/
│   ├── cloud_function.py      # Cloud Run用コア処理
│   └── modules/
│       ├── __init__.py
│       ├── file_reader/       # ファイル読み込みモジュール
│       │   ├── __init__.py
│       │   ├── reader.py
│       │   └── README.md
│       ├── llm_processor/     # LLM処理モジュール
│       │   ├── __init__.py
│       │   ├── processor.py
│       │   └── README.md
│       ├── content_formatter/ # 出力フォーマットモジュール
│       │   ├── __init__.py
│       │   ├── formatter.py
│       │   └── README.md
│       ├── gdrive_watcher/    # Google Drive監視モジュール
│       │   ├── __init__.py
│       │   ├── watcher.py
│       │   └── README.md
│       ├── notifier/          # 通知モジュール
│       │   ├── __init__.py
│       │   ├── discord.py
│       │   └── README.md
│       ├── notion_publisher.py    # Notion投稿モジュール
│       └── approval_watcher.py    # 承認済みファイル監視モジュール
├── .env.example               # 環境変数のサンプル
├── .gitignore
├── requirements.txt
└── README.md
```

## Google Drive Folder Structure

```
Google Drive/
├── 100. Input/                    # 入力フォルダ（GDRIVE_INPUT_FOLDER_ID）
│   └── *.md, *.txt, etc.          # 未処理ファイル → 処理後 _processed_ プレフィックス付与
├── 200. Awaiting review/          # 出力フォルダ（GDRIVE_OUTPUT_FOLDER_ID）
│   └── *_blog.md, *_linkedin.txt, *_x_post.txt
├── 300. Approved/                 # 承認済みフォルダ
│   ├── Notion/                    # Notion投稿待ち（GDRIVE_APPROVED_FOLDER_ID）→ 自動投稿
│   ├── LinkedIn/                  # LinkedIn投稿待ち → 手動投稿
│   └── X/                         # X投稿待ち → 手動投稿
└── 400. Posted/                   # 投稿済みフォルダ
    └── Notion/                    # Notion投稿完了（GDRIVE_POSTED_FOLDER_ID）
```

## Modules

### file_reader

ファイル読み込みを担当するモジュール。

| 関数 | 引数 | 戻り値 | 説明 |
|------|------|--------|------|
| `read_file(filepath)` | `filepath: str` | `str` | ファイルからテキストを抽出 |
| `get_supported_extensions()` | なし | `list[str]` | 対応拡張子リストを返す |

**対応形式:** `.txt`, `.md`, `.docx`, `.pdf`

**PDF処理仕様:**
- PyMuPDFでテキスト抽出
- テキストが10文字未満の場合は`ValueError`を返す（OCR未処理と判断）
- エラーメッセージ: 「このPDFはOCR処理されていません。PDFelementなどでOCR処理してから再度お試しください。」

### llm_processor

Claude APIを使用したコンテンツ生成を担当するモジュール。

| 関数/クラス | 引数 | 戻り値 | 説明 |
|-------------|------|--------|------|
| `generate_content(text, content_type)` | `text: str`, `content_type: str` | `str` | コンテンツを生成 |
| `get_content_types()` | なし | `list[str]` | 利用可能なタイプを返す |
| `LLMProcessor` | クラス | - | API呼び出しを管理 |

**content_type:** `"blog"`, `"x_post"`, `"linkedin"`

### content_formatter

出力ファイルの生成を担当するモジュール。

| 関数 | 引数 | 戻り値 | 説明 |
|------|------|--------|------|
| `save_outputs(blog, x_post, linkedin, output_dir)` | 各コンテンツ文字列 | `OutputPaths` | 3ファイルを一括保存 |
| `save_single_output(content, output_dir, filename)` | 内容とパス | `str` | 単一ファイルを保存 |

### gdrive_watcher

Google Drive APIを使用したフォルダ監視モジュール。

| 関数/クラス | 引数 | 戻り値 | 説明 |
|-------------|------|--------|------|
| `GDriveWatcher` | クラス | - | Google Driveフォルダ監視 |
| `list_new_files()` | なし | `list[dict]` | 未処理ファイル一覧 |
| `download_file(file_id, local_path)` | ID, パス | `str` | ファイルダウンロード |
| `upload_file(local_path, filename)` | パス, ファイル名 | `str` | ファイルアップロード |
| `mark_as_processed(file_id, name)` | ID, 名前 | なし | 処理済みマーク |

**認証情報パス（Cloud Run）:**
- `/secrets-cred/credentials.json`
- `/secrets-token/token.json`

**環境変数:**
- `GDRIVE_INPUT_FOLDER_ID`: 入力フォルダID
- `GDRIVE_OUTPUT_FOLDER_ID`: 出力フォルダID

### notifier

Discord Webhookを使用した通知モジュール。

| 関数/クラス | 引数 | 戻り値 | 説明 |
|-------------|------|--------|------|
| `DiscordNotifier` | クラス | - | Discord通知管理 |
| `notify_error(error, context, file_name)` | 例外, コンテキスト, ファイル名 | `bool` | エラー通知送信 |
| `notify_review(file_names, source_file, output_folder_id)` | ファイル名リスト, 元ファイル, フォルダID | `bool` | レビュー待ち通知 |
| `notify_notion_success(page_title, page_id, source_file)` | タイトル, ページID, 元ファイル | `bool` | Notion投稿成功通知 |
| `notify_notion_error(error, file_name)` | 例外, ファイル名 | `bool` | Notion投稿エラー通知 |

**環境変数:**
- `DISCORD_WEBHOOK_URL`: Discord WebhookのURL

**Discord通知タイミング:**
| タイミング | 関数 | 内容 |
|------------|------|------|
| レビュー待ちファイル作成 | `notify_review` | 生成されたファイル名、Google Driveリンク |
| Notion投稿成功 | `notify_notion_success` | ページタイトル、NotionページURL |
| Notion投稿エラー | `notify_notion_error` | エラータイプ、メッセージ |
| 処理エラー | `notify_error` | エラータイプ、メッセージ、スタックトレース |

**通知仕様:**
- Webhook未設定時はログ出力のみ（エラーにはならない）

### notion_publisher

Notion APIを使用したコンテンツ投稿モジュール。

| 関数/クラス | 引数 | 戻り値 | 説明 |
|-------------|------|--------|------|
| `NotionPublisher` | クラス | - | Notion投稿管理 |
| `create_page(title, content, properties)` | タイトル, Markdown, プロパティ | `str` | ページ作成、ページIDを返す |
| `markdown_to_notion_blocks(markdown)` | Markdown文字列 | `list[dict]` | MarkdownをNotionブロックに変換 |
| `post_to_notion(title, content)` | タイトル, Markdown | `str` | 関数インターフェース |

**環境変数:**
- `NOTION_API_KEY`: Notion APIキー
- `NOTION_DATABASE_ID`: 投稿先データベースID

**対応Markdown記法:**
- 見出し（h1, h2, h3）
- 段落
- 箇条書き、番号付きリスト
- コードブロック
- 引用
- 太字、イタリック、インラインコード、リンク

### approval_watcher

承認済みファイルを監視してNotionに投稿するモジュール。

| 関数/クラス | 引数 | 戻り値 | 説明 |
|-------------|------|--------|------|
| `ApprovalWatcher` | クラス | - | 承認ワークフロー管理 |
| `list_approved_files()` | なし | `list[dict]` | 承認済みファイル一覧 |
| `move_to_posted(file_id)` | ファイルID | なし | 投稿済みフォルダに移動 |
| `process_approved_files()` | なし | `list[dict]` | 承認済みファイルを処理 |

**処理フロー:**
1. 承認済みフォルダ（300. Approved）からファイルを取得
2. Notionデータベースにページを作成
3. Discord通知（成功/エラー）
4. 投稿済みフォルダ（400. Posted -> Notion）に移動

## File Descriptions

| ファイル | 役割 |
|----------|------|
| `main.py` | Cloud Run用エントリーポイント |
| `Dockerfile` | Cloud Run用Dockerイメージ定義 |
| `Procfile` | Cloud Run用プロセス定義（functions-framework起動） |
| `cloudbuild.yaml` | Cloud Build CI/CD設定（自動ビルド・デプロイ） |
| `src/cloud_function.py` | Cloud Run用コア処理 |
| `src/modules/file_reader/` | 各種ファイル形式からテキスト抽出 |
| `src/modules/llm_processor/` | Claude APIを使用したコンテンツ生成 |
| `src/modules/content_formatter/` | 出力ファイルの生成・保存 |
| `src/modules/gdrive_watcher/` | Google Drive監視・ファイル取得 |
| `src/modules/notifier/` | Discord Webhook通知 |
| `src/modules/notion_publisher.py` | Notion APIを使用したページ作成 |
| `src/modules/approval_watcher.py` | 承認済みファイルの監視・Notion投稿 |

## Input File Types

| 種類 | 形式 | 内容 |
|------|------|------|
| A | テキスト/MD | Plaud AIによる文字起こしMTG議事 |
| B | MD | Google Drive格納のSAP/IT技術系トピック |
| C | DOCX | Word文書形式のドキュメント |
| D | PDF | PDF形式のドキュメント（※OCR処理済みのみ） |

**PDF注意事項:** OCR処理済みPDFのみ対応。画像PDFはPDFelementなどで事前にOCR処理が必要。

## Output Files

| ファイル | 形式 | 説明 |
|----------|------|------|
| `blog.md` | Markdown | ブログ記事（構造化された長文） |
| `x_post.txt` | Plain Text | X(Twitter)投稿（280文字以内、ハッシュタグ付き） |
| `linkedin_post.txt` | Plain Text | LinkedIn投稿用テキスト |

## Development Rules

### コーディング規約
- Python 3.9+を使用
- PEP 8スタイルガイドに準拠
- 型ヒントを積極的に使用
- docstringはGoogle styleで記述
- エラーハンドリングは適切に実装

### 環境変数
- APIキーは必ず`.env`ファイルで管理
- `.env`ファイルは絶対にコミットしない
- フォルダIDやWebhook URLもハードコーディング禁止

### セキュリティ注意事項
- 認証情報はSecret Managerで管理
- APIキーやフォルダIDは環境変数で設定
- 機密情報はハードコーディング禁止

**必須環境変数:**
| 変数名 | 説明 |
|--------|------|
| `ANTHROPIC_API_KEY` | Claude APIキー |
| `GDRIVE_INPUT_FOLDER_ID` | Google Drive入力フォルダID |
| `GDRIVE_OUTPUT_FOLDER_ID` | Google Drive出力フォルダID |
| `GDRIVE_APPROVED_FOLDER_ID` | 承認済みフォルダID（Notion連携時に必要） |
| `GDRIVE_POSTED_FOLDER_ID` | Notion投稿済みフォルダID（Notion連携時に必要） |
| `DISCORD_WEBHOOK_URL` | Discord通知用Webhook URL（オプション） |
| `NOTION_API_KEY` | Notion APIキー（オプション、Notion連携時に必要） |
| `NOTION_DATABASE_ID` | Notion投稿先データベースID（オプション） |

### 使用API
- Anthropic Claude API
- モデル: `claude-sonnet-4-20250514`

## Usage

### Cloud Runデプロイ

```bash
# Dockerイメージをビルド
gcloud builds submit --tag gcr.io/PROJECT_ID/echo-me

# Cloud Runにデプロイ
gcloud run deploy echo-me \
    --image gcr.io/PROJECT_ID/echo-me \
    --region asia-northeast1 \
    --memory 512Mi \
    --timeout 540s \
    --set-env-vars "GDRIVE_INPUT_FOLDER_ID=xxx,GDRIVE_OUTPUT_FOLDER_ID=xxx" \
    --set-secrets "ANTHROPIC_API_KEY=anthropic-api-key:latest,DISCORD_WEBHOOK_URL=discord-webhook-url:latest,/secrets-cred/credentials.json=gdrive-credentials:latest,/secrets-token/token.json=gdrive-token:latest" \
    --no-allow-unauthenticated
```

### 処理フロー

**コンテンツ生成フロー:**
1. Google Driveの入力フォルダから未処理ファイルを取得
2. Claude APIでコンテンツ生成（ブログ、X、LinkedIn）
3. 生成結果をGoogle Driveの出力フォルダにアップロード
4. 処理済みファイルに`_processed_`プレフィックスを付与
5. Discord通知（レビュー待ちファイル作成）

**Notion投稿フロー:**
1. 承認済みフォルダ（300. Approved）からファイルを取得
2. Notionデータベースにページを作成
3. Discord通知（成功/エラー）
4. 投稿済みフォルダ（400. Posted -> Notion）に移動

## Security Policy

### 機密情報の管理方針
- .envファイルは作成しない
- 全ての機密情報（API Key、認証情報、フォルダIDなど）はGCP Secret Managerに登録
- ローカル開発時もSecret Managerを参照（.envファイル不使用）
- ハードコーディング禁止

### 開発時の認証
```bash
gcloud auth application-default login
```

### Secret Manager使用例
```python
from google.cloud import secretmanager

def get_secret(secret_id, project_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
```
