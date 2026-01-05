"""
gdrive_watcher モジュール

Google Drive APIを使用してフォルダを監視し、ファイルを取得する
"""

import io
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload


# 対応するMIMEタイプとファイル拡張子のマッピング
SUPPORTED_MIME_TYPES = {
    "text/plain": ".txt",
    "text/markdown": ".md",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/pdf": ".pdf",
}


class GDriveWatcher:
    """Google Driveフォルダを監視するクラス"""

    def __init__(
        self,
        input_folder_id: str | None = None,
        output_folder_id: str | None = None,
        credentials_path: str | None = None,
    ):
        """GDriveWatcherを初期化する

        Args:
            input_folder_id: 監視する入力フォルダのID。Noneの場合は環境変数から取得
            output_folder_id: 出力先フォルダのID。Noneの場合は環境変数から取得
            credentials_path: サービスアカウントの認証情報JSONファイルのパス

        Raises:
            ValueError: フォルダIDが設定されていない場合
        """
        load_dotenv()

        self.input_folder_id = input_folder_id or os.getenv("GDRIVE_INPUT_FOLDER_ID")
        self.output_folder_id = output_folder_id or os.getenv("GDRIVE_OUTPUT_FOLDER_ID")

        if not self.input_folder_id:
            raise ValueError(
                "GDRIVE_INPUT_FOLDER_IDが設定されていません。"
                ".envファイルで設定してください。"
            )

        if not self.output_folder_id:
            raise ValueError(
                "GDRIVE_OUTPUT_FOLDER_IDが設定されていません。"
                ".envファイルで設定してください。"
            )

        # サービスアカウント認証
        self.credentials_path = credentials_path or os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )
        self.service = self._build_service()

    def _build_service(self):
        """Google Drive APIサービスを構築する"""
        if self.credentials_path:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=["https://www.googleapis.com/auth/drive"],
            )
        else:
            # Cloud Functions環境ではデフォルト認証を使用
            from google.auth import default

            credentials, _ = default(
                scopes=["https://www.googleapis.com/auth/drive"]
            )

        return build("drive", "v3", credentials=credentials)

    def list_new_files(self, processed_marker: str = "_processed") -> list[dict]:
        """入力フォルダ内の未処理ファイルを一覧取得する

        Args:
            processed_marker: 処理済みファイル名に付与するマーカー

        Returns:
            未処理ファイルのリスト（各要素は{'id': str, 'name': str, 'mimeType': str}）
        """
        # サポートするMIMEタイプでフィルタ
        mime_conditions = " or ".join(
            [f"mimeType='{mime}'" for mime in SUPPORTED_MIME_TYPES.keys()]
        )

        query = (
            f"'{self.input_folder_id}' in parents "
            f"and trashed=false "
            f"and ({mime_conditions}) "
            f"and not name contains '{processed_marker}'"
        )

        results = (
            self.service.files()
            .list(
                q=query,
                fields="files(id, name, mimeType, createdTime)",
                orderBy="createdTime",
            )
            .execute()
        )

        return results.get("files", [])

    def download_file(self, file_id: str, local_path: str) -> str:
        """ファイルをダウンロードする

        Args:
            file_id: ダウンロードするファイルのID
            local_path: 保存先のローカルパス

        Returns:
            保存したファイルのパス
        """
        request = self.service.files().get_media(fileId=file_id)
        file_handle = io.BytesIO()
        downloader = MediaIoBaseDownload(file_handle, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(file_handle.getvalue())

        return local_path

    def upload_file(
        self,
        local_path: str,
        filename: str,
        folder_id: str | None = None,
        mime_type: str = "text/plain",
    ) -> str:
        """ファイルをアップロードする

        Args:
            local_path: アップロードするローカルファイルのパス
            filename: Google Drive上のファイル名
            folder_id: アップロード先フォルダID。Noneの場合はoutput_folder_idを使用
            mime_type: ファイルのMIMEタイプ

        Returns:
            アップロードしたファイルのID
        """
        target_folder = folder_id or self.output_folder_id

        file_metadata = {
            "name": filename,
            "parents": [target_folder],
        }

        media = MediaFileUpload(local_path, mimetype=mime_type)

        file = (
            self.service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )

        return file.get("id")

    def mark_as_processed(self, file_id: str, original_name: str) -> None:
        """ファイルを処理済みとしてマークする（リネーム）

        Args:
            file_id: ファイルのID
            original_name: 元のファイル名
        """
        # ファイル名に_processedを付与
        name_parts = original_name.rsplit(".", 1)
        if len(name_parts) == 2:
            new_name = f"{name_parts[0]}_processed.{name_parts[1]}"
        else:
            new_name = f"{original_name}_processed"

        self.service.files().update(
            fileId=file_id, body={"name": new_name}
        ).execute()

    def get_file_extension(self, mime_type: str) -> str:
        """MIMEタイプからファイル拡張子を取得する

        Args:
            mime_type: MIMEタイプ

        Returns:
            ファイル拡張子
        """
        return SUPPORTED_MIME_TYPES.get(mime_type, ".txt")


def get_new_files(
    input_folder_id: str | None = None,
    output_folder_id: str | None = None,
) -> list[dict]:
    """入力フォルダ内の未処理ファイルを取得する（関数インターフェース）

    Args:
        input_folder_id: 入力フォルダID
        output_folder_id: 出力フォルダID

    Returns:
        未処理ファイルのリスト
    """
    watcher = GDriveWatcher(input_folder_id, output_folder_id)
    return watcher.list_new_files()
