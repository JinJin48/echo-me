"""
ローカルテスト用スクリプト

Google DriveからファイルをダウンロードしてClaude APIで処理し、
結果をGoogle Driveにアップロードする。

初回実行時はOAuth認証のためブラウザが開きます。
"""

import io
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# モジュールのインポート
from modules.file_reader import read_file
from modules.llm_processor import LLMProcessor
from modules.content_formatter import save_outputs

# OAuth スコープ
SCOPES = ["https://www.googleapis.com/auth/drive"]

# 対応するMIMEタイプ
SUPPORTED_MIME_TYPES = {
    "text/plain": ".txt",
    "text/markdown": ".md",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/pdf": ".pdf",
}


def get_credentials():
    """OAuth認証を行い、認証情報を取得する

    初回実行時はブラウザが開いてGoogleアカウントでログインが必要。
    認証後はtoken.jsonにトークンが保存され、次回以降は自動的に使用される。

    Returns:
        google.oauth2.credentials.Credentials: 認証情報
    """
    creds = None

    # 認証ファイルのパス
    script_dir = Path(__file__).parent
    token_path = script_dir / "token.json"
    credentials_path = script_dir / "credentials.json"

    # 保存済みトークンがあれば読み込む
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    # トークンがないか無効な場合は再認証
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("トークンを更新中...")
            creds.refresh(Request())
        else:
            if not credentials_path.exists():
                print(f"エラー: {credentials_path} が見つかりません。")
                print("Google Cloud ConsoleからOAuthクライアントIDの認証情報をダウンロードして、")
                print(f"{credentials_path} として保存してください。")
                sys.exit(1)

            print("ブラウザでGoogleアカウントにログインしてください...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # トークンを保存
        with open(token_path, "w") as token:
            token.write(creds.to_json())
        print(f"トークンを保存しました: {token_path}")

    return creds


def list_new_files(service, folder_id, processed_marker="_processed"):
    """入力フォルダ内の未処理ファイルを取得する"""
    mime_conditions = " or ".join(
        [f"mimeType='{mime}'" for mime in SUPPORTED_MIME_TYPES.keys()]
    )

    query = (
        f"'{folder_id}' in parents "
        f"and trashed=false "
        f"and ({mime_conditions}) "
        f"and not name contains '{processed_marker}'"
    )

    results = (
        service.files()
        .list(
            q=query,
            fields="files(id, name, mimeType, createdTime)",
            orderBy="createdTime",
        )
        .execute()
    )

    return results.get("files", [])


def download_file(service, file_id, local_path):
    """ファイルをダウンロードする"""
    request = service.files().get_media(fileId=file_id)
    file_handle = io.BytesIO()
    downloader = MediaIoBaseDownload(file_handle, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    Path(local_path).parent.mkdir(parents=True, exist_ok=True)
    with open(local_path, "wb") as f:
        f.write(file_handle.getvalue())

    return local_path


def upload_file(service, local_path, filename, folder_id, mime_type="text/plain"):
    """ファイルをアップロードする"""
    file_metadata = {
        "name": filename,
        "parents": [folder_id],
    }

    media = MediaFileUpload(local_path, mimetype=mime_type)

    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )

    return file.get("id")


def mark_as_processed(service, file_id, original_name):
    """ファイルを処理済みとしてマークする"""
    name_parts = original_name.rsplit(".", 1)
    if len(name_parts) == 2:
        new_name = f"{name_parts[0]}_processed.{name_parts[1]}"
    else:
        new_name = f"{original_name}_processed"

    service.files().update(
        fileId=file_id, body={"name": new_name}
    ).execute()


def get_file_extension(mime_type):
    """MIMEタイプからファイル拡張子を取得する"""
    return SUPPORTED_MIME_TYPES.get(mime_type, ".txt")


def main():
    """メイン処理"""
    print("=" * 60)
    print("echo-me ローカルテスト")
    print("=" * 60)

    # 環境変数を読み込み
    load_dotenv()

    input_folder_id = os.getenv("GDRIVE_INPUT_FOLDER_ID")
    output_folder_id = os.getenv("GDRIVE_OUTPUT_FOLDER_ID")

    if not input_folder_id or not output_folder_id:
        print("エラー: GDRIVE_INPUT_FOLDER_ID と GDRIVE_OUTPUT_FOLDER_ID を")
        print(".envファイルに設定してください。")
        sys.exit(1)

    print(f"\n入力フォルダID: {input_folder_id}")
    print(f"出力フォルダID: {output_folder_id}")

    # OAuth認証
    print("\n[1/5] OAuth認証中...")
    creds = get_credentials()
    service = build("drive", "v3", credentials=creds)
    print("認証成功!")

    # 未処理ファイルを取得
    print("\n[2/5] 未処理ファイルを検索中...")
    new_files = list_new_files(service, input_folder_id)

    if not new_files:
        print("処理対象のファイルがありません。")
        print("\n処理完了（0件）")
        return

    print(f"{len(new_files)}件のファイルが見つかりました:")
    for f in new_files:
        print(f"  - {f['name']} ({f['mimeType']})")

    # LLMプロセッサを初期化
    print("\n[3/5] Claude APIに接続中...")
    processor = LLMProcessor()
    print("接続成功!")

    # 処理結果
    success_count = 0
    error_count = 0

    # 各ファイルを処理
    print("\n[4/5] ファイル処理中...")
    for i, file_info in enumerate(new_files, 1):
        file_id = file_info["id"]
        file_name = file_info["name"]
        mime_type = file_info.get("mimeType", "text/plain")

        print(f"\n--- [{i}/{len(new_files)}] {file_name} ---")

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # ダウンロード
                print(f"  ダウンロード中...")
                extension = get_file_extension(mime_type)
                local_input_path = os.path.join(temp_dir, f"input{extension}")
                download_file(service, file_id, local_input_path)

                # ファイル読み込み
                print(f"  ファイル読み込み中...")
                content = read_file(local_input_path)

                # コンテンツ生成
                print(f"  ブログ記事を生成中...")
                blog = processor.generate_content(content, "blog")

                print(f"  X投稿を生成中...")
                x_post = processor.generate_content(content, "x_post")

                print(f"  LinkedIn投稿を生成中...")
                linkedin = processor.generate_content(content, "linkedin")

                # ローカルに保存
                output_dir = os.path.join(temp_dir, "output")
                paths = save_outputs(
                    blog=blog,
                    x_post=x_post,
                    linkedin=linkedin,
                    output_dir=output_dir,
                    use_timestamp=False,
                )

                # Google Driveにアップロード
                print(f"  Google Driveにアップロード中...")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = os.path.splitext(file_name)[0]

                upload_file(
                    service,
                    paths.blog,
                    f"{base_name}_{timestamp}_blog.md",
                    output_folder_id,
                    mime_type="text/markdown",
                )
                upload_file(
                    service,
                    paths.x_post,
                    f"{base_name}_{timestamp}_x_post.txt",
                    output_folder_id,
                    mime_type="text/plain",
                )
                upload_file(
                    service,
                    paths.linkedin,
                    f"{base_name}_{timestamp}_linkedin.txt",
                    output_folder_id,
                    mime_type="text/plain",
                )

                # 処理済みマーク
                print(f"  処理済みとしてマーク中...")
                mark_as_processed(service, file_id, file_name)

                print(f"  成功!")
                success_count += 1

        except Exception as e:
            print(f"  エラー: {e}")
            error_count += 1

    # 結果表示
    print("\n" + "=" * 60)
    print("[5/5] 処理結果")
    print("=" * 60)
    print(f"成功: {success_count}件")
    print(f"失敗: {error_count}件")

    if error_count == 0:
        print("\nすべてのファイルの処理が完了しました!")
    else:
        print(f"\n{error_count}件のエラーが発生しました。上記のログを確認してください。")


if __name__ == "__main__":
    main()
