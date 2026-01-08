"""
Cloud Functions エントリーポイント

Google Cloud Functionsから呼び出されるメイン関数
"""

import os
import tempfile
from datetime import datetime

from modules.file_reader import read_file
from modules.llm_processor import LLMProcessor
from modules.content_formatter import save_outputs
from modules.gdrive_watcher import GDriveWatcher
from modules.notifier import notify_error, notify_review
from modules.approval_watcher import process_approved_files
from modules.metadata_extractor import extract_metadata, add_frontmatter_to_content


def main(request=None):
    """Cloud Functionsのエントリーポイント

    Google Driveの入力フォルダを監視し、新規ファイルを処理して
    生成されたコンテンツを出力フォルダにアップロードする。

    Args:
        request: Cloud Functions HTTPリクエストオブジェクト（オプション）

    Returns:
        処理結果のJSON（Cloud Functions用）
    """
    results = {
        "processed": [],
        "errors": [],
        "timestamp": datetime.now().isoformat(),
    }

    try:
        # Google Drive Watcherを初期化
        watcher = GDriveWatcher()

        # 未処理ファイルを取得
        new_files = watcher.list_new_files()

        if new_files:
            # LLMプロセッサを初期化
            processor = LLMProcessor()

            for file_info in new_files:
                file_id = file_info["id"]
                file_name = file_info["name"]
                mime_type = file_info.get("mimeType", "text/plain")

                try:
                    # 一時ディレクトリにダウンロード
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # ファイルをダウンロード
                        extension = watcher.get_file_extension(mime_type)
                        local_input_path = os.path.join(temp_dir, f"input{extension}")
                        watcher.download_file(file_id, local_input_path)

                        # ファイルを読み込み
                        content = read_file(local_input_path)

                        # コンテンツを生成
                        blog = processor.generate_content(content, "blog")
                        x_post = processor.generate_content(content, "x_post")
                        linkedin = processor.generate_content(content, "linkedin")

                        # メタデータを抽出してブログにフロントマターを追加
                        # LLMメタデータ生成を使用（.meta.yamlがない場合）
                        metadata = extract_metadata(
                            filename=file_name,
                            content=content,
                            use_llm=True,
                        )
                        blog_with_frontmatter = add_frontmatter_to_content(blog, metadata)

                        # 一時ディレクトリに保存
                        output_dir = os.path.join(temp_dir, "output")
                        paths = save_outputs(
                            blog=blog_with_frontmatter,
                            x_post=x_post,
                            linkedin=linkedin,
                            output_dir=output_dir,
                            use_timestamp=False,
                        )

                        # Google Driveにアップロード
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        base_name = os.path.splitext(file_name)[0]

                        blog_filename = f"{base_name}_{timestamp}_blog.md"
                        x_post_filename = f"{base_name}_{timestamp}_x_post.txt"
                        linkedin_filename = f"{base_name}_{timestamp}_linkedin.txt"

                        watcher.upload_file(
                            paths.blog,
                            blog_filename,
                            mime_type="text/markdown",
                        )
                        watcher.upload_file(
                            paths.x_post,
                            x_post_filename,
                            mime_type="text/plain",
                        )
                        watcher.upload_file(
                            paths.linkedin,
                            linkedin_filename,
                            mime_type="text/plain",
                        )

                        # 処理済みとしてマーク
                        watcher.mark_as_processed(file_id, file_name)

                        # Discord通知（レビュー待ち）
                        notify_review(
                            file_names=[blog_filename, x_post_filename, linkedin_filename],
                            source_file=file_name,
                            output_folder_id=os.getenv("GDRIVE_OUTPUT_FOLDER_ID"),
                        )

                        results["processed"].append({
                            "file_name": file_name,
                            "status": "success",
                        })

                except Exception as e:
                    # ファイル単位のエラーを記録
                    error_info = {
                        "file_name": file_name,
                        "error": str(e),
                    }
                    results["errors"].append(error_info)

                    # Discord通知
                    notify_error(
                        error=e,
                        context="ファイル処理",
                        file_name=file_name,
                    )

        results["message"] = (
            f"処理完了: {len(results['processed'])}件成功, "
            f"{len(results['errors'])}件エラー"
        )

        # 承認済みファイルをNotionに投稿
        try:
            approval_results = process_approved_files()
            results["notion_posted"] = approval_results
        except Exception as e:
            results["errors"].append({
                "error": str(e),
                "type": "notion_error",
            })
            notify_error(
                error=e,
                context="Notion投稿処理",
            )

    except Exception as e:
        # 全体的なエラー
        results["errors"].append({
            "error": str(e),
            "type": "system_error",
        })
        results["message"] = f"システムエラー: {str(e)}"

        # Discord通知
        notify_error(
            error=e,
            context="システム初期化",
        )

        raise

    return results


def http_handler(request):
    """HTTP トリガー用ハンドラ

    Args:
        request: Flask リクエストオブジェクト

    Returns:
        JSON レスポンス
    """
    import json

    try:
        result = main(request)
        return json.dumps(result, ensure_ascii=False), 200, {"Content-Type": "application/json"}
    except Exception as e:
        error_response = {
            "error": str(e),
            "status": "error",
        }
        return json.dumps(error_response, ensure_ascii=False), 500, {"Content-Type": "application/json"}


def pubsub_handler(event, context):
    """Pub/Sub トリガー用ハンドラ（スケジュール実行用）

    Args:
        event: Pub/Subイベント
        context: イベントコンテキスト

    Returns:
        処理結果
    """
    return main()


# ローカル実行用
if __name__ == "__main__":
    result = main()
    print(result)
