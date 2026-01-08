"""
Cloud Run エントリーポイント

Flask直接起動方式
"""

import os
import sys
from pathlib import Path

from flask import Flask, request, jsonify

# Flaskアプリを最初に作成（インポートエラーがあっても動作するように）
app = Flask(__name__)

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent / "src"))

# cloud_functionのインポート（エラーをキャッチ）
cloud_function_main = None
import_error = None

try:
    from cloud_function import main as cloud_function_main
except Exception as e:
    import_error = str(e)


@app.route("/health", methods=["GET"])
def health_check():
    """ヘルスチェック用エンドポイント"""
    return jsonify({"status": "healthy"}), 200


@app.route("/", methods=["POST", "GET"])
def http_handler():
    """HTTP トリガー用ハンドラ"""
    import json

    # インポートエラーがある場合
    if import_error:
        return json.dumps(
            {"error": f"Import error: {import_error}", "status": "error"},
            ensure_ascii=False
        ), 500, {"Content-Type": "application/json"}

    # cloud_functionがロードされていない場合
    if cloud_function_main is None:
        return json.dumps(
            {"error": "cloud_function not loaded", "status": "error"},
            ensure_ascii=False
        ), 500, {"Content-Type": "application/json"}

    try:
        result = cloud_function_main(request)
        return json.dumps(result, ensure_ascii=False), 200, {"Content-Type": "application/json"}
    except Exception as e:
        error_response = {
            "error": str(e),
            "status": "error",
        }
        return json.dumps(error_response, ensure_ascii=False), 500, {"Content-Type": "application/json"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
