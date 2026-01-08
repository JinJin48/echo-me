"""
Cloud Run エントリーポイント

Flask直接起動方式 - 遅延インポートで高速起動
"""

import os
import sys
import logging
from pathlib import Path

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("=== main.py loading started ===")

from flask import Flask, request, jsonify

# Flaskアプリを最初に作成
app = Flask(__name__)
logger.info("Flask app created")

# srcディレクトリをパスに追加
src_path = str(Path(__file__).parent / "src")
sys.path.insert(0, src_path)
logger.info(f"Added to sys.path: {src_path}")

# cloud_functionは遅延インポート（起動を高速化）
_cloud_function_main = None
_import_error = None
_import_attempted = False


def _lazy_import():
    """cloud_functionを遅延インポート"""
    global _cloud_function_main, _import_error, _import_attempted

    if _import_attempted:
        return

    _import_attempted = True
    logger.info("Lazy importing cloud_function...")

    try:
        from cloud_function import main as cloud_main
        _cloud_function_main = cloud_main
        logger.info("cloud_function imported successfully")
    except Exception as e:
        _import_error = str(e)
        logger.error(f"Failed to import cloud_function: {e}", exc_info=True)


@app.route("/health", methods=["GET"])
def health_check():
    """ヘルスチェック用エンドポイント（インポート不要）"""
    logger.info("Health check endpoint called")
    return jsonify({"status": "healthy"}), 200


@app.route("/debug", methods=["GET"])
def debug_info():
    """デバッグ情報を返すエンドポイント"""
    logger.info("Debug endpoint called")
    return jsonify({
        "status": "ok",
        "import_attempted": _import_attempted,
        "import_error": _import_error,
        "cloud_function_loaded": _cloud_function_main is not None,
        "sys_path": sys.path[:5],
        "cwd": os.getcwd(),
        "routes": [str(rule) for rule in app.url_map.iter_rules()],
    }), 200


@app.route("/", methods=["POST", "GET"])
def http_handler():
    """HTTP トリガー用ハンドラ"""
    import json
    logger.info(f"Root endpoint called: method={request.method}")

    # 遅延インポートを実行
    _lazy_import()

    # インポートエラーがある場合
    if _import_error:
        logger.error(f"Returning import error: {_import_error}")
        return json.dumps(
            {"error": f"Import error: {_import_error}", "status": "error"},
            ensure_ascii=False
        ), 500, {"Content-Type": "application/json"}

    # cloud_functionがロードされていない場合
    if _cloud_function_main is None:
        logger.error("cloud_function_main is None")
        return json.dumps(
            {"error": "cloud_function not loaded", "status": "error"},
            ensure_ascii=False
        ), 500, {"Content-Type": "application/json"}

    try:
        result = _cloud_function_main(request)
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
logger.info("=== main.py loading completed (fast startup) ===")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Flask dev server on port {port}")
    app.run(host="0.0.0.0", port=port)
