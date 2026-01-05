# gdrive_watcher モジュール

Google Drive APIを使用してフォルダを監視し、ファイルを取得するモジュール

## 概要

このモジュールは、指定されたGoogle Driveフォルダを監視し、新規ファイルを検出・ダウンロードする機能を提供します。処理済みファイルはリネームによりマーキングされ、重複処理を防止します。

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `GDRIVE_INPUT_FOLDER_ID` | 監視対象の入力フォルダID |
| `GDRIVE_OUTPUT_FOLDER_ID` | 生成ファイルのアップロード先フォルダID |
| `GOOGLE_APPLICATION_CREDENTIALS` | サービスアカウントJSONファイルのパス（ローカル実行時） |

## 対応ファイル形式

| MIMEタイプ | 拡張子 |
|------------|--------|
| `text/plain` | .txt |
| `text/markdown` | .md |
| `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | .docx |
| `application/pdf` | .pdf |

## クラス・関数一覧

### `class GDriveWatcher`

Google Driveフォルダを監視するクラス。

#### `__init__(self, input_folder_id, output_folder_id, credentials_path)`

**引数:**
- `input_folder_id` (str | None): 監視する入力フォルダのID
- `output_folder_id` (str | None): 出力先フォルダのID
- `credentials_path` (str | None): サービスアカウント認証情報のパス

#### `list_new_files(self, processed_marker="_processed") -> list[dict]`

未処理ファイルを一覧取得します。

**戻り値:**
- `list[dict]`: ファイル情報のリスト（id, name, mimeType, createdTime）

#### `download_file(self, file_id, local_path) -> str`

ファイルをダウンロードします。

**引数:**
- `file_id` (str): ダウンロードするファイルのID
- `local_path` (str): 保存先のローカルパス

**戻り値:**
- `str`: 保存したファイルのパス

#### `upload_file(self, local_path, filename, folder_id, mime_type) -> str`

ファイルをアップロードします。

**戻り値:**
- `str`: アップロードしたファイルのID

#### `mark_as_processed(self, file_id, original_name) -> None`

ファイルを処理済みとしてマークします（`_processed`をファイル名に付与）。

### `get_new_files(input_folder_id, output_folder_id) -> list[dict]`

関数インターフェース。未処理ファイルを取得します。

## 使用例

```python
from modules.gdrive_watcher import GDriveWatcher

# 初期化（環境変数から設定を読み込み）
watcher = GDriveWatcher()

# 未処理ファイルを取得
new_files = watcher.list_new_files()
for file in new_files:
    print(f"新規ファイル: {file['name']}")

    # ファイルをダウンロード
    local_path = f"/tmp/{file['name']}"
    watcher.download_file(file['id'], local_path)

    # 処理後、ファイルをアップロード
    watcher.upload_file("output/blog.md", "blog.md")

    # 処理済みとしてマーク
    watcher.mark_as_processed(file['id'], file['name'])
```

## GCP設定手順

### 1. サービスアカウントの作成

```bash
# GCPプロジェクトでサービスアカウントを作成
gcloud iam service-accounts create echo-me-sa \
    --display-name="echo-me Service Account"

# キーを生成
gcloud iam service-accounts keys create credentials.json \
    --iam-account=echo-me-sa@PROJECT_ID.iam.gserviceaccount.com
```

### 2. Google Drive APIの有効化

1. GCPコンソールで「APIとサービス」→「ライブラリ」
2. 「Google Drive API」を検索して有効化

### 3. フォルダの共有設定

1. Google Driveで入力/出力フォルダを作成
2. サービスアカウントのメールアドレスを編集者として共有
3. フォルダIDをURLから取得（`https://drive.google.com/drive/folders/FOLDER_ID`）

## 依存ライブラリ

- `google-api-python-client` - Google Drive API クライアント
- `google-auth-oauthlib` - Google認証

```bash
pip install google-api-python-client google-auth-oauthlib
```
