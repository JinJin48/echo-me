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
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload


# 対応するMIMEタイプとファイル拡張子のマッピング
SUPPORTED_MIME_TYPES = {
    "text/plain": ".txt",
    "text/markdown": ".md",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/pdf": ".pdf",
}

# OAuth スコープ
SCOPES = ["https://www.googleapis.com/auth/drive"]

# 認証情報ファイルのパス（優先順位順）
# Cloud Run環境
CLOUD_CREDENTIALS_PATH = Path("/secrets-cred/credentials.json")
CLOUD_TOKEN_PATH = Path("/secrets-token/token.json")
# ローカル開発環境
LOCAL_CREDENTIALS_PATH = Path(__file__).parent.parent.parent / "credentials.json"
LOCAL_TOKEN_PATH = Path(__file__).parent.parent.parent / "token.json"


class GDriveWatcher:
    """Google Driveフォルダを監視するクラス"""

    def __init__(
        self,
        input_folder_id: str | None = None,
        output_folder_id: str | None = None,
    ):
        """GDriveWatcherを初期化する

        Args:
            input_folder_id: 監視する入力フォルダのID。Noneの場合は環境変数から取得
            output_folder_id: 出力先フォルダのID。Noneの場合は環境変数から取得

        Raises:
            ValueError: フォルダIDが設定されていない場合
            FileNotFoundError: 認証情報ファイルが見つからない場合
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

        # 認証情報パスを解決
        self.credentials_path, self.token_path = self._resolve_credential_paths()
        self.service = self._build_service()

    def _resolve_credential_paths(self) -> tuple[Path, Path]:
        """認証情報ファイルのパスを解決する

        Cloud Run環境のパスを優先し、なければローカル開発環境のパスを使用する。

        Returns:
            (credentials_path, token_path) のタプル

        Raises:
            FileNotFoundError: 認証情報ファイルが見つからない場合
        """
        # Cloud Run環境のパスをチェック
        if CLOUD_CREDENTIALS_PATH.exists():
            credentials_path = CLOUD_CREDENTIALS_PATH
        elif LOCAL_CREDENTIALS_PATH.exists():
            credentials_path = LOCAL_CREDENTIALS_PATH
        else:
            raise FileNotFoundError(
                f"credentials.jsonが見つかりません。"
                f"Cloud Run: {CLOUD_CREDENTIALS_PATH} または "
                f"ローカル: {LOCAL_CREDENTIALS_PATH} に配置してください。"
            )

        if CLOUD_TOKEN_PATH.exists():
            token_path = CLOUD_TOKEN_PATH
        elif LOCAL_TOKEN_PATH.exists():
            token_path = LOCAL_TOKEN_PATH
        else:
            raise FileNotFoundError(
                f"token.jsonが見つかりません。"
                f"Cloud Run: {CLOUD_TOKEN_PATH} または "
                f"ローカル: {LOCAL_TOKEN_PATH} に配置してください。"
            )

        return credentials_path, token_path

    def _build_service(self):
        """Google Drive APIサービスを構築する

        OAuth認証を使用してGoogle Drive APIサービスを構築する。
        トークンが期限切れの場合は自動的に更新する。
        """
        creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)

        # トークンが期限切れの場合は更新
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # 更新されたトークンを保存（Cloud Run環境では書き込み不可の場合がある）
            try:
                with open(self.token_path, "w") as token:
                    token.write(creds.to_json())
            except (PermissionError, OSError):
                # Cloud Run環境などで書き込みできない場合は無視
                pass

        return build("drive", "v3", credentials=creds)

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
