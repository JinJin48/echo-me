"""
approval_watcher モジュール

承認済みファイルを監視し、Notionに投稿する
"""

import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv

from modules.gdrive_watcher import GDriveWatcher
from modules.notion_publisher import NotionPublisher
from modules.notifier import notify_notion_success, notify_notion_error


class ApprovalWatcher:
    """承認済みファイルを監視してNotionに投稿するクラス"""

    def __init__(
        self,
        approved_folder_id: str | None = None,
        posted_folder_id: str | None = None,
    ):
        """ApprovalWatcherを初期化する

        Args:
            approved_folder_id: 承認済みフォルダID
            posted_folder_id: 投稿済みフォルダID

        Raises:
            ValueError: フォルダIDが設定されていない場合
        """
        load_dotenv()

        self.approved_folder_id = approved_folder_id or os.getenv("GDRIVE_APPROVED_FOLDER_ID")
        self.posted_folder_id = posted_folder_id or os.getenv("GDRIVE_POSTED_FOLDER_ID")

        if not self.approved_folder_id:
            raise ValueError(
                "GDRIVE_APPROVED_FOLDER_IDが設定されていません。"
                ".envファイルで設定してください。"
            )

        if not self.posted_folder_id:
            raise ValueError(
                "GDRIVE_POSTED_FOLDER_IDが設定されていません。"
                ".envファイルで設定してください。"
            )

        # GDriveWatcherを初期化（入力/出力フォルダは使用しないがインスタンスは必要）
        self.gdrive = GDriveWatcher()
        self.notion = NotionPublisher()

    def list_approved_files(self) -> list[dict]:
        """承認済みフォルダ内のファイルを一覧取得する

        Returns:
            ファイルのリスト（各要素は{'id': str, 'name': str, 'mimeType': str}）
        """
        # Markdownとテキストファイルのみ対象
        query = (
            f"'{self.approved_folder_id}' in parents "
            f"and trashed=false "
            f"and (mimeType='text/plain' or mimeType='text/markdown')"
        )

        results = (
            self.gdrive.service.files()
            .list(
                q=query,
                fields="files(id, name, mimeType, createdTime)",
                orderBy="createdTime",
            )
            .execute()
        )

        return results.get("files", [])

    def move_to_posted(self, file_id: str) -> None:
        """ファイルを投稿済みフォルダに移動する

        Args:
            file_id: 移動するファイルのID
        """
        # 現在の親フォルダを取得
        file = (
            self.gdrive.service.files()
            .get(fileId=file_id, fields="parents")
            .execute()
        )
        previous_parents = ",".join(file.get("parents", []))

        # フォルダを移動
        self.gdrive.service.files().update(
            fileId=file_id,
            addParents=self.posted_folder_id,
            removeParents=previous_parents,
            fields="id, parents",
        ).execute()

    def process_approved_files(self) -> list[dict]:
        """承認済みファイルを処理してNotionに投稿する

        Returns:
            処理結果のリスト
        """
        results = []
        approved_files = self.list_approved_files()

        for file_info in approved_files:
            file_id = file_info["id"]
            file_name = file_info["name"]

            try:
                # 一時ファイルにダウンロード
                with tempfile.TemporaryDirectory() as temp_dir:
                    local_path = os.path.join(temp_dir, file_name)
                    self.gdrive.download_file(file_id, local_path)

                    # ファイル内容を読み込み
                    with open(local_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # タイトルを生成（拡張子を除いたファイル名）
                    title = Path(file_name).stem

                    # Notionに投稿
                    page_id = self.notion.create_page(title, content)

                    # 投稿済みフォルダに移動
                    self.move_to_posted(file_id)

                    # Discord通知（成功）
                    notify_notion_success(
                        page_title=title,
                        page_id=page_id,
                        source_file=file_name,
                    )

                    results.append({
                        "file_name": file_name,
                        "status": "success",
                        "notion_page_id": page_id,
                    })

            except Exception as e:
                # Discord通知（エラー）
                notify_notion_error(
                    error=e,
                    file_name=file_name,
                )

                results.append({
                    "file_name": file_name,
                    "status": "error",
                    "error": str(e),
                })

        return results


def process_approved_files() -> list[dict]:
    """承認済みファイルを処理する（関数インターフェース）

    Returns:
        処理結果のリスト
    """
    watcher = ApprovalWatcher()
    return watcher.process_approved_files()
