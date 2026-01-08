"""
Cloud Run エントリーポイント

Flask直接起動方式
"""

import os
import sys
import logging
from pathlib import Path

# ログ設定（Cloud Runで確認しやすくする）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("=== main.py loading started ===")

from flask import Flask, request, jsonify

# Flaskアプリを最初に作成（インポートエラーがあっても動作するように）
app = Flask(__name__)
logger.info(f"Flask app created: {app}")

# srcディレクトリをパスに追加
src_path = str(Path(__file__).parent / "src")
sys.path.insert(0, src_path)
logger.info(f"Added to sys.path: {src_path}")

# cloud_functionのインポート（エラーをキャッチ）
cloud_function_main = None
import_error = None

try:
    logger.info("Attempting to import cloud_function...")
    from cloud_function import main as cloud_function_main
    logger.info("cloud_function imported successfully")
except Exception as e:
    import_error = str(e)
    logger.error(f"Failed to import cloud_function: {e}", exc_info=True)


@app.route("/health", methods=["GET"])
def health_check():
    """ヘルスチェック用エンドポイント"""
    logger.info("Health check endpoint called")
    return jsonify({"status": "healthy"}), 200


@app.route("/debug", methods=["GET"])
def debug_info():
    """デバッグ情報を返すエンドポイント"""
    logger.info("Debug endpoint called")
    return jsonify({
        "status": "ok",
        "import_error": import_error,
        "cloud_function_loaded": cloud_function_main is not None,
        "sys_path": sys.path[:5],
        "cwd": os.getcwd(),
        "routes": [str(rule) for rule in app.url_map.iter_rules()],
    }), 200


@app.route("/", methods=["POST", "GET"])
def http_handler():
    """HTTP トリガー用ハンドラ"""
    import json
    logger.info(f"Root endpoint called: method={request.method}")

    # インポートエラーがある場合
    if import_error:
        logger.error(f"Returning import error: {import_error}")
        return json.dumps(
            {"error": f"Import error: {import_error}", "status": "error"},
            ensure_ascii=False
        ), 500, {"Content-Type": "application/json"}

    # cloud_functionがロードされていない場合
    if cloud_function_main is None:
        logger.error("cloud_function_main is None")
        return json.dumps(
            {"error": "cloud_function not loaded", "status": "error"},
            ensure_ascii=False
        ), 500, {"Content-Type": "application/json"}

    try:
        result = cloud_function_main(request)
        return json.dumps(result, ensure_ascii=False), 200, {"Content-Type": "application/json"}
    except Exception as e:
        logger.error(f"Error in cloud_function_main: {e}", exc_info=True)
        error_response = {
            "error": str(e),
            "status": "error",
        }
        return json.dumps(error_response, ensure_ascii=False), 500, {"Content-Type": "application/json"}


# 起動時のルート確認
logger.info(f"Registered routes: {[str(rule) for rule in app.url_map.iter_rules()]}")
logger.info("=== main.py loading completed ===")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Flask dev server on port {port}")
    app.run(host="0.0.0.0", port=port)
