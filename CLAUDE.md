# echo-me Project Context

## Overview
echo-meは、音声ファイルやMarkdownファイルからブログ・SNS投稿を自動生成するシステムです。

### 背景
- 会議の議事録や技術トピックを効率的にコンテンツ化したい
- 複数のプラットフォーム（ブログ、X、LinkedIn）向けに最適化された投稿を生成
- SAP/IT技術系のコンテンツを発信するワークフローを自動化

## System Flow

```
【INPUT】
音声(Plaud) / MDファイル
       ↓
Google Drive → NotebookLM（手動）
       ↓
【PROCESSING】
Claude API（ブログ/X/LinkedIn形式生成）
       ↓
【REVIEW】
Notion（レビュー・承認）
       ↓
【OUTPUT】
SAP Community / LinkedIn / X / JSUG / ASUG
+ Notion公式（ポートフォリオ）
```

## File Structure

```
echo-me/
├── main.py                    # Cloud Run用エントリーポイント
├── CLAUDE.md                  # このファイル（Claude Code用コンテキスト）
├── src/
│   ├── local_test.py          # ローカルテスト用スクリプト（OAuth認証）
│   ├── cloud_function.py      # Cloud Run/Functions用コア処理
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
│       └── notifier/          # 通知モジュール
│           ├── __init__.py
│           ├── discord.py
│           └── README.md
├── .env                       # API Key（.gitignore対象）
├── .gitignore
├── requirements.txt
└── README.md
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

**環境変数:**
- `GDRIVE_INPUT_FOLDER_ID`: 入力フォルダID
- `GDRIVE_OUTPUT_FOLDER_ID`: 出力フォルダID

### notifier

Discord Webhookを使用したエラー通知モジュール。

| 関数/クラス | 引数 | 戻り値 | 説明 |
|-------------|------|--------|------|
| `DiscordNotifier` | クラス | - | Discord通知管理 |
| `send_error(error, context, file_name)` | 例外, コンテキスト, ファイル名 | `bool` | エラー通知送信 |
| `notify_error(error, context, file_name)` | 同上 | `bool` | 関数インターフェース |

**環境変数:**
- `DISCORD_WEBHOOK_URL`: Discord WebhookのURL

**エラー通知仕様:**
- エラー発生時のみ通知（成功時は通知なし）
- エラータイプ、メッセージ、スタックトレースを含む
- Webhook未設定時はログ出力のみ（エラーにはならない）

## File Descriptions

| ファイル | 役割 |
|----------|------|
| `main.py` | Cloud Run用エントリーポイント（Buildpacks用） |
| `src/local_test.py` | ローカルテスト用スクリプト（OAuth認証） |
| `src/cloud_function.py` | Cloud Run/Functions用コア処理 |
| `src/modules/file_reader/` | 各種ファイル形式からテキスト抽出 |
| `src/modules/llm_processor/` | Claude APIを使用したコンテンツ生成 |
| `src/modules/content_formatter/` | 出力ファイルの生成・保存 |
| `src/modules/gdrive_watcher/` | Google Drive監視・ファイル取得 |
| `src/modules/notifier/` | Discord Webhook通知 |
| `.env` | 環境変数（Git管理外） |

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
- **`credentials.json`と`token.json`はGit管理禁止**
- これらは機密情報を含むため、**絶対にGitHubに公開しない**
- `credentials.json`: Google Cloud OAuth クライアント認証情報
- `token.json`: OAuth認証後に生成されるアクセストークン
- これらのファイルは`.gitignore`に登録済み
- 万が一コミットした場合は、Google Cloud Consoleで認証情報を無効化し、新規発行すること
- 本番環境ではCloud FunctionsのSecret Managerを使用して認証情報を管理する

**必須環境変数:**
| 変数名 | 説明 |
|--------|------|
| `ANTHROPIC_API_KEY` | Claude APIキー |
| `GDRIVE_INPUT_FOLDER_ID` | Google Drive入力フォルダID |
| `GDRIVE_OUTPUT_FOLDER_ID` | Google Drive出力フォルダID |
| `DISCORD_WEBHOOK_URL` | Discord通知用Webhook URL（オプション） |

### 使用API
- Anthropic Claude API
- モデル: `claude-sonnet-4-20250514`

## Usage

### ローカルテスト実行

```bash
# Google Driveの入力フォルダからファイルを取得して処理
python src/local_test.py
```

初回実行時はOAuth認証のためブラウザが開きます。

### 処理フロー

1. Google Driveの入力フォルダから未処理ファイルを取得
2. Claude APIでコンテンツ生成（ブログ、X、LinkedIn）
3. 生成結果をGoogle Driveの出力フォルダにアップロード
4. 処理済みファイルを`_processed`でリネーム

## Development Phases

### Phase 1: ローカル実行 ✅
- 複数形式対応（.txt, .md, .docx, .pdf）
- Claude APIによるコンテンツ生成

### Phase 2: 自動化強化 ✅
- Google Drive連携によるフォルダ監視・ファイル自動取得
- Cloud Run/Functionsによる自動処理
- Discord Webhookによるエラー通知

### Phase 3: 配信自動化（予定）
- X API連携による自動投稿
- LinkedIn API連携による自動投稿
- SAP Community連携
- Notion API連携によるレビューワークフロー

### Phase 4: AI強化（予定）
- コンテンツの品質スコアリング
- トレンド分析による最適投稿時間提案
- マルチ言語対応（日英）
