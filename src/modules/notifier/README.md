# notifier モジュール

Discord Webhookを使用してエラー通知を送信するモジュール

## 概要

このモジュールは、処理中にエラーが発生した際にDiscord Webhookを通じて通知を送信します。エラーの詳細（タイプ、メッセージ、スタックトレース）を含むリッチな埋め込みメッセージを送信します。

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `DISCORD_WEBHOOK_URL` | Discord WebhookのURL |

## クラス・関数一覧

### `class DiscordNotifier`

Discord Webhook通知を管理するクラス。

#### `__init__(self, webhook_url: str | None = None)`

**引数:**
- `webhook_url` (str | None): Discord WebhookのURL。Noneの場合は環境変数から取得

**例外:**
- `ValueError`: Webhook URLが設定されていない場合

#### `send_error(self, error, context, file_name) -> bool`

エラー通知を送信します。

**引数:**
- `error` (Exception): 発生した例外
- `context` (str | None): エラーが発生したコンテキスト（処理名など）
- `file_name` (str | None): 処理中だったファイル名

**戻り値:**
- `bool`: 送信成功時True、失敗時False

#### `send_message(self, message, title) -> bool`

カスタムメッセージを送信します。

**引数:**
- `message` (str): 送信するメッセージ
- `title` (str): メッセージのタイトル（デフォルト: "echo-me 通知"）

**戻り値:**
- `bool`: 送信成功時True、失敗時False

### `notify_error(error, context, file_name, webhook_url) -> bool`

関数インターフェース。エラー通知を送信します。Webhook URLが未設定の場合はログ出力のみ行います。

## 使用例

```python
from modules.notifier import DiscordNotifier, notify_error

# クラスインターフェース
notifier = DiscordNotifier()

try:
    # 何らかの処理
    process_file("sample.txt")
except Exception as e:
    notifier.send_error(
        error=e,
        context="ファイル処理",
        file_name="sample.txt"
    )
    raise

# 関数インターフェース（シンプルな用途向け）
try:
    process_file("sample.txt")
except Exception as e:
    notify_error(e, context="ファイル処理", file_name="sample.txt")
    raise
```

## 通知内容

エラー通知には以下の情報が含まれます：

- **エラータイプ**: 例外クラス名（例: `ValueError`）
- **発生時刻**: エラー発生時のタイムスタンプ
- **処理**: エラーが発生したコンテキスト
- **対象ファイル**: 処理中だったファイル名
- **エラーメッセージ**: 例外のメッセージ
- **スタックトレース**: エラーの発生箇所（最大1500文字）

## Discord Webhook設定手順

### 1. Webhookの作成

1. Discordサーバーの設定を開く
2. 「連携サービス」→「ウェブフック」
3. 「新しいウェブフック」をクリック
4. 名前を設定（例: echo-me）
5. 通知先チャンネルを選択
6. 「ウェブフックURLをコピー」

### 2. 環境変数の設定

```bash
# .envファイルに追加
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxxx/yyyyy
```

## 依存ライブラリ

このモジュールはPython標準ライブラリのみを使用します。追加のインストールは不要です。
