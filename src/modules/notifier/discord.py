"""
notifier.discord モジュール

Discord Webhookを使用してエラー通知を送信する
"""

import json
import os
import traceback
from datetime import datetime
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from dotenv import load_dotenv


class DiscordNotifier:
    """Discord Webhook通知クラス"""

    def __init__(self, webhook_url: str | None = None):
        """DiscordNotifierを初期化する

        Args:
            webhook_url: Discord WebhookのURL。Noneの場合は環境変数から取得

        Raises:
            ValueError: Webhook URLが設定されていない場合
        """
        load_dotenv()

        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")

        if not self.webhook_url:
            raise ValueError(
                "DISCORD_WEBHOOK_URLが設定されていません。"
                ".envファイルで設定してください。"
            )

    def send_error(
        self,
        error: Exception,
        context: str | None = None,
        file_name: str | None = None,
    ) -> bool:
        """エラー通知を送信する

        Args:
            error: 発生した例外
            context: エラーが発生したコンテキスト（処理名など）
            file_name: 処理中だったファイル名

        Returns:
            送信成功時True、失敗時False
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # エラーメッセージを構築
        embed = {
            "title": "echo-me エラー通知",
            "color": 15158332,  # 赤色
            "fields": [
                {
                    "name": "エラータイプ",
                    "value": f"`{type(error).__name__}`",
                    "inline": True,
                },
                {
                    "name": "発生時刻",
                    "value": timestamp,
                    "inline": True,
                },
                {
                    "name": "エラーメッセージ",
                    "value": f"```{str(error)[:1000]}```",
                    "inline": False,
                },
            ],
            "footer": {
                "text": "echo-me Content Generator",
            },
        }

        if context:
            embed["fields"].insert(0, {
                "name": "処理",
                "value": context,
                "inline": True,
            })

        if file_name:
            embed["fields"].insert(1, {
                "name": "対象ファイル",
                "value": f"`{file_name}`",
                "inline": True,
            })

        # スタックトレースを追加（長い場合は省略）
        stack_trace = traceback.format_exc()
        if stack_trace and stack_trace != "NoneType: None\n":
            truncated_trace = stack_trace[-1500:] if len(stack_trace) > 1500 else stack_trace
            embed["fields"].append({
                "name": "スタックトレース",
                "value": f"```{truncated_trace}```",
                "inline": False,
            })

        payload = {
            "embeds": [embed],
        }

        return self._send_webhook(payload)

    def send_message(self, message: str, title: str = "echo-me 通知") -> bool:
        """カスタムメッセージを送信する

        Args:
            message: 送信するメッセージ
            title: メッセージのタイトル

        Returns:
            送信成功時True、失敗時False
        """
        embed = {
            "title": title,
            "description": message,
            "color": 3447003,  # 青色
            "timestamp": datetime.utcnow().isoformat(),
        }

        payload = {
            "embeds": [embed],
        }

        return self._send_webhook(payload)

    def _send_webhook(self, payload: dict) -> bool:
        """Webhookにペイロードを送信する

        Args:
            payload: 送信するJSONペイロード

        Returns:
            送信成功時True、失敗時False
        """
        try:
            data = json.dumps(payload).encode("utf-8")
            request = Request(
                self.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urlopen(request, timeout=10) as response:
                return response.status == 204

        except (URLError, HTTPError) as e:
            print(f"Discord通知の送信に失敗しました: {e}")
            return False


def notify_error(
    error: Exception,
    context: str | None = None,
    file_name: str | None = None,
    webhook_url: str | None = None,
) -> bool:
    """エラー通知を送信する（関数インターフェース）

    Args:
        error: 発生した例外
        context: エラーが発生したコンテキスト
        file_name: 処理中だったファイル名
        webhook_url: Discord WebhookのURL

    Returns:
        送信成功時True、失敗時False
    """
    try:
        notifier = DiscordNotifier(webhook_url)
        return notifier.send_error(error, context, file_name)
    except ValueError:
        # Webhook URLが設定されていない場合はログ出力のみ
        print(f"Discord通知をスキップ（Webhook未設定）: {error}")
        return False
