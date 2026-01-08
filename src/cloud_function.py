"""
Cloud Functions エントリーポイント

Google Cloud Functionsから呼び出されるメイン関数
"""

import os
import tempfile
import logging
from datetime import datetime

# ログ設定
logger = logging.getLogger(__name__)

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
        logger.info("Initializing GDriveWatcher...")
        watcher = GDriveWatcher()
        logger.info(f"GDriveWatcher initialized. Input folder: {watcher.input_folder_id}, Output folder: {watcher.output_folder_id}")

        # 未処理ファイルを取得
        logger.info("Listing new files from input folder...")
        new_files = watcher.list_new_files()
        logger.info(f"Found {len(new_files)} new files: {[f['name'] for f in new_files]}")

        if new_files:
            # LLMプロセッサを初期化
            logger.info("Initializing LLMProcessor...")
            processor = LLMProcessor()
            logger.info("LLMProcessor initialized")

            for file_info in new_files:
                file_id = file_info["id"]
                file_name = file_info["name"]
                mime_type = file_info.get("mimeType", "text/plain")
                logger.info(f"Processing file: {file_name} (id={file_id}, mimeType={mime_type})")

                try:
                    # 一時ディレクトリにダウンロード
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # ファイルをダウンロード
                        extension = watcher.get_file_extension(mime_type)
                        local_input_path = os.path.join(temp_dir, f"input{extension}")
                        logger.info(f"Downloading file to {local_input_path}...")
                        watcher.download_file(file_id, local_input_path)
                        logger.info(f"File downloaded successfully")

                        # ファイルを読み込み
                        logger.info("Reading file content...")
                        content = read_file(local_input_path)
                        logger.info(f"File content read: {len(content)} characters")

                        # コンテンツを生成
                        logger.info("Generating blog content...")
                        blog = processor.generate_content(content, "blog")
                        logger.info(f"Blog generated: {len(blog)} characters")

                        logger.info("Generating X post...")
                        x_post = processor.generate_content(content, "x_post")
                        logger.info(f"X post generated: {len(x_post)} characters")

                        logger.info("Generating LinkedIn post...")
                        linkedin = processor.generate_content(content, "linkedin")
                        logger.info(f"LinkedIn post generated: {len(linkedin)} characters")

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

                        logger.info(f"Uploading files to Google Drive output folder...")
                        watcher.upload_file(
                            paths.blog,
                            blog_filename,
                            mime_type="text/markdown",
                        )
                        logger.info(f"Uploaded {blog_filename}")
                        watcher.upload_file(
                            paths.x_post,
                            x_post_filename,
                            mime_type="text/plain",
                        )
                        logger.info(f"Uploaded {x_post_filename}")
                        watcher.upload_file(
                            paths.linkedin,
                            linkedin_filename,
                            mime_type="text/plain",
                        )
                        logger.info(f"Uploaded {linkedin_filename}")

                        # 処理済みとしてマーク
                        logger.info(f"Marking file as processed...")
                        watcher.mark_as_processed(file_id, file_name)
                        logger.info(f"File {file_name} marked as processed")

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
                    logger.error(f"Error processing file {file_name}: {e}", exc_info=True)
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

        else:
            logger.info("No new files to process")

        results["message"] = (
            f"処理完了: {len(results['processed'])}件成功, "
            f"{len(results['errors'])}件エラー"
        )
        logger.info(results["message"])

        # 承認済みファイルをNotionに投稿
        logger.info("Processing approved files for Notion...")
        try:
            approval_results = process_approved_files()
            results["notion_posted"] = approval_results
            logger.info(f"Notion processing completed: {approval_results}")
        except Exception as e:
            logger.error(f"Notion processing error: {e}", exc_info=True)
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
        logger.error(f"System error: {e}", exc_info=True)
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
